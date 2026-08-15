# Supply Ontology Hand POC 验证报告

日期：2026-08-15  
目标环境：`https://poc.openbkn.ai/`  
目标知识网络：`supply_ontology_hand`  

## 结论

POC 的数据导入、物理 Catalog、对象类绑定、Action Dataset 建表与绑定、函数工具箱和 Skill 发布链路已完成。离线第三方盲测通过；Action Dataset 的三张表已通过 Resource 方式绑定，未使用平台不支持的 `data_source.type=dataset`。

当前仍保留一个验证边界：本次没有执行真实采购、创建监控任务或关闭监控任务；Action 只完成结构、绑定和 dry-run 门禁验证。

## POC 资源证据

| 项目 | 结果 |
|---|---|
| 数据库 | `supply_ontology_hand_poc` |
| 数据表 | 12 张 `hand_` 表，78,635 行 |
| 物理 Catalog | `Supply_Ontology_Hand_POC` |
| Catalog ID | `d9vuoqtjdthc73bmpprg` |
| Action Toolbox | `af2ad8cb-9c32-4c07-aea8-fc05161d12e7`，published |
| Toolbox 工具 | 13/13 enabled |
| Skill | S1、S2、S3 已发布；S1 使用 POC 专用名称避免同名冲突 |

## Action Dataset 验证

数据库建表后重新执行 Catalog Discover，得到以下 Resource：

| 对象类 | Resource 名称 | Resource ID |
|---|---|---|
| 监控任务明细 | `public.sc_plan_monitor_item` | `da00p1ljdthc73bmqa9g` |
| 监控任务 | `public.sc_plan_monitor_task` | `da00p1ljdthc73bmqaa0` |
| 采购申请决策 | `public.sc_pr_decision` | `da00p1ljdthc73bmqaag` |

三个对象类回读结果均为：`data_source.type=resource`，且 Resource ID 与 Catalog Discover 结果一致。

标准执行命令：

```bash
cd /tmp/bkn-samples-inspect/samples/supply_ontology_hand
python3 tools/bootstrap_action_layer.py \\
  --config tools/config.poc.yaml \\
  --interactive --apply
```

该命令会依次执行：交互输入数据库连接 → 幂等建表并验收 → Catalog Discover → 查找三张表对应的 Resource → 更新对象类绑定。密码不写入配置文件。

## 盲测结果

```json
{
  "benchmark": "third_party_behavioral_blind",
  "reference_answers_read": false,
  "question_cases_loaded": 3,
  "playbook_accuracy": 1.0,
  "passed": true
}
```

Playbook 行为用例全部通过，覆盖澄清、证据优先、技能调用顺序、Action 提议和人工批准边界。

## 未纳入通过结论的事项

通过 Context Loader 进行的一次真实业务查询没有作为 POC 证据纳入：当前会话返回的是公共/旧资源绑定，查询预测单 `0000023181` 无结果。这说明在客户/生态环境验收时，必须先核对会话实际使用的知识网络 ID、Catalog/Resource 绑定和环境路由，避免把旧 KN 当成 POC KN。

下一轮客户验收应使用 POC Agent 接口，先回读 `supply_ontology_hand` 的对象类和 Resource，再执行业务问题；如返回旧资源，应先停止业务测试并修正环境路由。
