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
| 函数 Toolbox | 已发布；`backward_plan` 工具 `91565dd5-7df6-4d94-8e7a-2172488b6de5`，enabled |
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

## Agent Interaction 验证

通过已认证的 POC CLI Context Loader 完成了一次可追踪只读 Interaction：

- `conversation_id`: `conv_ebf77eb23300783b9bc396203ac4369`
- `interaction_id`: `int_164102eccbc4f239601ec1706b6e8d8a`
- 目标对象：`supply_ontology_hand_forecast`
- 查询产品：`U00-000080`
- 命中实例：`id=0000023181`，数量 `3000`，截止日 `2026-05-31`，状态 `正常`
- Interaction：`completed`，`evidence_status=complete`

此前内置连接器的一次查询返回旧/公共资源，属于连接器环境路由问题，不属于 POC 数据问题。客户/生态环境验收时必须先核对 Agent 实际使用的知识网络 ID、Catalog/Resource 绑定和环境路由；若返回旧资源，应先停止业务测试并修正路由。

本次只验证了预测单事实。是否可交付仍需继续执行 S1 履约证据链：成品库存、BOM 主料、物料库存、采购/生产计划和交期；“不启用替代料”必须作为明确输入。

## S1 履约证据链结果

随后通过同一 POC Context Loader 完成只读 S1 Interaction：

- 预测：`U00-000080` / `0000023181`，数量 `3000`，截止 `2026-05-31`，状态正常。
- 产品：对象存在，名称为“北斗车载智能终端系统”。
- BOM：命中 5 个主料行，均为 `alt_priority=0`；本轮未启用替代料。
- 成品库存：查询到可用库存记录合计 61 台，不能直接覆盖 3000 台需求。
- 计划/采购：存在截止日前的生产记录，但没有足够证据证明仍有 3000 台未被消耗的可交付量；部分采购订单交期为 2026-06/07，晚于目标日。

S1 结论：**不能证明按 2026-05-31 交付 3000 台；当前证据应判定为存在交付风险，不放行承诺。** 本次未执行任何 Action。

## Skill Registry POC 状态

未来场景预测已在 POC 命中：`0000023181-FUTURE` 为 3000 台、截止 2026-10-31；`0000023181-SHORT` 为 6000 台、截止 2026-11-30。

检查 `find_skills` 时发现 POC 对象类 `skills` 的 `data_source` 为空，因而召回失败。已在样例中补齐：

1. `datasets/postgres/002_skill_registry.sql`
2. `tools/setup_skill_dataset.py`：建表并从当前环境已发布 Skill 幂等回填
3. `tools/bind_skill_dataset.py`：Discover 后按 Resource 绑定 `skills`
4. 中英文测试与 Agent/手工手册说明

POC 已完成该补充步骤：`public.skills` Resource ID 为 `da01diljdthc73bmqf10`，对象类 `skills` 已绑定并补齐 `object_type_ids` / `skill_query` 等物理映射。通过可追踪 Context Loader Interaction 成功召回 3 个已发布 Skill：S1、S2、S3。Skill Registry 现计入 POC 通过项。

## Skill 可执行契约检查

随后按 POC Context Loader 的 `execute_skill` 契约读取 S1 内容并尝试执行。平台要求 `entry_shell` 必须来自 `SKILL.md` 明确声明的入口；当前 S1 只声明“优先调用 Toolbox `backward_plan`”，没有声明 `entry_shell`，因此平台拒绝进入执行阶段。本轮已按受管协议以 `failed` 结束，未调用离线 CLI、未伪造入口、未执行任何业务 Action。

这暴露的是 Skill 执行入口选择问题，不是函数 Toolbox 不支持调用：POC 函数 Toolbox 已发布，`backward_plan` 工具已启用；当前 `execute_skill` 只适合带 `entry_shell` 的脚本型 Skill，而 Context Loader 的 MCP 工具目录不等于 Toolbox 工具目录。编排型 S1 应由第三方 Agent 读取 Skill 契约后，通过 OpenBKN Toolbox Tool 接口提交 `resolved_context` 和业务参数。待按该路径完成一次真实 POC 函数调用后，再单独关闭 S1 在线闭环验证。
