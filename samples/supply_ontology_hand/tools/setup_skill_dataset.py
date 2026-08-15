"""Create and seed the dataset-backed Skill registry."""

from __future__ import annotations

import argparse
import getpass
import json
import subprocess
from pathlib import Path

EXPECTED_TABLES = {"skills"}
SQL_PATH = Path(__file__).resolve().parents[1] / "datasets" / "postgres" / "002_skill_registry.sql"


def expected_tables() -> set[str]:
    return set(EXPECTED_TABLES)


def seed_rows(entries: list[dict], kn_id: str) -> list[dict]:
    rows = []
    for entry in entries:
        name = str(entry.get("name") or "")
        description = str(entry.get("description") or "")
        rows.append({
            "skill_id": str(entry.get("id") or entry.get("skill_id") or ""),
            "name": name,
            "description": description,
            "version": str(entry.get("version") or ""),
            "status": str(entry.get("status") or "published"),
            "business_domain_id": str(entry.get("business_domain_id") or ""),
            "kn_id": kn_id,
            "object_type_ids": entry.get("object_type_ids") or ["skills"],
            "skill_query": " ".join(part for part in (name, description) if part),
        })
    return [row for row in rows if row["skill_id"] and row["name"]]


def verify_table(connection, schema: str = "public") -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = ANY(%s)",
            (schema, sorted(expected_tables())),
        )
        found = {row[0] for row in cursor.fetchall()}
    missing = sorted(expected_tables() - found)
    return {"schema": schema, "found": sorted(found), "missing": missing, "ok": not missing}


def apply_ddl(connection, sql_text: str | None = None, schema: str = "public") -> dict:
    with connection.cursor() as cursor:
        cursor.execute(sql_text if sql_text is not None else SQL_PATH.read_text(encoding="utf-8"))
    connection.commit()
    report = verify_table(connection, schema=schema)
    if not report["ok"]:
        raise RuntimeError(f"Skill Dataset table missing after apply: {report['missing']}")
    return report


def upsert_rows(connection, rows: list[dict], schema: str = "public") -> int:
    query = f"""INSERT INTO {schema}.skills
        (skill_id, name, description, version, status, business_domain_id, kn_id, object_type_ids, skill_query)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
        ON CONFLICT (skill_id) DO UPDATE SET
          name=EXCLUDED.name, description=EXCLUDED.description, version=EXCLUDED.version,
          status=EXCLUDED.status, business_domain_id=EXCLUDED.business_domain_id,
          kn_id=EXCLUDED.kn_id, object_type_ids=EXCLUDED.object_type_ids,
          skill_query=EXCLUDED.skill_query"""
    with connection.cursor() as cursor:
        for row in rows:
            cursor.execute(query, (
                row["skill_id"], row["name"], row["description"], row["version"], row["status"],
                row["business_domain_id"], row["kn_id"], json.dumps(row["object_type_ids"]), row["skill_query"],
            ))
    connection.commit()
    return len(rows)


def load_published_skills(kn_id: str) -> list[dict]:
    result = subprocess.run(["openbkn", "--json", "skill", "list"], check=True, capture_output=True, text=True)
    return load_skill_entries(json.loads(result.stdout), kn_id=kn_id)


def load_skill_entries(payload: dict | list, kn_id: str | None = None) -> list[dict]:
    entries = payload if isinstance(payload, list) else (payload.get("entries") or payload.get("data") or [])
    base_kn_id = kn_id.removesuffix("_en") if kn_id else None
    return [entry for entry in entries
            if str(entry.get("status") or "published") == "published"
            and (not base_kn_id or base_kn_id in f"{entry.get('name', '')} {entry.get('description', '')}")]


def interactive_connection():
    import psycopg
    host = input("数据库 Host: ").strip()
    port = int(input("端口 [5432]: ") or "5432")
    database = prompt_database_name()
    user = input("用户名: ").strip()
    password = getpass.getpass("密码（输入时不显示）: ")
    return psycopg.connect(host=host, port=port, dbname=database, user=user, password=password)


def prompt_database_name() -> str:
    return input("数据库名 [supply_ontology_hand_poc]: ").strip() or "supply_ontology_hand_poc"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kn-id", default="supply_ontology_hand")
    parser.add_argument("--schema", default="public")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(f"DDL: {SQL_PATH}")
    if not (args.interactive or args.apply):
        print(SQL_PATH.read_text(encoding="utf-8"))
        print("mode=dry-run")
        return
    connection = interactive_connection()
    try:
        print(json.dumps(apply_ddl(connection, schema=args.schema), ensure_ascii=False))
        entries = load_published_skills(args.kn_id)
        rows = seed_rows(entries, kn_id=args.kn_id)
        print(json.dumps({"seeded": upsert_rows(connection, rows, schema=args.schema), "kn_id": args.kn_id}, ensure_ascii=False))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
