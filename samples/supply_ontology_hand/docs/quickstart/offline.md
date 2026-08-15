# 离线快速体验：客户需求承诺前的履约核查

这条路径不需要 OpenBKN 凭据、数据库或 ERP。它使用包内 CSV 生成 `offline_test` 的 `resolved_context`，但函数、Skill 和报告结构与在线路径一致。

## 1. 安装

```bash
cd /Users/leecky/Downloads/数据智能产品线/Kowell/供应链/Supply_demo_202608/bkn-samples/samples/supply_ontology_hand/tools
python3 -m pip install -r requirements.txt
```

## 2. 跑完整故事

```bash
python3 run_scenario.py \
  --scenario fulfillment-commitment \
  --product U00-000080 \
  --forecast-id 0000023181 \
  --demand-end 2026-05-31 \
  --demand-qty 3000 \
  --output /tmp/fulfillment-report.json
```

这个故事代表：客户提出 3000 台需求，计划负责人要判断 2026-05-31 是否可交付。

## 3. 如何读结果

- `s1`：生产计划倒排、物料缺口、供应状态和最大延迟；
- `s2`：成品库存 + 理论可产的合计可售数量；
- `snapshot_meta`：本次输入的快照、摘要和数据源；
- `action_proposals`：仅为 `proposed`，不会自动创建 ERP 单据。

样例金标预期：S1 最大延迟 166 天、S2 合计可售 20。结果中所有 Action 都必须先经过人工批准。

## 4. 可选：加入第二个需求验证共享物料

Python 调用 `FulfillmentCommitmentRunner` 时传入 `demands`，会追加 S3 共享物料争用分析。多个需求按传入顺序扣减，顺序必须在报告中声明。

## 5. 跑准确率验收

从包根执行：

```bash
cd /Users/leecky/Downloads/数据智能产品线/Kowell/供应链/Supply_demo_202608/bkn-samples/samples/supply_ontology_hand
PYTHONPATH=tools python3 -c 'from eval.evaluate import evaluate_local_sample; from pathlib import Path; print(evaluate_local_sample(Path("data"), Path("eval/cases")))'
```

放行要求：关键业务结论至少 95%，关键数值至少 98%，治理边界 100%。
