import sqlite3

from psi_jarvis.infrastructure.sqlite_migrations import CURRENT_SCHEMA_VERSION, initialize_schema


def test_initialize_schema_creates_schema_version(tmp_path):
    database = tmp_path / "schema.db"
    connection = sqlite3.connect(database)

    initialize_schema(connection)
    connection.commit()

    row = connection.execute("SELECT version FROM schema_version").fetchone()

    assert row[0] == CURRENT_SCHEMA_VERSION


def test_initialize_schema_adds_rule_traces_to_existing_results_table(tmp_path):
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE screening_results ("
        "result_key TEXT PRIMARY KEY,"
        "paper_id TEXT NOT NULL,"
        "included INTEGER NOT NULL,"
        "reason TEXT NOT NULL,"
        "run_id TEXT,"
        "matched_rules TEXT NOT NULL,"
        "failed_rules TEXT NOT NULL,"
        "matched_rule_ids TEXT NOT NULL,"
        "failed_rule_ids TEXT NOT NULL,"
        "criteria_version TEXT NOT NULL"
        ")"
    )

    initialize_schema(connection)
    connection.commit()

    columns = [row[1] for row in connection.execute("PRAGMA table_info(screening_results)")]

    assert "rule_traces" in columns


def test_initialize_schema_is_idempotent(tmp_path):
    database = tmp_path / "schema.db"
    connection = sqlite3.connect(database)

    initialize_schema(connection)
    initialize_schema(connection)
    connection.commit()

    row = connection.execute("SELECT version FROM schema_version").fetchone()

    assert row[0] == CURRENT_SCHEMA_VERSION
