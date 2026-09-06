import json
import sqlite3
from uuid import UUID

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteScreeningAuditRepository:
    "Repositorio persistente de auditorías de cribado mediante SQLite."

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _key(audit: ScreeningAudit) -> str:
        run_key = str(audit.run_id) if audit.run_id is not None else "none"
        return f"{run_key}:{audit.paper_id}"

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, audit: ScreeningAudit) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO screening_audits ("
                "audit_key, paper_id, included, reason, run_id, "
                "matched_rules, failed_rules, matched_rule_ids, "
                "failed_rule_ids, criteria_version"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(audit_key) DO UPDATE SET "
                "paper_id = excluded.paper_id, "
                "included = excluded.included, "
                "reason = excluded.reason, "
                "run_id = excluded.run_id, "
                "matched_rules = excluded.matched_rules, "
                "failed_rules = excluded.failed_rules, "
                "matched_rule_ids = excluded.matched_rule_ids, "
                "failed_rule_ids = excluded.failed_rule_ids, "
                "criteria_version = excluded.criteria_version",
                (
                    self._key(audit),
                    str(audit.paper_id),
                    int(audit.included),
                    audit.reason,
                    str(audit.run_id) if audit.run_id is not None else None,
                    json.dumps(audit.matched_rules),
                    json.dumps(audit.failed_rules),
                    json.dumps(audit.matched_rule_ids),
                    json.dumps(audit.failed_rule_ids),
                    audit.criteria_version,
                ),
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ScreeningAudit:
        return ScreeningAudit(
            paper_id=UUID(row["paper_id"]),
            included=bool(row["included"]),
            reason=row["reason"],
            run_id=UUID(row["run_id"]) if row["run_id"] else None,
            matched_rules=tuple(json.loads(row["matched_rules"])),
            failed_rules=tuple(json.loads(row["failed_rules"])),
            matched_rule_ids=tuple(json.loads(row["matched_rule_ids"])),
            failed_rule_ids=tuple(json.loads(row["failed_rule_ids"])),
            criteria_version=row["criteria_version"],
        )

    def get(
        self,
        paper_id: UUID,
        run_id: UUID | None = None,
    ) -> ScreeningAudit | None:
        with self._connect() as connection:
            if run_id is None:
                row = connection.execute(
                    "SELECT * FROM screening_audits "
                    "WHERE paper_id = ? AND run_id IS NULL",
                    (str(paper_id),),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM screening_audits "
                    "WHERE paper_id = ? AND run_id = ?",
                    (str(paper_id), str(run_id)),
                ).fetchone()

        return None if row is None else self._from_row(row)

    def list_all(self) -> tuple[ScreeningAudit, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM screening_audits ORDER BY rowid"
            ).fetchall()

        return tuple(self._from_row(row) for row in rows)
