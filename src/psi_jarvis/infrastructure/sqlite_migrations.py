import sqlite3


CURRENT_SCHEMA_VERSION = 1


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
        ("table", table),
    ).fetchone() is not None


def _migration_1(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "screening_results") and not _column_exists(connection, "screening_results", "rule_traces"):
        connection.execute(
            "ALTER TABLE screening_results ADD COLUMN rule_traces TEXT NOT NULL DEFAULT '[]'"
        )

    if _table_exists(connection, "screening_audits") and not _column_exists(connection, "screening_audits", "run_id"):
        connection.execute(
            "ALTER TABLE screening_audits ADD COLUMN run_id TEXT"
        )


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )

    row = connection.execute(
        "SELECT version FROM schema_version LIMIT 1"
    ).fetchone()

    current_version = 0 if row is None else row[0]

    if current_version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {current_version} is newer than "
            f"supported version {CURRENT_SCHEMA_VERSION}"
        )

    if current_version < 1:
        _migration_1(connection)
        if row is None:
            connection.execute(
                "INSERT INTO schema_version (version) VALUES (1)"
            )
        else:
            connection.execute(
                "UPDATE schema_version SET version = 1"
            )
