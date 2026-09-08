from dataclasses import dataclass


@dataclass(frozen=True)
class PrismaFlow:
    """Deterministic PRISMA-style flow counts for persisted screening data.

    PSI.JARVIS currently persists identification, deduplication and
    title/abstract screening. Full-text retrieval and study-level assessment
    are not yet persisted, so those later PRISMA stages remain explicitly
    unpopulated instead of being inferred from screening decisions.
    """

    records_identified: int
    duplicates_removed: int
    records_screened: int
    records_excluded: int
    records_included_for_next_stage: int
    reports_sought: int = 0
    reports_not_retrieved: int = 0
    reports_assessed: int = 0
    reports_excluded: int = 0
    studies_included: int = 0

    def __post_init__(self) -> None:
        values = (
            self.records_identified,
            self.duplicates_removed,
            self.records_screened,
            self.records_excluded,
            self.records_included_for_next_stage,
            self.reports_sought,
            self.reports_not_retrieved,
            self.reports_assessed,
            self.reports_excluded,
            self.studies_included,
        )
        if any(value < 0 for value in values):
            raise ValueError("PRISMA counts cannot be negative")
        if self.records_screened + self.duplicates_removed != self.records_identified:
            raise ValueError(
                "Identified records must equal screened records plus duplicates removed"
            )
        if self.records_excluded + self.records_included_for_next_stage != self.records_screened:
            raise ValueError(
                "Screened records must equal excluded records plus records retained for the next stage"
            )
        if self.reports_not_retrieved > self.reports_sought:
            raise ValueError("Not-retrieved reports cannot exceed reports sought")
        if self.reports_assessed + self.reports_not_retrieved != self.reports_sought:
            raise ValueError("Reports sought must equal assessed plus not retrieved")
        if self.reports_excluded > self.reports_assessed:
            raise ValueError("Excluded reports cannot exceed reports assessed")
        if self.studies_included > self.reports_assessed:
            raise ValueError("Included studies cannot exceed assessed reports")

    @property
    def unique_records(self) -> int:
        return self.records_identified - self.duplicates_removed

    @property
    def screening_exclusion_rate(self) -> float:
        if self.records_screened == 0:
            return 0.0
        return self.records_excluded / self.records_screened

    @classmethod
    def from_run(
        cls,
        *,
        total_input: int,
        unique_papers: int,
        duplicates_removed: int,
        screened_papers: int,
        included: int,
        excluded: int,
    ) -> "PrismaFlow":
        """Build the supported PRISMA stages from one persisted screening run."""
        if unique_papers != screened_papers:
            raise ValueError(
                "A run-level PRISMA flow requires unique papers to equal screened papers"
            )
        if included + excluded != screened_papers:
            raise ValueError("Included and excluded records must equal screened papers")
        return cls(
            records_identified=total_input,
            duplicates_removed=duplicates_removed,
            records_screened=screened_papers,
            records_excluded=excluded,
            records_included_for_next_stage=included,
        )
