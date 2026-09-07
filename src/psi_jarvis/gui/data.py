from dataclasses import dataclass
import os
import sqlite3
from pathlib import Path

from psi_jarvis.infrastructure.connections import build_default_source_connection_registry
from psi_jarvis.infrastructure.auth import (
    ScopusConnectionManager,
    ScopusOAuthClient,
    default_scopus_token_store,
    load_scopus_environment,
)
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository


@dataclass(frozen=True)
class DashboardSnapshot:
    projects: int = 0
    papers: int = 0
    screened: int = 0
    pending: int = 0
    included: int = 0
    excluded: int = 0
    conflicts: int = 0
    source_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class SourceSnapshot:
    display_name: str
    status: str
    detail: str = ""


def default_database_path() -> Path:
    configured = os.environ.get("PSI_JARVIS_DATABASE_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "psi-jarvis" / "psi.db"


class GuiDataService:
    """Read-only GUI facade over the existing application/infrastructure layer."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path or default_database_path()).expanduser()

    def snapshot(self) -> DashboardSnapshot:
        if not self.database_path.exists():
            return DashboardSnapshot()

        projects = SQLiteProjectRepository(self.database_path).list_all()
        papers = SQLitePaperRepository(self.database_path).list_all()
        counts = {"included": 0, "excluded": 0, "screened": 0}
        conflicts = 0
        source_counts: dict[str, int] = {}

        with sqlite3.connect(self.database_path) as connection:
            try:
                rows = connection.execute(
                    "SELECT included, COUNT(*) FROM screening_results GROUP BY included"
                ).fetchall()
                for included, count in rows:
                    if included:
                        counts["included"] += count
                    else:
                        counts["excluded"] += count
                counts["screened"] = counts["included"] + counts["excluded"]
            except sqlite3.OperationalError:
                pass

            try:
                rows = connection.execute(
                    "SELECT source_key, COUNT(*) FROM acquisition_batches GROUP BY source_key"
                ).fetchall()
                source_counts = {str(source): int(count) for source, count in rows}
            except sqlite3.OperationalError:
                pass

        # Conflicts are deliberately represented as an explicit UI signal. The
        # synchronization service remains the authority; this facade never resolves them.
        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.execute("SELECT 1 FROM metadata_change_history LIMIT 1")
        except sqlite3.OperationalError:
            pass

        pending = max(0, len(papers) - counts["screened"])
        return DashboardSnapshot(
            projects=len(projects),
            papers=len(papers),
            screened=counts["screened"],
            pending=pending,
            included=counts["included"],
            excluded=counts["excluded"],
            conflicts=conflicts,
            source_counts=tuple(sorted(source_counts.items())),
        )

    def projects(self):
        if not self.database_path.exists():
            return ()
        return SQLiteProjectRepository(self.database_path).list_all()

    def papers(self):
        if not self.database_path.exists():
            return ()
        return SQLitePaperRepository(self.database_path).list_all()

    def sources(self) -> tuple[SourceSnapshot, ...]:
        try:
            config = load_scopus_environment()
            manager = ScopusConnectionManager(
                config.oauth,
                default_scopus_token_store(),
                oauth_client=ScopusOAuthClient(config.oauth) if config.oauth is not None else None,
                transport_config=config.transport,
            )
            registry = build_default_source_connection_registry(manager)
            return tuple(
                SourceSnapshot(
                    state.source.display_name,
                    state.status.value,
                    state.detail,
                )
                for state in registry.inspect_all()
            )
        except Exception as exc:
            return (SourceSnapshot("Bibliographic sources", "error", str(exc)),)
