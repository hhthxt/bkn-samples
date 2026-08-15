# 人工操作手册：界面与脚本模式

人工模式由“界面操作 + 脚本操作”组成，不通过 Agent 对话完成业务判断。

## 第 1 步：人工导入数据库表（必做）

数据库表导入是线上体验的前置环节，必须由操作者使用数据库连接信息完成，不能只在 OpenBKN 界面导入 KN JSON。执行：

```bash
python3 tools/load_sample_data.py --interactive --table-prefix hand_
```

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
python3 bind_kn_resources.py --config config.yaml --kn-id supply_ontology_hand
python3 verify_sample.py --config config.yaml --kn-id supply_ontology_hand
```

再按 `tools/setup_action_datasets.py`、Skill 注册和函数服务说明完成动力层配置。所有写入命令先使用 `--dry-run`，确认资源和影响范围后再执行。

人工模式的界面截图、资源 ID 和操作时间应记录在本次验证报告中；不得把环境特定 ID 写回可移植 KN JSON。

## 供应承诺问题

使用 `docs/qa-eval-set.yaml` 中的未来预测案例，记录查询结果、计算证据和最终结论。
