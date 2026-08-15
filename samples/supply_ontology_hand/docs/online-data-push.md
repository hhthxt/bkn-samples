# 线上数据推送与绑定说明

## 推荐顺序

```text
新建独立数据库/连接 → 新建物理 Catalog → 导入 sample 表 → Discover → 核验资源 → 绑定对象类 → 再注册指标
```

## Agent/API 模式

物理 Catalog 不是文件上传容器。供应链 sample 必须使用独立数据库和独立 Catalog，不得复用 POC 现有的 `RT_Supply_Data`，避免 sample 数据与真实供应链数据混合。建议数据库名为 `supply_ontology_hand_poc`，Catalog 名为 `Supply_Ontology_Hand_POC`。

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

脚本会先使用 `postgres` 维护库创建目标数据库（若不存在），再提示连接信息；密码不回显，连接测试成功后必须输入 `yes` 才开始写入，目标表名为 `hand_<原表名>`。若数据库账号没有 `CREATEDB` 权限，应由 DBA 先建库，再去掉 `--create-database` 重试。

数据库表导入后，使用同一组连接信息创建独立物理 Catalog：

```bash
python3 tools/setup_catalog.py --interactive --table-prefix hand_ --write-config
```

交互模式不会把数据库密码写入配置，而是将后续绑定所需的无密码配置写入
`tools/config.poc.yaml`。如果当前目录没有 `config.yaml`，不会影响 Catalog
创建或扫描；后续绑定必须使用这个 `config.poc.yaml`。

该命令默认使用 `Supply_Ontology_Hand_POC`，会测试连接、创建/复用同名新 Catalog、Discover，并核对 12 张 `hand_` 表。不要把 `RT_Supply_Data` 填入配置。

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
  --config tools/config.poc.yaml \
  --mapping tools/mapping/object_table_map.yaml
python3 tools/power_layer.py create --kn-id supply_ontology_hand
```

Embedding 需在导入 KN 时使用 `--resolve-embedding`；数据上传和向量索引构建是两步，不要把 `--build` 当成数据上传成功的证明。

## 失败排查

- `HTTP 404`：通常不是物理 Catalog 无效，而是当前环境没有启用 CSV 数据流接口。先把 CSV 灌入 POC 可访问的 PostgreSQL/MySQL，再让物理 Catalog discover；不要反复重试 `create-from-csv`。
- `Invalid Record Length`：CSV 某行列数与表头不一致；先运行上面的 shape check。不要直接重试，否则可能留下部分表。
- 资源存在但绑定失败：检查资源是否在目标 Catalog、表名是否包含 `hand_` 前缀，以及对象类的 `data_source.resource.id` 是否来自当前环境。
- 指标创建提示 `resource id is required`：先完成对象类资源绑定，再创建指标。

## 手工模式

UI 中先确认目标 Catalog 的连接状态和写入能力，再执行 CSV 导入；导入后在资源列表核对表名和行数，最后按同一份映射逐个绑定对象类。手工模式也必须使用前缀隔离、先绑定数据后创建指标。
