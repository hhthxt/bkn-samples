# backward_plan 合成夹具说明

本目录描述 `tests/test_backward_plan.py` 使用的最小内存夹具。测试通过
`build_snapshot(rows)` 组装 `Snapshot`，不读取 CSV、业务问答测试集或远端数据。
当前向量直接写在测试文件中；如后续拆分为 JSON/YAML，字段口径须保持一致。

## 数据集与最小字段

- `forecast`
  - `id`：预测单 ID。
  - `material_number`：产品编码，必须等于请求 `product`。
  - `enddate`：`YYYY-MM-DD` 截止日，必须等于请求 `demand_end`。
  - `qty`：正需求量，必须等于请求 `demand_qty`。
- `bom`
  - `bom_material_code`：BOM 所属产品。
  - `material_code`：当前子件。
  - `parent_material_code`：当前子件的直接父件。
  - `bom_level`：子件层级；根节点由函数生成，层级为 0。
  - `standard_usage`：父件生产一件所需的子件数量。
  - `alt_priority=0` 且 `alt_method!="替代"`：主料行。
  - `alt_group_no`、`alt_priority>0`、`alt_method="替代"`：替代行，只作为
    夹具噪声存在，不进入倒排主树。
- `material`
  - `material_code`：物料编码。
  - `materialattr`：`外购`、`委外` 或 `自制`。
  - `purchase_fixedleadtime`：外购/委外采购提前期。
  - `product_fixedleadtime`：自制生产提前期。
- `inventory`
  - `material_code`、`warehouse`、`available_inventory_qty`。
- `purchase_order`
  - `material_number`、`qty`、`actqty`、`deliverdate`、
    `rowclosestatus_title`。
- `purchase_request`
  - `material_number`、`qty`、`joinqty`、`rowclosestatus_title`。
- `mrp`
  - `materialplanid_number`、`closestatus_title`。

所有日期行为测试显式传 `today`，避免依赖系统日期。仓库夹具只使用明确属于
`production_available` 的仓名；另设隔离仓验证仓范围过滤。

## 公式口径

- 根节点：`end_date = demand_end`；
  `start_date = end_date - product_fixedleadtime`。
- 子件：`end_date = parent.start_date - 1 天`。
- 标准提前期：外购/委外取 `purchase_fixedleadtime`，自制取
  `product_fixedleadtime`，缺失按 0。
- 甘特条长：已满足（无未关闭 MRP 且供给量大于 0）时为 1 天，
  即 `start_date = end_date - 1 天`，`lead_time_days` 仍回显标准提前期；
  否则条长为 `max(标准提前期, 1)`，因此缺提前期的节点仍至少占 1 天。
- 主树只取主料 BOM。`substitute_enabled` 必须显式传入并原样回显，
  `False` 与 `True` 都不会把替代行加入倒排树，也不改变节点数。
- 缺物料主数据：与 `leadtime_days` 合同一致，抛 `CannotCompute`，不做
  soft-fail。LT 字段缺失（主数据存在但提前期字段为空）仍按 0，条长至少 1。
- 有效倒排请求会为每个节点计算 due/end。因此 `backward_plan` 的有效树
  集成只覆盖 10 个非 unknown 供应状态。`unknown` 是 `supply_status` 对
  无到位日的防御状态，已由 `test_fn_core.py::test_supply_status_requires_due_date`
  锁定；不为 `backward_plan` 发明不可达输入。
- 路径累计单耗：`usage_per_unit = 路径上 standard_usage 的乘积`。
- 毛需求：`gross_requirement = demand_qty * usage_per_unit`。
- 可用量：只汇总 `warehouse_scope` 内的 `available_inventory_qty`。
- 在途量：仅未关闭 PO，逐行计算 `max(0, qty - actqty)` 后求和。
- PR 未清量不进入供应量，只作为供应状态证据。
- A 类延迟：外购/委外、库存不足、无 PO 且倒排开始早于 `today` 时，
  `delay_days = max(0, (today + lead_time_days) - end_date)`。
- B 类延迟：PO 到货日晚于节点 `end_date`；延迟天数为到货日超过
  `end_date` 的日历日数。
- 同料号经多条路径出现时，树节点均保留；产品级 A/B 清单保留该料号的最大
  延迟。
- `max_delay_days` 为 A/B 最大值；
  `can_deliver_on_time = (max_delay_days == 0)`。
- `summary` 只返回根节点及风险/缺口节点，`full_tree` 返回全部节点；
  `node_count_total` 始终表示过滤前的完整节点数。
- 节点上限固定为 5000，不作为调用参数暴露：`root + 4999` 个可达主料子件
  （合计 5000 节点）可计算，`root + 5000`（合计 5001 节点）拒绝计算；
  传入 `max_nodes` 应因未知参数而报错。

## 节点断言合同

每个返回节点至少包含：

`material_code`、`parent_material_code`、`bom_level`、`usage_per_unit`、
`gross_requirement`、`start_date`、`end_date`、`lead_time_days`、
`available_qty`、`in_transit_qty`、`supply_status`、`delay_class`、
`delay_days`、`evidence`。

夹具只表达字段、分支条件和可独立复算的公式，不记录任何业务问答答案。
