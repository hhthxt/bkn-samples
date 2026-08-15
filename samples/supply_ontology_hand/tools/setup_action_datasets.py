"""Create and verify the idempotent Action Dataset tables."""

import argparse
import getpass
from pathlib import Path

EXPECTED_TABLES = {
    "sc_pr_decision",
    "sc_plan_monitor_task",
    "sc_plan_monitor_item",
}
SQL_PATH = Path(__file__).resolve().parents[1] / "datasets" / "postgres" / "001_action_datasets.sql"


def expected_tables() -> set[str]:
    return set(EXPECTED_TABLES)


def verify_tables(connection, schema: str = "public") -> dict:
    query = (
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = ANY(%s)"
    )
    with connection.cursor() as cursor:
        cursor.execute(query, (schema, sorted(expected_tables())))
        found = {row[0] for row in cursor.fetchall()}
    missing = sorted(expected_tables() - found)
    return {"schema": schema, "expected": sorted(expected_tables()), "found": sorted(found), "missing": missing, "ok": not missing}


def apply_ddl(connection, sql_text: str | None = None, schema: str = "public") -> dict:
    with connection.cursor() as cursor:
        cursor.execute(sql_text if sql_text is not None else SQL_PATH.read_text(encoding="utf-8"))
    connection.commit()
    report = verify_tables(connection, schema=schema)
    if not report["ok"]:
        raise RuntimeError(f"Action Dataset tables missing after apply: {', '.join(report['missing'])}")
    return report


def interactive_connection():
    import psycopg

    host = input("数据库 Host: ").strip()
    port = int(input("端口 [5432]: ") or "5432")
    database = input("数据库名（必填）: ").strip()
    if not database:
        raise ValueError("数据库名不能为空；请填写本环境 sample 数据库名")
    user = input("用户名: ").strip()
    password = getpass.getpass("密码（输入时不显示）: ")
    return psycopg.connect(host=host, port=port, dbname=database, user=user, password=password)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("postgres", "mysql"), default="postgres")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interactive", action="store_true", help="Prompt for database credentials and apply PostgreSQL DDL")
    parser.add_argument("--schema", default="public")
    args = parser.parse_args()
    sql = Path(__file__).resolve().parents[1] / "datasets" / args.engine / "001_action_datasets.sql"
    print(f"DDL: {sql}")
    should_apply = args.apply or args.interactive
    print(f"mode={'apply' if should_apply else 'dry-run'}")
    if not should_apply:
        print(sql.read_text())
        return
    if args.engine != "postgres":
        raise SystemExit("Automatic apply currently supports postgres only")
    connection = interactive_connection()
    try:
        print(__import__("json").dumps(apply_ddl(connection, schema=args.schema), ensure_ascii=False, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
