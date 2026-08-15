# Agent 操作手册：API、CLI 与脚本模式

## 目标

Agent 不依赖网页界面，通过 OpenBKN API、`openbkn` CLI 和 sample 脚本完成一次性导入、绑定、能力验证和供应承诺判断。

## 第 1 步：人工导入数据库表（Agent 前置条件）

这一步必须由部署/POC 操作者完成，因为它需要数据库连接信息和密码；Agent 不代替操作者登录数据库。请在 sample 根目录执行：

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

按提示输入 PostgreSQL Host、端口、数据库名、用户名和密码；连接测试成功后输入 `yes` 才写入。脚本会创建 `hand_` 前缀表，不覆盖原表。完成后，Agent 才从 Catalog Discover 开始接管。

## 操作入口

```text
Agent → OpenBKN API / openbkn CLI → KN、Resource、Skill、Function、Action → 测试集与报告
```

推荐入口顺序：

```bash
cp tools/config.example.yaml tools/config.yaml
# 编辑 tools/config.yaml：填写本环境 database.* 与 vega.catalog_name；不要提交该文件。
openbkn auth status
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --dry-run
python3 tools/setup_catalog.py --config tools/config.yaml --write-config
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --resolve-embedding
python3 tools/bind_kn_resources.py --config tools/config.yaml --dry-run --table-prefix hand_
python3 tools/bind_kn_resources.py --config tools/config.yaml --table-prefix hand_
python3 tools/register_skills.py
python3 tools/register_skills.py --apply
python3 tools/setup_skill_dataset.py --interactive --apply --kn-id supply_ontology_hand
openbkn --json vega catalog discover <catalog-id-from-config.yaml> --wait
python3 tools/bind_skill_dataset.py --kn-id supply_ontology_hand --catalog-id <catalog-id-from-config.yaml> --apply
python3 tools/power_layer.py --dry-run all --kn-id supply_ontology_hand
python3 tools/power_layer.py all --kn-id supply_ontology_hand
python3 tools/bootstrap_action_layer.py \
  --config tools/config.yaml \
  --interactive --apply
```

### 平台写入前的实施约束

- Toolbox 名称只能包含中文、英文字母、数字和下划线；不要使用 `-`、空格或其他标点。例如使用 `供应链计算函数工具箱P0`，不要使用 `供应链计算函数工具箱-P0`。
- 每次创建前先用 `openbkn toolbox list` 按名称确认是否已经存在。若命令出现连接超时，不要立即重复创建；先执行 `openbkn auth status`，再查询列表确认平台是否已创建成功。
- 函数服务必须先启动并保持运行；服务地址通过 `FUNCTION_SERVICE_URL` 配置，并且必须从 OpenBKN/POC 网络可解析、可访问。本机浏览器能访问不等于平台容器能访问。
- OpenAPI 上传后工具默认可能是 `disabled`；必须记录返回的 `tool_id`，执行 `openbkn tool enable --toolbox <box-id> <tool-id...>`，再查询 Toolbox 确认全部为 `enabled`。
- Agent 模式由 `bootstrap_action_layer.py` 一次完成幂等建表、三张表验收和对象类绑定；密码只在本次交互中使用，不写入 `config.yaml`。
- Skill Registry 需要两步：先用 `register_skills.py --apply` 将本包三项 Skill 注册/更新为 published，再用 `setup_skill_dataset.py` 建表并回填 `public.skills`，重新 Discover 后用 `bind_skill_dataset.py` 将小写对象类 ID `skills` 绑定到 Resource。不能只做其中一步。
- `setup_action_datasets.py --dry-run` 和 `bind_action_datasets.py --dry-run` 仍可分别检查计划；正式执行后必须再用数据库查询和 `openbkn bkn object-type get` 验收。

所有平台写入先用 dry-run；Agent 只能在平台返回能力和证据后继续，不得猜测对象类、字段、Skill 或 Action。

## 发布前推荐用户问题

先完成可移植的基础问答：成品有多少种、查询一个产品、该产品有多少销售订单、三个成品仓的可用库存是多少。它们只依赖已绑定数据与指标。S1 供应承诺题可以作为受限扩展：只有当管理员已验证 Function Toolbox 后端从平台网络可访问时，才使用 `U00-000080` / `0000023181-FUTURE` / `2026-10-31` / `3000` / 不启用替代料。

## 验证顺序

1. 确认知识网络和数据源已就绪。
2. 通过 Skill 查找供应承诺分析能力。
3. 查询预测单、产品、库存、BOM、生产和采购证据。
4. 仅在 Function Toolbox 后端已通过平台网络连通性验证时调用函数；否则记录为平台部署限制，不伪造在线计算结果。
5. 输出结论、证据和风险。
6. 涉及行动时先展示 dry-run 和影响范围，再等待人工确认。

## 编排型 Skill 的实际执行

S1/S2/S3 是编排型 Skill。Agent 先用 `find_skills` / `get_skill_content` 读取契约，然后自己完成受管查询和函数调用；不要把 S1 作为没有业务参数的 `execute_skill` shell 命令调用。

Agent 不需要额外保存上下文副本：已有的 `conversation_id`、`interaction_id` 原样放入每次调用的 `bkn_context`，已有的查询快照和 `bkn_receipt` 组装成 `resolved_context` 后直接传给 `backward_plan`。函数只计算，不查库；报告由 Agent 按 Skill 输出契约生成。

在线闭环的关键请求关系是：

```text
optional Context Loader(bkn_context)
→ resolved_context(rows + receipts)
→ OpenBKN Toolbox REST Proxy(backward_plan, request body)
→ Agent report
```

Context Loader MCP 工具目录与 Toolbox 工具目录是两套目录。Agent 通过 OpenBKN Execution Factory 的 REST Proxy 调用工具，不需要知道 Toolbox 背后的 `FUNCTION_SERVICE_URL`；管理员只在创建/更新 OpenAPI Toolbox 时配置后端地址。POC 已证明旧 Toolbox 使用 `host.docker.internal` 时会被平台容器 DNS 阻断，因此不能把“Toolbox 已注册”当作“函数已在线可用”。

生产调用入口：

```http
POST https://<openbkn-host>/api/agent-operator-integration/v1/tool-box/<box_id>/proxy/<tool_id>
Authorization: Bearer <token-or-appkey>
x-business-domain: bd_public
Content-Type: application/json
```

请求体的 `body` 放函数请求；平台返回的 `status_code` 才是被调函数服务的真实状态。不得改用 CSV、离线 CLI 或绕过 Toolbox 的直连调用冒充在线通过。

如果函数只需要调用计算能力、不需要额外检索，Agent 可以跳过 Context Loader，直接调用上述 REST Proxy；如果需要供应链事实证据，则先用受管 Context Loader 查询，再把 `resolved_context` 放入函数请求。对于多层 BOM、库存和在途等大数据量场景，当前平台尚未提供 Function 受管按需读取 BKN 的能力；不要尝试传递全量明细，相关能力跟踪见 Foundry #939–#942。

完整对话样例见 [Playbook](playbook.md)。
