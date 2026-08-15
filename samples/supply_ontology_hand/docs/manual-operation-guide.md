# 人工操作手册：界面与脚本模式

人工模式由“界面操作 + 脚本操作”组成，不通过 Agent 对话完成业务判断。

## 第 1 步：人工导入数据库表（必做）

数据库表导入是线上体验的前置环节，必须由操作者使用数据库连接信息完成，不能只在 OpenBKN 界面导入 KN JSON。执行：

```bash
python3 tools/load_sample_data.py --interactive --create-database --table-prefix hand_
```

提示：PostgreSQL 数据库名使用 `supply_ontology_hand_poc`；OpenBKN 连接/Catalog 名称使用 `Supply_Ontology_Hand_POC`。两者不同，Catalog ID 也不能当数据库名输入。

依次输入 PostgreSQL Host、端口、数据库名、用户名和密码。连接测试成功后输入 `yes`，脚本会创建 `hand_` 前缀表并保留原有业务表。

## 界面操作

1. 登录 OpenBKN 控制台。
2. 进入“领域知识网络 → 知识网络管理”。
3. 使用“导入”上传 `kn/supply_ontology_hand.json`。
4. 检查知识网络名称、对象类、关系类、指标和行动类数量。
5. 在数据资源/绑定页面选择对应资源并完成对象类绑定。
6. 在验证页面确认知识网络可查询，再进入脚本验证。

## 脚本操作

```bash
cd tools
python3 load_sample_data.py --config config.yaml
python3 import_kn.py --json ../kn/supply_ontology_hand.json
python3 setup_catalog.py --interactive --table-prefix hand_ --write-config
python3 bind_kn_resources.py --config config.poc.yaml --kn-id supply_ontology_hand --table-prefix hand_
python3 verify_sample.py --config config.poc.yaml --kn-id supply_ontology_hand
```

再按 `tools/setup_action_datasets.py`、Skill 注册和函数服务说明完成动力层配置。所有写入命令先使用 `--dry-run`，确认资源和影响范围后再执行。

### 函数 Toolbox 与超时处理

函数服务启动后，Toolbox 名称只能使用中文、字母、数字和下划线，不能含连字符、空格或其他标点。创建前先在 UI 或 `openbkn toolbox list` 中确认同名 Toolbox；如果 POC 返回连接超时，先检查 `openbkn auth status` 和 Toolbox 列表，再决定是否重试，避免重复创建。

函数服务地址不能硬编码。启动函数服务后，由部署者将 OpenBKN/POC 网络可访问的 `FUNCTION_SERVICE_URL` 注入 Toolbox 和 OpenAPI；`host.docker.internal` 仅是部分本地 Docker 环境的别名。服务进程必须持续运行，不能在上传 OpenAPI 后立即关闭。

本 sample 已提供可自托管的函数服务容器。开发机或客户自己的 Docker 主机上执行：

```bash
docker compose -f docker-compose.function.yaml up -d --build
curl http://127.0.0.1:8765/health
```

本机验证通过后，不能把 `http://127.0.0.1:8765` 填入远程 POC Toolbox。应把同一容器部署到客户/伙伴可控制且 OpenBKN 能访问的运行环境，使用该环境返回的 HTTPS 地址作为 `FUNCTION_SERVICE_URL`，只由管理员在 Toolbox 配置时填写一次。业务 Agent 和业务用户不需要知道这个地址；他们调用的是 OpenBKN Execution Factory 的 REST Proxy。参考 [BKN Foundry ToolBox REST proxy](https://openbkn-ai.github.io/bkn-foundry/versions/v0.1.3/execution-factory/toolbox.html)。

### Action Dataset 建表

Agent 模式可用以下命令一次完成幂等建表、三张表验收和对象类绑定；密码只在提示时输入，不写入配置：

```bash
python3 tools/bootstrap_action_layer.py \
  --config tools/config.poc.yaml \
  --interactive --apply
```

若采用纯手工模式，仍可直接执行 `datasets/postgres/001_action_datasets.sql`；执行前确认目标库，执行后核对 `sc_pr_decision`、`sc_plan_monitor_task`、`sc_plan_monitor_item`。

人工模式的界面截图、资源 ID 和操作时间应记录在本次验证报告中；不得把环境特定 ID 写回可移植 KN JSON。

## 供应承诺问题

使用 `docs/qa-eval-set.yaml` 中的未来预测案例，记录查询结果、计算证据和最终结论。
