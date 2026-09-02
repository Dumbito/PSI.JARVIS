from uuid import UUID

from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository
from psi_jarvis.infrastructure.sqlite_screening_result_repository import SQLiteScreeningResultRepository
from psi_jarvis.infrastructure.sqlite_screening_audit_repository import SQLiteScreeningAuditRepository


class SQLiteScreeningExecutionRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self.run_repository = SQLiteScreeningRunRepository(database_path)
        self.result_repository = SQLiteScreeningResultRepository(database_path)
        self.audit_repository = SQLiteScreeningAuditRepository(database_path)
        self._initialize()

    def _connect(self):
        import sqlite3
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS screening_executions ("
                "run_id TEXT PRIMARY KEY"
                ")"
            )
            connection.commit()

    def save(self, execution: ScreeningExecution) -> None:
        self.run_repository.save(execution.run)

        for result in execution.results:
            self.result_repository.save(result)

        for audit in execution.audits:
            self.audit_repository.save(audit)

        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO screening_executions (run_id) VALUES (?)",
                (str(execution.run.run_id),),
            )
            connection.commit()

    def get(self, run_id: UUID) -> ScreeningExecution | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT run_id FROM screening_executions WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()

        if row is None:
            return None

        run = self.run_repository.get(run_id)
        if run is None:
            return None

        results = tuple(
            result
            for result in self.result_repository.list_all()
            if result.run_id == run_id
        )

        audits = tuple(
            audit
            for audit in self.audit_repository.list_all()
            if audit.run_id == run_id
        )

        return ScreeningExecution(
            run=run,
            results=results,
            audits=audits,
        )

    def list_all(self) -> tuple[ScreeningExecution, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id FROM screening_executions ORDER BY rowid"
            ).fetchall()

        executions: list[ScreeningExecution] = []

        for row in rows:
            execution = self.get(UUID(row[0]))
            if execution is not None:
                executions.append(execution)

        return tuple(executions)
