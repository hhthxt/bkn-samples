# 供应链本体 · 手工体验包

- **Sample slug:** `supply_ontology_hand`
- **KN ID:** `supply_ontology_hand`
- **名称:** 供应链本体知识网络-手工版
- **数据:** 12 张 CSV（脱敏样例，约 16MB）
- **对象类:** 15 个：步骤 5 绑定 11 个事实对象；步骤 8 按需绑定监控/采购决策数据集与 `skills` 注册表。

## 文档

| 文档 | 说明 |
|------|------|
| [导入说明书](docs/openbkn-hand-import-guide_cn.md) | 步骤 1～7：导入 KN → 灌库 → 扫描 → 绑定 |
| [场景驱动的供应链动态能力设计](docs/场景驱动的供应链动态能力设计.md) | **主设计**（钉死本网 + CSV 样例；对照计划协同逻辑，不依赖其界面） |
| [能力口径清单](docs/能力口径清单.md) | 指标 / 函数 / 技能 / 行动口径 |
| [业务问答测试集](docs/业务问答测试集.md) | 每条能力 5–10 道业务题 + CSV 快照答案 |
| [Agent 导入验证清单](docs/Agent导入验证清单.md) | 导入真实环境后分步验收 |
| [POC 发布验证基线](docs/verification/poc-013-validation-report-2026-08-15.md) | 第三方放行范围、实测金标与已知限制（附既有 POC 证据链接） |
| [动力层落地方案](docs/动力层建设方案.md) | 指标 / 函数 / 技能 / 行动：步骤 8 做什么、如何验收 |
| [动力层落地说明书](docs/动力层落地说明书.md) | 步骤 8：指标 + 函数库/CLI + 技能注册 |
| [metrics-create.json](docs/payloads/metrics-create.json) | 创建指标的载荷 |
| [metrics-query-examples.json](docs/payloads/metrics-query-examples.json) | 可运行 query 体 + 样例期望值 |
| [logic-properties.json](docs/payloads/logic-properties.json) | 指标 → 对象逻辑属性绑定规格 |
| [完整业务故事 Playbook](docs/playbook/fulfillment-commitment-playbook.md) | 从需求预测到 S1/S2/S3、Action 提案和回读 |
| [Agent 对话 Playbook](docs/playbook/agent-conversation.md) | 人与 Agent 如何逐轮推进和确认 Action |
| [离线快速体验](docs/quickstart/offline.md) | 无 OpenBKN 凭据，使用 CSV 跑完整场景 |
| [OpenBKN 在线体验](docs/quickstart/online-openbkn.md) | 第三方 Agent 通过 Context Loader 交接数据 |
| [指标目录](docs/catalog/metrics.md) · [函数目录](docs/catalog/functions.md) · [Action 目录](docs/catalog/actions.md) | 本地能力、输入、输出和证据 |
| [能力注册表](docs/power-layer/capability-registry.yaml) | 指标 / 函数 / Skill / Action 的入口与验收映射 |

## 快速开始

### 推荐：先跑离线故事

```bash
cd tools
python3 run_scenario.py --scenario fulfillment-commitment \
  --product U00-000080 --forecast-id 0000023181 \
  --demand-end 2026-05-31 --demand-qty 3000 \
  --output /tmp/fulfillment-report.json
```

结果会串联 S1 倒排、S2 可售能力和 Action 提案。完整步骤见 [离线快速体验](docs/quickstart/offline.md)。

### 再接入 OpenBKN

1. 复制 `tools/config.example.yaml` → `tools/config.yaml`，填写数据库与 OpenBKN 环境信息
2. 按 [openbkn-hand-import-guide_cn.md](docs/openbkn-hand-import-guide_cn.md) 步骤 1～7 执行。
3. 冒烟验收后做动力层（步骤 8）：

```bash
cd tools
python3 smoke_test.py --config config.yaml
python3 power_layer.py all --kn-id supply_ontology_hand
```

## 工具一览

| 脚本 | 步骤 | 说明 |
|------|------|------|
| `import_kn.py` | 2 | 导入 `kn/supply_ontology_hand.json` |
| `load_sample_data.py` | 3 | 将 `data/*.csv` 灌入自备数据库 |
| `setup_catalog.py` | 4 | 创建 / 启用 Catalog 并扫描表 |
| `bind_kn_resources.py` | 5 | 对象类绑定 Catalog 资源 |
| `smoke_test.py` | 验收 | KN 名称、OT 行数、DB 联接命中率 |
| `power_layer.py` | 8 | 创建指标、挂逻辑属性、快照验收 |
| `fn/` · `fn_cli.py` | 8 | CSV 金标函数库及离线 CLI |
| `fn_service.py` · `export_fn_openapi.py` | 8 | Toolbox HTTP 服务与 OpenAPI 导出 |
| `metrics.py` | 本地 | 8 项 P0 指标的 CSV 计算与证据 |
| `scenario/` · `run_scenario.py` | 本地 | 离线业务故事 Runner |
| `actions/` | 本地 | 批准、采购决策、监控任务和 dry-run |
| `eval/cases/` | 验收 | 独立金标与 95%+ 评测 |

## 包内结构

```
supply_ontology_hand/
├── kn/supply_ontology_hand.json
├── data/
├── tools/         # power_layer + fn/ + CLI + OpenAPI 服务
├── skills/        # S1 齐套倒排 / S2 可售 / S3 新需求覆盖
└── docs/
```

## 国际化（当前状态）

本目录是**中文版 sample**：

- KN 模型（`kn/supply_ontology_hand.json`）：网络名称、对象类名、属性 `display_name` 等为中文。
- 样例 CSV 含中文业务文本（组织、物料等）。
- 技术 ID（`supply_ontology_hand`、`supply_ontology_hand_*`）为英文 slug，与工具/映射一致且保持不变。

英文体验请使用独立目录 `../supply_ontology_hand_en/`；不要在中文版目录混入英文说明或英文样例数据。

## 依赖

```bash
cd tools
pip install -r requirements.txt
```
