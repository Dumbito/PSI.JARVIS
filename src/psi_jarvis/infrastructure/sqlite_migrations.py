import sqlite3


CURRENT_SCHEMA_VERSION = 4


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


def _migration_2(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS review_projects (
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            research_question TEXT NOT NULL,
            topic TEXT NOT NULL,
            inclusion_rules TEXT NOT NULL,
            exclusion_rules TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    if _table_exists(connection, "screening_runs") and not _column_exists(connection, "screening_runs", "project_id"):
        connection.execute("ALTER TABLE screening_runs ADD COLUMN project_id TEXT")

    if _table_exists(connection, "screening_runs"):
        connection.execute("CREATE INDEX IF NOT EXISTS idx_screening_runs_project_id ON screening_runs(project_id)")

def _migration_3(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            abstract TEXT,
            doi TEXT,
            pmid TEXT,
            publication_year INTEGER,
            journal TEXT
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid)"
    )

def _migration_4(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS corpora (
            corpus_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS corpus_papers (
            corpus_id TEXT NOT NULL,
            paper_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (corpus_id, paper_id),
            FOREIGN KEY (corpus_id) REFERENCES corpora(corpus_id),
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_corpora_project_id ON corpora(project_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_corpus_papers_paper_id ON corpus_papers(paper_id)"
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
        current_version = 1

    if current_version < 2:
        _migration_2(connection)
        connection.execute(
            "UPDATE schema_version SET version = 2"
        )
        current_version = 2

    if current_version < 3:
        _migration_3(connection)
        connection.execute(
            "UPDATE schema_version SET version = 3"
        )
        current_version = 3

    if current_version < 4:
        _migration_4(connection)
        connection.execute(
            "UPDATE schema_version SET version = 4"
        )
