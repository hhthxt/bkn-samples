PRODUCTION_AVAILABLE = [
    "Suzhou Semi-finished Goods Warehouse",
    "Suzhou Finished Goods Warehouse",
    "Suzhou Electronics Materials Warehouse",
    "Suzhou UAV Materials Warehouse",
    "Suzhou Assembly Materials Warehouse",
    "Urumqi Finished Goods Warehouse",
    "Harbin Finished Goods Warehouse",
]

FINISHED_GOODS = [
    "Suzhou Finished Goods Warehouse",
    "Urumqi Finished Goods Warehouse",
    "Harbin Finished Goods Warehouse",
]

PRESETS = {
    "production_available": PRODUCTION_AVAILABLE,
    "finished_goods": FINISHED_GOODS,
    "all": [],
}

ALIASES = {
    "Suzhou Semi-finished Goods Warehouse": "苏州半成品仓",
    "Suzhou Finished Goods Warehouse": "苏州成品仓",
    "Suzhou Electronics Materials Warehouse": "苏州电子原料仓",
    "Suzhou UAV Materials Warehouse": "苏州无人机原料仓",
    "Suzhou Assembly Materials Warehouse": "苏州装配原料仓",
    "Urumqi Finished Goods Warehouse": "乌鲁木齐成品仓",
    "Harbin Finished Goods Warehouse": "哈尔滨成品仓",
}


def warehouse_matches(actual: str, allowed: list[str]) -> bool:
    return actual in allowed or any(
        actual == alias and english == allowed_name
        for english, alias in ALIASES.items()
        for allowed_name in allowed
    )


def resolve_warehouse_scope(scope: str | list[str] | None) -> list[str]:
    if scope is None:
        return list(PRODUCTION_AVAILABLE)
    if isinstance(scope, list):
        return list(scope)
    key = str(scope).strip()
    if key in PRESETS:
        return list(PRESETS[key])
    raise ValueError(f"unknown warehouse_scope: {scope}")
