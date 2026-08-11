# BKN Samples

OpenBKN 官方体验样例集合：知识网络模型、样例数据与分步导入工具。

## 前置条件

- [OpenBKN 平台安装（飞书文档）](https://openbkn-ai.feishu.cn/wiki/Hby4wPzuhiFqD8klgMdcwvpBnde)
- [openbkn CLI（bkn-sdk）](https://github.com/openbkn-ai/bkn-sdk)
- Python 3.11+（运行 sample 内 `tools/` 脚本）

## Samples

| Sample | KN ID | 说明 |
|--------|-------|------|
| [supply_ontology_hand](samples/supply_ontology_hand/) | `supply_ontology_hand` | 供应链本体手工体验：CSV 灌库 → Catalog 扫描 → 对象类绑定 → Agent 场景体验 |

> 更多 sample 将陆续加入（如 `supply-chain-skill`）。

## 快速导航

每个 sample 目录均为**自包含交付包**：

```
samples/<slug>/
├── README.md
├── kn/
├── data/
├── tools/
└── docs/
    ├── openbkn-hand-import-guide.md       # English
    ├── openbkn-hand-import-guide_cn.md    # 中文
    ├── agent-scenario-kn-capability-design.md
    └── agent-scenario-kn-capability-design_cn.md
```

## 贡献

新增 sample：在 `samples/<slug>/` 下提供完整 README、数据、工具与文档，并更新上表。
