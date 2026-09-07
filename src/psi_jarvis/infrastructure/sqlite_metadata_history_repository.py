import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from psi_jarvis.application.synchronization.contracts import MetadataChange
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteMetadataHistoryRepository:
    """Persistencia SQLite de cambios de metadata detectados por sincronización."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

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
                SELECT paper_id, batch_id, source_key, source_record_id,
                       changed_at, changed_fields, before_json, after_json
                FROM metadata_change_history
                ORDER BY changed_at, change_key
                """
            ).fetchall()

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
