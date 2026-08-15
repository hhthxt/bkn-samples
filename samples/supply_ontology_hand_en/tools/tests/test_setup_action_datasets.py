from setup_action_datasets import apply_ddl, expected_tables, verify_tables


class FakeCursor:
    def __init__(self, tables=None):
        self.tables = set(tables or [])
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return [(name,) for name in sorted(self.tables)]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeConnection:
    def __init__(self, tables=None):
        self.cursor_obj = FakeCursor(tables)
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def test_expected_tables_are_the_three_action_datasets():
    assert expected_tables() == {"sc_pr_decision", "sc_plan_monitor_task", "sc_plan_monitor_item"}


def test_apply_ddl_executes_sql_and_verifies_tables():
    conn = FakeConnection(expected_tables())
    report = apply_ddl(conn, sql_text="CREATE TABLE sc_pr_decision (...);")
    assert report["ok"] is True
    assert conn.committed is True


def test_verify_tables_reports_missing_dataset():
    conn = FakeConnection({"sc_pr_decision"})
    report = verify_tables(conn)
    assert report["ok"] is False
    assert report["missing"] == ["sc_plan_monitor_item", "sc_plan_monitor_task"]
