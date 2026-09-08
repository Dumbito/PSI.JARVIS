import json
import sqlite3
from uuid import UUID

from psi_jarvis.domain.screening.result import ScreeningResult
from psi_jarvis.domain.screening.rules.trace import RuleTrace
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema


class SQLiteScreeningResultRepository:
    """Repositorio persistente de resultados individuales mediante SQLite."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _key(result: ScreeningResult) -> str:
        run_key = str(result.run_id) if result.run_id is not None else "none"
        return f"{run_key}:{result.paper_id}"

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, result: ScreeningResult) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO screening_results (
                    result_key,
                    paper_id,
                    included,
                    reason,
                    run_id,
                    matched_rules,
                    failed_rules,
                    matched_rule_ids,
                    failed_rule_ids,
                    criteria_version,
                    rule_traces
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(result_key) DO UPDATE SET
                    paper_id = excluded.paper_id,
                    included = excluded.included,
                    reason = excluded.reason,
                    run_id = excluded.run_id,
                    matched_rules = excluded.matched_rules,
                    failed_rules = excluded.failed_rules,
                    matched_rule_ids = excluded.matched_rule_ids,
                    failed_rule_ids = excluded.failed_rule_ids,
                    criteria_version = excluded.criteria_version,
                    rule_traces = excluded.rule_traces
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
                    json.dumps(
                        [self._trace_to_dict(trace) for trace in result.rule_traces]
                    ),
                ),
            )

    @staticmethod
    def _trace_to_dict(trace: RuleTrace) -> dict:
        return {
            "rule_id": trace.rule_id,
            "kind": trace.kind,
            "matched": trace.matched,
            "children": [
                SQLiteScreeningResultRepository._trace_to_dict(child)
                for child in trace.children
            ],
        }

    @staticmethod
    def _trace_from_dict(data: dict) -> RuleTrace:
        return RuleTrace(
            rule_id=data["rule_id"],
            kind=data["kind"],
            matched=bool(data["matched"]),
            children=tuple(
                SQLiteScreeningResultRepository._trace_from_dict(child)
                for child in data.get("children", [])
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
            rule_traces=tuple(
                SQLiteScreeningResultRepository._trace_from_dict(item)
                for item in json.loads(row["rule_traces"] or "[]")
            ),
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
