---
name: demand-fulfillment-requirement-coverage-analysis
description: >
  Use when checking whether multiple new product demands can be accepted together
  on knowledge network supply_ontology_hand, including shared-BOM structure,
  kitting net demand, and shared-material contention.
---

# 需求承接 · 新需求覆盖（S3）

> 多单能不能一起接。口径：`docs/能力口径清单.md` §2。  
> 数量未定 → 只跑 **产品 BOM 共用清单**（结构交），不要给满足/不满足。
> 函数工具箱：`供应链计算函数工具箱`（`71600d21-c9f6-4336-bfbf-95bfb3654674`）。

## Skill Card

| 字段 | 值 |
|------|-----|
| `bkn_scope` | `supply_ontology_hand` |
| `trigger` | 多单互抢、新需求能否一起接、共用料够不够 |
| `required_metrics` | 库存可用量（按仓预设） |
| `required_functions` | **BOM 清单**；**产品 BOM 共用清单**（≥2，无 X 时停这里）；每单 **合计可售** / **要 X 套净需求**；**共用料争用**；**替代料状态** |
| `required_toolbox` | 优先调用 `产品BOM共用清单`、`要X套净需求与齐套`、`共用料与多需求争用`、`合计可售`、`替代料状态` |
| `open_parameters` | `demands[]`（产品 + 数量? + 优先级）、`substitute_enabled` |

不要调用：S1（无截止日）；把结构交当成争用；可售主公式里加在途。  
在途 = 未关闭 PO 未清，**要进入**净需求与争用。

## 数据交接（强制）

Agent 直接调用**官方 Context Loader**。不要让函数服务取数。本场景按是否有数量查询 `bom`，以及 `inventory`、`purchase_order`（净需求 / 争用）。

1. 先 `bkn_start_interaction`
2. 按合同查询所需数据集，**只查询一次**，保留每份 `bkn_receipt`
3. 内联 `resolved_context` 调用函数 Tool；**函数服务不查询**
4. 结束时 `bkn_finish_interaction`

- **禁止伪造** receipt
- **禁止 CSV** 作为运行时输入
- 合同见 `docs/第三方Agent数据交接说明.md`

## 口径

- ≥2 款且数量未定 → `bom_shared_list`（全部产品交集）；`shared_count`；无库存、无够不够
- 已有各单数量 → 每单净需求 + `shared_contention`（共享可用+在途按**传入顺序/优先级**扣）
- 产品级对照可用 `合计可售 >= demand_qty`；物料级缺口必须走净需求（含在途）
- 替代组 MAX；未确认替代 → 不能算

CSV 快照：382 ∩ P61 主料唯一 **28**；382 ∩ P61 ∩ U00-000151 **11**。样例争用：382×50 与 P61×60。

## 函数调用

平台执行时优先调用 Toolbox Tool，不在 Skill 内重写共享池或净需求公式。以下 CLI 只用于离线验收：

```bash
cd tools
python3 fn_cli.py bom-shared --products 382-000005,P61-000351
python3 fn_cli.py bom-shared --products 382-000005,P61-000351,U00-000151
python3 fn_cli.py kitting --product 382-000005 --qty 50 --substitute no
python3 fn_cli.py contention --demands 382-000005:50,P61-000351:60 --substitute no
```

## 输入

- `knowledge_network_id`：默认 `supply_ontology_hand`
- `demands[]`：至少 2 条；产品编码或名称；数量可缺（则只做结构交）
- `substitute_enabled`：未给出先问
- 扣减顺序 = 数组顺序（或用户给出的优先级，高优先先扣）

## 编排

1. `resolve_context` — 官方 Context Loader **只查询一次**：各产品 BOM、库存、未关闭 PO 在途；保留 `bkn_receipt` 并内联 `resolved_context`  
2. `analyze`  
   - 无数量：只用产品 BOM 共用清单，停止  
   - 有数量：每单净需求 + 共用料争用；产品级可售仅作对照  
   - **函数服务不查询**  
3. `render_report` — pegging / 共享标记；禁止再查远端  
4. `bkn_finish_interaction`

## 完成门槛

1. 至少 2 个产品  
2. 无数量时不得输出满足/不满足  
3. 有数量时 `substitute_enabled` 已确认  
4. 仓名单回显；在途口径声明为未关闭 PO  
5. 报告阶段远程查询次数为 0

## 输出

见 `references/io-contract.md` 与 `references/report-spec.md`。

## 参考

- `references/business-rules.md`
- `references/io-contract.md`
- `references/report-spec.md`
