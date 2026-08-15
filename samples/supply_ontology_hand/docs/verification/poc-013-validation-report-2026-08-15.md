# 供应链本体 Sample：POC 发布验证基线

日期：2026-08-15
目标平台：`https://poc.openbkn.ai`
知识网络：`supply_ontology_hand`

## 发布结论

**`third_party_base_pass`。** 可将 sample 发布给第三方进行“导入、数据绑定、指标与基础 Agent 联查、Skill 发现”的自助体验；不发布“实时 S1/S2/S3 自动履约闭环”承诺。

完整的 POC 历史证据见 [POC 验证报告](./poc-verification-report-2026-08-15.md)。本报告补充发布前重新读取的指标与样例数据金标，并规定第三方放行边界。

> CLI 实测版本为 `0.1.2`。平台构建版本未通过 CLI 暴露；交付现场应在控制台截图记录实际平台构建，不得将 CLI 版本当作平台版本。

## 已实测通过

| 项 | 现场证据 | 结果 |
|---|---|---|
| 知识网络 | 15 对象类、19 关系、3 Action、8 指标 | 通过 |
| 样例数据 | 12 张 `hand_` 业务表；预测 137 行 | 通过 |
| 产品对象 | Context Loader 返回 `382-000005`（北斗导航农机驾驶仪） | 通过 |
| 指标 | 成品 30、物料 3497、供应商 230、订单 800、仓库 29 | 通过 |
| Q1–Q4 基础问答 | 受管 Context Loader Interaction：成品 30、`382-000005` 订单 40、三成品仓可用 534；未验证 UI 内置 Agent 对话 | 通过 |
| 预测金标 | 全量 115922；未关闭 90 张、56340 件 | 通过 |
| Skill 注册 | 同一受管 Context Loader Interaction 中，以严格对象类 ID `skills` 召回 S1/S2/S3 | 通过，`evidence_status=complete` |
| 原生 Function Runtime | `open_forecast_count` 最小调用：普通与 zlib+base64 压缩上下文均返回 `open_count=1`、`exit_code=0` | 通过（Runtime smoke） |

## 第三方可体验范围

第三方用自己的数据库和 OpenBKN 环境按以下顺序操作：

1. 人工输入数据库连接信息运行 `load_sample_data.py`，创建专用体验库与 `hand_` 表。
2. 导入 KN、扫描 Catalog、执行对象绑定；名称、数据库、Catalog ID 只能写在本地 `tools/config.yaml`。
3. 创建 8 个指标，验证产品、物料、供应商、订单、仓库、库存、预测。
4. 建立 `skills` 数据集并将对象类 ID **`skills`**（全小写）绑定到扫描出的 Resource；再做 Skill 发现。
5. 用官方 Context Loader / Agent 完成 Q1–Q4：成品数、产品详情、销售订单关联、成品仓库存；保存 receipt/Trace。

人工路径见 [人工操作手册](../manual-operation-guide.md)，Agent 路径见 [Agent 操作手册](../agent-operation-guide.md)，常见平台差异见 [FAQ](../faq.md)。

## 不作为本次发布承诺的能力

| 能力 | 原因 | 对第三方的要求 |
|---|---|---|
| 实时 S1/S2/S3 自动闭环 | Function 尚不能受管地按需读取 BKN 的大规模 BOM、库存、采购和生产数据 | 不传递全量明细；按 Foundry #939–#942 跟踪 |
| 旧 OpenAPI 函数 Toolbox | POC 实测 `host.docker.internal` 不能被平台容器解析 | 由管理员部署到平台可达地址；业务用户不配置 `FUNCTION_SERVICE_URL` |
| 真实采购写入 | 不属于样例体验安全边界 | 禁止执行 `initiate_po` |
| 监控/采购 Action 写入 | 需要显式人工确认和已验证的后端 | 只可单独授权 dry-run，保留执行回执 |

## 金标变更说明

早期文档保留了旧预测快照（134 行、未关闭 87、总量 106422）。当前 CSV 与 POC 一致：137 行、未关闭 90、总量 115922。发布包已将相关题库、验证清单和指标说明同步为当前值；第三方环境若重新灌入本包 CSV，应以当前值为准。

## 发布前最小复验

```bash
cd samples/supply_ontology_hand/tools
python3 smoke_test.py --config config.yaml
python3 -m pytest tests/test_paths.py tests/test_verify_sample.py tests/test_resolved_context_docs.py -q
```

通过后，实施方应把自身的数据库名、Catalog 名、时间、操作者、Trace/receipt 写入交付记录；不得提交密码、Token、内部 Catalog ID 或 POC 专用地址。
