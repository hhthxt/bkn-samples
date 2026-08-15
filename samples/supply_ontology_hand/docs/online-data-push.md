# 线上数据推送与绑定说明

## 推荐顺序

```text
新建独立数据库/连接 → 新建物理 Catalog → 导入 sample 表 → Discover → 核验资源 → 绑定对象类 → 再注册指标
```

Action Dataset 也遵循同一链路：建表后必须重新 Discover，不能把表名直接当作对象类的 `data_source.id`。

## Agent/API 模式

物理 Catalog 不是文件上传容器。供应链 sample 必须使用独立数据库和独立 Catalog，不得复用现有业务 Catalog，避免 sample 数据与真实供应链数据混合。由部署者自行命名，例如数据库 `<sample_database>`、Catalog `<sample_catalog_name>`。

正确链路是：先创建独立数据库连接和数据库，再写入 sample 表，最后让新 Catalog Discover 扫描出表和资源。

```text
PostgreSQL/MySQL 数据库（写入 sample 表）
  → 物理 Catalog（connector）
  → discover
  → Vega resources
  → KN object_type.data_source
```

先检查每个 CSV 的列数一致，避免平台数据流中途失败：

```bash
python3 - <<'PY'
import csv, glob
for path in glob.glob('data/*.csv'):
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    width = len(rows[0])
    bad = [i + 1 for i, row in enumerate(rows) if len(row) != width]
    if bad:
        raise SystemExit(f'{path}: inconsistent rows {bad[:5]}')
print('CSV shape check passed')
PY
```

`create-from-csv` 只是平台提供的便捷数据流入口，不是物理 Catalog 的基本属性。若目标环境已启用该数据流，也应指定独立 Catalog；否则应先通过独立数据库连接创建带前缀的表，再运行新 Catalog Discover。

本 sample 自带数据库推送脚本；交付/POC 操作者没有必要手写 INSERT：

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

名称必须区分：数据库名填 `<sample_database>`；OpenBKN 里的物理 Catalog/连接名称填 `<sample_catalog_name>`；Catalog 创建后返回当前环境的 Catalog ID。数据库名不是 Catalog 名称，也不是 Catalog ID，不能复制其他 POC 或客户报告中的值。

脚本会先使用 `postgres` 维护库创建目标数据库（若不存在），再提示连接信息；密码不回显，连接测试成功后必须输入 `yes` 才开始写入，目标表名为 `hand_<原表名>`。若数据库账号没有 `CREATEDB` 权限，应由 DBA 先建库，再去掉 `--create-database` 重试。

数据库表导入后，使用同一组连接信息创建独立物理 Catalog：

```bash
python3 tools/setup_catalog.py --interactive --table-prefix hand_ --write-config
```

先复制 `tools/config.example.yaml` 为 `tools/config.yaml` 并填写本环境信息。交互模式不会回写数据库密码；后续绑定统一使用该本地 `tools/config.yaml`，不要创建或引用 `config.poc.yaml`。

该命令会使用 `config.yaml` 中的本环境 Catalog 名称，测试连接、创建/复用同名 Catalog、Discover，并核对 12 张 `hand_` 表。不要把现有业务 Catalog 填入配置。

不要把现有业务表直接覆盖。用前缀隔离本 sample：

```bash
openbkn --json bkn create-from-csv <catalog_id> \
  --files 'data/*.csv' \
  --name supply_ontology_hand_uploaded_data \
  --table-prefix hand_ \
  --batch-size 500
```

上传完成后，先核验 `hand_erp_material`、`hand_erp_mds_forecast`、`hand_sales_order` 等资源，再把 `tools/mapping/object_table_map.yaml` 中的表名改为带 `hand_` 前缀的映射，执行：

```bash
python3 tools/bind_kn_resources.py \
  --config tools/config.yaml \
  --mapping tools/mapping/object_table_map.yaml
python3 tools/power_layer.py all --kn-id supply_ontology_hand
```

Embedding 需在导入 KN 时使用 `--resolve-embedding`；数据上传和向量索引构建是两步，不要把 `--build` 当成数据上传成功的证明。

## 失败排查

- `HTTP 404`：通常不是物理 Catalog 无效，而是当前环境没有启用 CSV 数据流接口。先把 CSV 灌入 POC 可访问的 PostgreSQL/MySQL，再让物理 Catalog discover；不要反复重试 `create-from-csv`。
- `Invalid Record Length`：CSV 某行列数与表头不一致；先运行上面的 shape check。不要直接重试，否则可能留下部分表。
- 资源存在但绑定失败：检查资源是否在目标 Catalog、表名是否包含 `hand_` 前缀，以及对象类的 `data_source.resource.id` 是否来自当前环境。
- 指标创建提示 `resource id is required`：先完成对象类资源绑定，再创建指标。
- Toolbox 名称格式错误：去掉连字符、空格和其他标点，仅保留中文、字母、数字、下划线。
- POC API 返回连接超时：先执行 `openbkn auth status`，再执行 `openbkn toolbox list` 或 `openbkn skill list` 检查实际状态；不要盲目重复创建。
- 函数 Toolbox 无法调用：确认服务运行后，还要从 POC 平台网络验证 Toolbox `service_url` 的 DNS 和 TCP 可达性。`host.docker.internal:8765` 不是通用公网地址；出现 `lookup host.docker.internal ... no such host` 时，改用 POC 可解析的 HTTPS/服务地址或部署到 POC 网络内。
- Action Dataset 自动化失败：先用 `python3 tools/bootstrap_action_layer.py --dry-run` 检查映射；再确认数据库账号权限和三张 `sc_` 表，最后用 `openbkn bkn object-type get` 核对对象类 `data_source`。

## 手工模式

UI 中先确认目标 Catalog 的连接状态和写入能力，再执行 CSV 导入；导入后在资源列表核对表名和行数，最后按同一份映射逐个绑定对象类。手工模式也必须使用前缀隔离、先绑定数据后创建指标。
