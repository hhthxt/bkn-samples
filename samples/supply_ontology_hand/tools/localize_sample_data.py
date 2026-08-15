"""Create the English sample-data copy without changing CSV headers or keys."""

import csv
import hashlib
import sys
from pathlib import Path


KNOWN_TRANSLATIONS = {
    "北斗车载智能终端系统": "Beidou Vehicle Telematics Terminal System",
    "北斗导航农机驾驶仪": "Beidou Agricultural Navigation Controller",
    "农业全程作业智能探测系统": "Full-cycle Agricultural Operation Detection System",
    "农机智能探测系统": "Agricultural Machinery Detection System",
    "408卫星平地系统(海外版）": "408 Satellite Land Leveling System (Overseas)",
    "验证用户": "Benchmark User",
    "朱杰倩": "Zhu Jieqian",
    "邵明": "Shao Ming",
    "已关闭": "Closed",
    "正常": "Normal",
    "已审核": "Approved",
    "已上架": "Listed",
    "可用": "Available",
    "普通": "Standard",
    "全部领料": "Fully Issued",
    "部分领料": "Partially Issued",
    "完工": "Completed",
    "开工": "Started",
    "已确认": "Confirmed",
    "生产项目采购订单": "Production Project Purchase Order",
    "物料类采购": "Material Purchase",
    "生产项目采购申请单": "Production Project Purchase Request",
    "采购订单": "Purchase Order",
    "库存组织": "Inventory Organization",
    "业务组织": "Business Organization",
    "个": "piece",
    "天": "days",
    "自动驾驶": "Autonomous Driving",
    "替代": "Substitute",
    "外购": "Purchased",
    "委外": "Outsourced",
    "自制": "In-house",
    "苏州半成品仓": "Suzhou Semi-finished Goods Warehouse",
    "苏州成品仓": "Suzhou Finished Goods Warehouse",
    "苏州电子原料仓": "Suzhou Electronics Materials Warehouse",
    "苏州无人机原料仓": "Suzhou UAV Materials Warehouse",
    "苏州装配原料仓": "Suzhou Assembly Materials Warehouse",
    "乌鲁木齐成品仓": "Urumqi Finished Goods Warehouse",
    "哈尔滨成品仓": "Harbin Finished Goods Warehouse",
}


def translate(value, fallback_cache):
    if value in KNOWN_TRANSLATIONS:
        return KNOWN_TRANSLATIONS[value]
    if not any("\u3400" <= char <= "\u9fff" for char in value):
        return value
    if value not in fallback_cache:
        digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
        fallback_cache[value] = f"Sample Business Label {digest}"
    return fallback_cache[value]


def localize(source_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    fallback_cache = {}
    for source_path in sorted(source_dir.glob("*.csv")):
        target_path = target_dir / source_path.name
        with source_path.open(newline="", encoding="utf-8") as source, target_path.open(
            "w", newline="", encoding="utf-8"
        ) as target:
            reader = csv.reader(source)
            writer = csv.writer(target, lineterminator="\n")
            for row in reader:
                writer.writerow([translate(value, fallback_cache) for value in row])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    source = root / "data"
    target = root.parent / "supply_ontology_hand_en" / "data"
    if len(sys.argv) == 3:
        source, target = map(Path, sys.argv[1:])
    localize(source, target)
