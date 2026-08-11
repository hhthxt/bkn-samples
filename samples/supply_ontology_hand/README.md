# 供应链本体 · 手工体验包

- **Sample slug:** `supply_ontology_hand`
- **KN ID:** `supply_ontology_hand`
- **名称:** 供应链本体知识网络-手工版
- **数据:** 12 张 CSV（脱敏样例，约 16MB）
- **对象类:** 11 个绑定 + 1 个跳过（`mon_task`，`bind:false`）

## Documentation

- **English:** [docs/openbkn-hand-import-guide.md](docs/openbkn-hand-import-guide.md)
- **中文:** [docs/openbkn-hand-import-guide_cn.md](docs/openbkn-hand-import-guide_cn.md)

## 快速开始

1. 复制 `tools/config.example.yaml` → `tools/config.yaml`，填写数据库与 OpenBKN 环境信息
2. 按 [OpenBKN 手工体验导入说明书（中文）](docs/openbkn-hand-import-guide_cn.md) 或 [English guide](docs/openbkn-hand-import-guide.md) 步骤 1～7 执行
3. 冒烟验收：

```bash
cd tools
python3 smoke_test.py --config config.yaml
```

## 工具一览

| 脚本 | 步骤 | 说明 |
|------|------|------|
| `import_kn.py` | 2 | 导入 `kn/supply_ontology_hand.json` |
| `load_sample_data.py` | 3 | 将 `data/*.csv` 灌入自备数据库 |
| `setup_catalog.py` | 4 | 创建 / 启用 Catalog 并扫描表 |
| `bind_kn_resources.py` | 5 | 对象类绑定 Catalog 资源 |
| `smoke_test.py` | 验收 | KN 名称、OT 行数、DB 联接命中率 |

## 包内结构

```
supply_ontology_hand/
├── kn/supply_ontology_hand.json
├── data/                    # 12 张体验表 CSV
├── tools/
│   ├── config.example.yaml
│   ├── mapping/object_table_map.yaml
│   └── tests/
└── docs/
    ├── openbkn-hand-import-guide.md
    ├── openbkn-hand-import-guide_cn.md
    ├── agent-scenario-kn-capability-design.md
    └── agent-scenario-kn-capability-design_cn.md
```

## 场景扩展（可选）

见 [Agent 场景能力设计（English）](docs/agent-scenario-kn-capability-design.md) / [中文](docs/agent-scenario-kn-capability-design_cn.md)（S1～S6 场景地图与标杆场景说明）。

## 依赖

```bash
cd tools
pip install -r requirements.txt
```
