# Action 目录

| Action | 本地行为 | 安全边界 |
|---|---|---|
| `create_pr_decision` | 记录人工批准后的采购建议 | 不创建 ERP PR/PO |
| `create_monitor_task` | 创建一个产品 + 一张预测单的监控任务和物料证据 | 需要批准；同一预测单不能重复开任务 |
| `close_monitor_task` | 关闭任务并保留证据 | 需要批准；不删除历史 |
| `monitor_runner` | dry-run 刷新任务状态和证据 | 单任务失败不应影响其他任务 |

本地入口：`tools/actions/`。Action 默认 dry-run，批准凭证绑定提案摘要、Interaction、Action 类型、批准人、过期时间和幂等键。
