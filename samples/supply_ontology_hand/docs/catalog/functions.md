# 函数目录

| 函数 | 用途 | 关键边界 |
|---|---|---|
| `bom_list` | 查看 BOM | 结构查询，不等于争用 |
| `bom_shared_list` | 查看多个产品共用料 | 无数量时不做争用结论 |
| `layered_inventory` | 查看分层库存 | 占用只展示 |
| `substitute_status` | 判断替代料状态 | 替代策略需确认 |
| `theoretical_build` | 现有物料最多能产多少 | 不含成品和在途 |
| `total_sellable` | 当前最多可售多少 | 成品仓 + 理论可产 |
| `kitting_net_demand` | 要 X 套的净需求/齐套 | 在途只计未清 PO |
| `shared_contention` | 多需求共享物料争用 | 按输入顺序扣减 |
| `max_build_without_po` | 无需采购最大可产 | 与理论可产口径一致 |
| `leadtime_days` | 标准交期 | 只读物料主数据 |
| `supply_status` | 供应状态 10 档 | 无到货日不能判交期 |
| `open_forecast_count` | 未关闭预测单数 | 固定排除已关闭 |
| `backward_plan` | 生产计划倒排 | 一个产品 + 一张预测单 |

运行时函数只接受 `resolved_context`。离线 CSV 由本地 Provider 生成上下文；在线由第三方 Agent 查询 Context Loader。
