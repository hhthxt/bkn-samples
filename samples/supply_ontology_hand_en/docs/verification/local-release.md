# 本地体验包验收

在包根运行：

```bash
cd /Users/leecky/Downloads/数据智能产品线/Kowell/供应链/Supply_demo_202608/bkn-samples/samples/supply_ontology_hand
PYTHONPATH=tools python3 tools/verify_sample.py
```

验收包含：

1. README、Playbook、离线/在线指南和能力目录是否存在；
2. `tools/tests` 全量测试；
3. 指标、函数、场景和治理边界独立金标评测；
4. Action 默认 dry-run、需要批准、幂等且不触发 ERP 的代码路径。

当前放行门槛：关键结论 ≥95%，关键数值 ≥98%，治理边界 100%。平台注册、真实 Dataset DDL 和 ERP 联动不属于本地验收。
