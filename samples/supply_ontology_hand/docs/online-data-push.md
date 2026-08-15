# 线上数据推送与绑定说明

## 推荐顺序

```text
检查 CSV → 选择可写入的物理 Catalog → 带前缀上传 → 核验资源 → 绑定对象类 → 再注册指标
```

## Agent/API 模式

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

使用平台可写入的物理 Catalog；不要把现有业务表直接覆盖。用前缀隔离本 sample：

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
python3 tools/power_layer.py create --kn-id supply_ontology_hand
```

Embedding 需在导入 KN 时使用 `--resolve-embedding`；数据上传和向量索引构建是两步，不要把 `--build` 当成数据上传成功的证明。

## 失败排查

- `HTTP 404`：当前 Catalog 不是可写入的数据流目标，或该环境未启用 CSV 数据流。换用平台明确标记为可写入的物理 Catalog，或先把 CSV 灌入一个 POC 可访问的 PostgreSQL/MySQL，再运行 `setup_catalog.py` 扫描。
- `Invalid Record Length`：CSV 某行列数与表头不一致；先运行上面的 shape check。不要直接重试，否则可能留下部分表。
- 资源存在但绑定失败：检查资源是否在目标 Catalog、表名是否包含 `hand_` 前缀，以及对象类的 `data_source.resource.id` 是否来自当前环境。
- 指标创建提示 `resource id is required`：先完成对象类资源绑定，再创建指标。

## 手工模式

UI 中先确认目标 Catalog 的连接状态和写入能力，再执行 CSV 导入；导入后在资源列表核对表名和行数，最后按同一份映射逐个绑定对象类。手工模式也必须使用前缀隔离、先绑定数据后创建指标。
