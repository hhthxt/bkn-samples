# FAQ：第三方导入与 Embedding 模型绑定

## Q1：为什么导入时提示模型获取失败？

最常见原因是 `index_config.vector_config.model_id` 来自另一个环境。模型 ID 是平台实例内的资源 ID，不保证跨环境或跨租户有效。本 sample 已在 POC 实际复现过该问题。

## Q2：第三方用户怎么检查当前环境的 embedding？

Agent 模式先完成 OAuth 登录，再执行：

```bash
openbkn --json model small list
openbkn --json model small get-default --type embedding
```

确认 `model_type` 为 `embedding`，使用返回的 `model_id`。不要复制其他环境、旧报告或他人 JSON 中的 ID。

## Q3：怎么修复 JSON？

把所有启用向量索引属性的 `vector_config.model_id` 替换为目标环境可用的 embedding ID，保持 `vector_config.enabled` 不变。Agent 模式可直接让导入脚本动态读取目标环境默认 embedding：

```bash
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --resolve-embedding
```

## Q4：如何不写平台先验证？

```bash
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --dry-run
```

dry-run 只能验证本地 JSON 和请求准备，不能证明目标环境的模型 ID 有效；仍需做一次目标环境 API 导入或平台 schema 校验。

## Q5：导入后如何确认 embedding 真可用？

先执行 `openbkn --json bkn get <kn_id> --stats`，再对启用向量索引的字段执行一次语义搜索，并记录结果、模型 ID 和时间。知识网络创建成功不等于异步索引已经完成。

## Q6：为什么导入后指标数量可能是 0？

知识网络导入与指标注册是两个能力。`metrics_total: 0` 表示当前环境尚未注册指标，不代表对象类或关系导入失败。注册指标后用以下命令核验：

```bash
openbkn --json bkn metric list <kn_id>
```

技能注册、函数服务和行动绑定也必须分别验收，不能用 KN 导入成功替代全部动力层验证。

## Q7：手工模式怎么处理？

在 UI 的模型/索引配置中选择当前环境可用的 embedding，再导入 JSON。原则与 Agent 模式相同：不能照抄其他环境的 model ID。
