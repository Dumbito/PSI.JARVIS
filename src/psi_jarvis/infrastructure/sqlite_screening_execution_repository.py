import sqlite3
from uuid import UUID

from psi_jarvis.domain.screening.execution import ScreeningExecution
from psi_jarvis.infrastructure.sqlite_migrations import initialize_schema
from psi_jarvis.infrastructure import sqlite_screening_persistence as persistence
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

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            initialize_schema(connection)

    def save(self, execution: ScreeningExecution) -> None:
        with self._connect() as connection:
            persistence.save_run(connection, execution.run)
            for result in execution.results:
                persistence.save_result(connection, result)
            for audit in execution.audits:
                persistence.save_audit(connection, audit)
            connection.execute("INSERT INTO screening_executions (run_id) VALUES (?) ON CONFLICT(run_id) DO NOTHING", (str(execution.run.run_id),))

    def get(self, run_id: UUID) -> ScreeningExecution | None:
        with self._connect() as connection:
            row = connection.execute("SELECT run_id FROM screening_executions WHERE run_id = ?", (str(run_id),)).fetchone()
        if row is None:
            return None
        run = self.run_repository.get(run_id)
        if run is None:
            return None
        results = tuple(result for result in self.result_repository.list_all() if result.run_id == run_id)
        audits = tuple(audit for audit in self.audit_repository.list_all() if audit.run_id == run_id)
        return ScreeningExecution(run=run, results=results, audits=audits)

    def list_all(self) -> tuple[ScreeningExecution, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT run_id FROM screening_executions ORDER BY rowid").fetchall()
        executions = []
        for row in rows:
            execution = self.get(UUID(row[0]))
            if execution is not None:
                executions.append(execution)
        return tuple(executions)
