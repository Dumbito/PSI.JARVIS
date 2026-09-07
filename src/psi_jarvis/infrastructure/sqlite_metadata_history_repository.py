import json
import sqlite3
from pathlib import Path

from psi_jarvis.application.synchronization.contracts import MetadataChange


class SQLiteMetadataHistoryRepository:
    """Persistencia SQLite de cambios de metadata detectados por sincronización."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
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

    def record(self, change: MetadataChange) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO metadata_change_history (
                    change_key, paper_id, batch_id, source_key, source_record_id,
                    changed_at, changed_fields, before_json, after_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(change_key) DO NOTHING
                """,
                (
                    change.key,
                    str(change.paper_id),
                    str(change.batch_id),
                    change.source_key,
                    change.source_record_id,
                    change.changed_at.isoformat(),
                    json.dumps(change.changed_fields, ensure_ascii=False, separators=(",", ":")),
                    change.before_json,
                    change.after_json,
                ),
            )

    def list_all(self) -> tuple[MetadataChange, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT change_key, paper_id, batch_id, source_key, source_record_id,
                       changed_at, changed_fields, before_json, after_json
                FROM metadata_change_history
                ORDER BY changed_at, change_key
                """
            ).fetchall()

        from datetime import datetime
        from uuid import UUID

        return tuple(
            MetadataChange(
                paper_id=UUID(row["paper_id"]),
                batch_id=UUID(row["batch_id"]),
                source_key=row["source_key"],
                source_record_id=row["source_record_id"],
                changed_at=datetime.fromisoformat(row["changed_at"]),
                changed_fields=tuple(json.loads(row["changed_fields"])),
                before_json=row["before_json"],
                after_json=row["after_json"],
            )
            for row in rows
        )
