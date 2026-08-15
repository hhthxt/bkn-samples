# Agent 操作手册：API、CLI 与脚本模式

## 目标

Agent 不依赖网页界面，通过 OpenBKN API、`openbkn` CLI 和 sample 脚本完成一次性导入、绑定、能力验证和供应承诺判断。

## 操作入口

```text
Agent → OpenBKN API / openbkn CLI → KN、Resource、Skill、Function、Action → 测试集与报告
```

推荐入口顺序：

```bash
openbkn auth status
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --dry-run
python3 tools/load_sample_data.py --config tools/config.yaml
python3 tools/load_sample_data.py --interactive --table-prefix hand_
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --resolve-embedding
python3 tools/bind_kn_resources.py --config tools/config.yaml --kn-id supply_ontology_hand
python3 tools/register_skills.py --dry-run
python3 tools/setup_action_datasets.py --engine postgres
python3 tools/bind_action_datasets.py --mapping tools/mapping/action_dataset_map.yaml
```

所有平台写入先用 dry-run；Agent 只能在平台返回能力和证据后继续，不得猜测对象类、字段、Skill 或 Action。

## 推荐用户问题

请判断产品 `U00-000080` 是否能在 `2026-10-31` 前交付 `3000` 台。预测单号是 `0000023181-FUTURE`，不启用替代料。请说明库存、可生产量、物料短缺和结论依据。

## 验证顺序

1. 确认知识网络和数据源已就绪。
2. 通过 Skill 查找供应承诺分析能力。
3. 查询预测单、产品、库存、BOM、生产和采购证据。
4. 调用函数完成可交付量计算。
5. 输出结论、证据和风险。
6. 涉及行动时先展示 dry-run 和影响范围，再等待人工确认。

完整对话样例见 [Playbook](playbook.md)。
