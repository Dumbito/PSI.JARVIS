import sqlite3


CURRENT_SCHEMA_VERSION = 7


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", table),
        ).fetchone()
        is not None
    )


def _migration_1(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "screening_results") and not _column_exists(
        connection, "screening_results", "rule_traces"
    ):
        connection.execute(
            "ALTER TABLE screening_results ADD COLUMN rule_traces TEXT NOT NULL DEFAULT '[]'"
        )

    if _table_exists(connection, "screening_audits") and not _column_exists(
        connection, "screening_audits", "run_id"
    ):
        connection.execute("ALTER TABLE screening_audits ADD COLUMN run_id TEXT")


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

    if _table_exists(connection, "screening_runs") and not _column_exists(
        connection, "screening_runs", "project_id"
    ):
        connection.execute("ALTER TABLE screening_runs ADD COLUMN project_id TEXT")

    if _table_exists(connection, "screening_runs"):
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_screening_runs_project_id ON screening_runs(project_id)"
        )


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
    connection.execute("CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid)")


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


def _migration_5(connection: sqlite3.Connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS screening_runs (
            run_id TEXT PRIMARY KEY,
            project_id TEXT,
            criteria_version TEXT NOT NULL,
            started_at TEXT NOT NULL,
            total_input INTEGER NOT NULL,
            unique_papers INTEGER NOT NULL,
            duplicates_removed INTEGER NOT NULL,
            screened_papers INTEGER NOT NULL
        )
        """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS screening_results (
            result_key TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            included INTEGER NOT NULL,
            reason TEXT NOT NULL,
            run_id TEXT,
            matched_rules TEXT NOT NULL,
            failed_rules TEXT NOT NULL,
            matched_rule_ids TEXT NOT NULL,
            failed_rule_ids TEXT NOT NULL,
            criteria_version TEXT NOT NULL,
            rule_traces TEXT NOT NULL DEFAULT "[]"
        )
        """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS screening_audits (
            audit_key TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            included INTEGER NOT NULL,
            reason TEXT NOT NULL,
            run_id TEXT,
            matched_rules TEXT NOT NULL,
            failed_rules TEXT NOT NULL,
            matched_rule_ids TEXT NOT NULL,
            failed_rule_ids TEXT NOT NULL,
            criteria_version TEXT NOT NULL
        )
        """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS screening_executions (
            run_id TEXT PRIMARY KEY
        )
        """)

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_screening_results_run_id ON screening_results(run_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_screening_audits_run_id ON screening_audits(run_id)"
    )


def _migration_6(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS acquisition_batches (
            batch_id TEXT PRIMARY KEY,
            source_key TEXT NOT NULL,
            adapter_key TEXT NOT NULL,
            adapter_version TEXT NOT NULL,
            acquired_at TEXT NOT NULL,
            request_json TEXT NOT NULL,
            request_sha256 TEXT NOT NULL,
            input_sha256 TEXT NOT NULL,
            source_locator TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_provenances (
            provenance_key TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            batch_id TEXT NOT NULL,
            record_ordinal INTEGER NOT NULL,
            format_name TEXT NOT NULL,
            format_version TEXT NOT NULL,
            mapping_version TEXT NOT NULL,
            raw_record_sha256 TEXT NOT NULL,
            source_record_id TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id),
            FOREIGN KEY (batch_id) REFERENCES acquisition_batches(batch_id),
            UNIQUE (paper_id, batch_id, record_ordinal, raw_record_sha256)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_paper_provenances_paper_id ON paper_provenances(paper_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_paper_provenances_batch_id ON paper_provenances(batch_id)"
    )


def _migration_7(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata_change_history (
            change_key TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            batch_id TEXT NOT NULL,
            source_key TEXT NOT NULL,
            source_record_id TEXT,
            changed_at TEXT NOT NULL,
            changed_fields TEXT NOT NULL,
            before_json TEXT NOT NULL,
            after_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_metadata_change_history_paper_id ON metadata_change_history(paper_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_metadata_change_history_batch_id ON metadata_change_history(batch_id)"
    )


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )

    row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    current_version = 0 if row is None else row[0]

    if current_version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {current_version} is newer than supported version {CURRENT_SCHEMA_VERSION}"
        )

    if current_version < 1:
        _migration_1(connection)
        if row is None:
            connection.execute("INSERT INTO schema_version (version) VALUES (1)")
        else:
            connection.execute("UPDATE schema_version SET version = 1")
        current_version = 1

    if current_version < 2:
        _migration_2(connection)
        connection.execute("UPDATE schema_version SET version = 2")
        current_version = 2

    if current_version < 3:
        _migration_3(connection)
        connection.execute("UPDATE schema_version SET version = 3")
        current_version = 3

    if current_version < 4:
        _migration_4(connection)
        connection.execute("UPDATE schema_version SET version = 4")
        current_version = 4

    if current_version < 5:
        _migration_5(connection)
        connection.execute("UPDATE schema_version SET version = 5")
        current_version = 5

    if current_version < 6:
        _migration_6(connection)
        connection.execute("UPDATE schema_version SET version = 6")
        current_version = 6

    if current_version < 7:
        _migration_7(connection)
        connection.execute("UPDATE schema_version SET version = 7")
