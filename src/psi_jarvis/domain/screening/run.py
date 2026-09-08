from dataclasses import dataclass
from datetime import datetime, UTC
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScreeningRun:
    """Representa una ejecución completa e inmutable del cribado."""

    run_id: UUID
    project_id: UUID | None
    criteria_version: str
    started_at: datetime
    total_input: int
    unique_papers: int
    duplicates_removed: int
    screened_papers: int

    @classmethod
    def create(
        cls,
        criteria_version: str,
        total_input: int,
        unique_papers: int,
        duplicates_removed: int,
        screened_papers: int,
        project_id: UUID | None = None,
    ) -> "ScreeningRun":
        if not criteria_version.strip():
            raise ValueError("Screening run criteria version cannot be empty")
        if total_input < 0:
            raise ValueError("Screening run total input cannot be negative")
        if unique_papers < 0:
            raise ValueError("Screening run unique papers cannot be negative")
        if duplicates_removed < 0:
            raise ValueError("Screening run duplicates removed cannot be negative")
        if screened_papers < 0:
            raise ValueError("Screening run screened papers cannot be negative")

        return cls(
            run_id=uuid4(),
            project_id=project_id,
            criteria_version=criteria_version,
            started_at=datetime.now(UTC),
            total_input=total_input,
            unique_papers=unique_papers,
            duplicates_removed=duplicates_removed,
            screened_papers=screened_papers,
        )
