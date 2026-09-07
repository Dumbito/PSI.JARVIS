import sqlite3

from psi_jarvis.infrastructure.sqlite_migrations import CURRENT_SCHEMA_VERSION, initialize_schema


def test_schema_seven_contains_metadata_change_history(tmp_path):
    database = tmp_path / "sync.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    connection.execute("INSERT INTO schema_version (version) VALUES (6)")

    initialize_schema(connection)
    connection.commit()

    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }

    assert CURRENT_SCHEMA_VERSION == 7
    assert "metadata_change_history" in tables
    assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 7
