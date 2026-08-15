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
openbkn auth status
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --dry-run
python3 tools/setup_catalog.py --interactive --table-prefix hand_ --write-config
python3 tools/import_kn.py --json kn/supply_ontology_hand.json --resolve-embedding
python3 tools/bind_kn_resources.py --config tools/config.poc.yaml --kn-id supply_ontology_hand --table-prefix hand_
python3 tools/register_skills.py --dry-run
python3 tools/setup_skill_dataset.py --interactive --apply --kn-id supply_ontology_hand
openbkn --json vega catalog discover <catalog-id> --wait
python3 tools/bind_skill_dataset.py --kn-id supply_ontology_hand --catalog-id <catalog-id> --apply
python3 tools/bootstrap_action_layer.py \
  --config tools/config.poc.yaml \
  --interactive --apply
```

### 平台写入前的实施约束

- Toolbox 名称只能包含中文、英文字母、数字和下划线；不要使用 `-`、空格或其他标点。例如使用 `供应链计算函数工具箱P0`，不要使用 `供应链计算函数工具箱-P0`。
- 每次创建前先用 `openbkn toolbox list` 按名称确认是否已经存在。若命令出现连接超时，不要立即重复创建；先执行 `openbkn auth status`，再查询列表确认平台是否已创建成功。
- 函数服务必须先启动并保持运行，服务地址使用 `http://host.docker.internal:8765`；OpenBKN 平台能访问该地址，不等于本机浏览器能访问该地址。
- OpenAPI 上传后工具默认可能是 `disabled`；必须记录返回的 `tool_id`，执行 `openbkn tool enable --toolbox <box-id> <tool-id...>`，再查询 Toolbox 确认全部为 `enabled`。
- Agent 模式由 `bootstrap_action_layer.py` 一次完成幂等建表、三张表验收和对象类绑定；密码只在本次交互中使用，不写入 `config.poc.yaml`。
- Skill Registry 也是数据库表：先运行 `setup_skill_dataset.py` 建表并从当前环境已发布 Skill 生成/幂等更新 `public.skills`，再重新 Discover，最后用 `bind_skill_dataset.py` 将对象类 ID `skills` 绑定到 Resource。不能只注册 Skill API 而跳过 Dataset 绑定。
- `setup_action_datasets.py --dry-run` 和 `bind_action_datasets.py --dry-run` 仍可分别检查计划；正式执行后必须再用数据库查询和 `openbkn bkn object-type get` 验收。

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
