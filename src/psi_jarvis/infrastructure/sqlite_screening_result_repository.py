import json
import sqlite3
from uuid import UUID

from psi_jarvis.domain.screening.result import ScreeningResult


class SQLiteScreeningResultRepository:
    """Repositorio persistente de resultados individuales mediante SQLite."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _key(result: ScreeningResult) -> str:
        run_key = str(result.run_id) if result.run_id is not None else "none"
        return f"{run_key}:{result.paper_id}"

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
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
                    criteria_version TEXT NOT NULL
                )
                """
            )

    def save(self, result: ScreeningResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO screening_results (
                    result_key,
                    paper_id,
                    included,
                    reason,
                    run_id,
                    matched_rules,
                    failed_rules,
                    matched_rule_ids,
                    failed_rule_ids,
                    criteria_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._key(result),
                    str(result.paper_id),
                    int(result.included),
                    result.reason,
                    str(result.run_id) if result.run_id is not None else None,
                    json.dumps(result.matched_rules),
                    json.dumps(result.failed_rules),
                    json.dumps(result.matched_rule_ids),
                    json.dumps(result.failed_rule_ids),
                    result.criteria_version,
                ),
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ScreeningResult:
        return ScreeningResult(
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
    ) -> ScreeningResult | None:
        with self._connect() as connection:
            if run_id is None:
                row = connection.execute(
                    """
                    SELECT *
                    FROM screening_results
                    WHERE paper_id = ? AND run_id IS NULL
                    """,
                    (str(paper_id),),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT *
                    FROM screening_results
                    WHERE paper_id = ? AND run_id = ?
                    """,
                    (str(paper_id), str(run_id)),
                ).fetchone()

        return None if row is None else self._from_row(row)

    def list_all(self) -> tuple[ScreeningResult, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM screening_results ORDER BY rowid"
            ).fetchall()

        return tuple(self._from_row(row) for row in rows)
