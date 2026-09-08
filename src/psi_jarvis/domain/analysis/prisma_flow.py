from dataclasses import dataclass


@dataclass(frozen=True)
class PrismaFlow:
    """Deterministic PRISMA-style flow counts for one persisted screening run.

    Counts are intentionally derived from persisted workflow stages rather than
    maintained as mutable presentation state. The model describes the records
    represented by a single run and does not make claims about full-text or
    study-level stages that are not persisted by PSI.JARVIS yet.
    """

    records_identified: int
    duplicates_removed: int
    records_screened: int
    records_excluded: int
    reports_sought: int
    reports_not_retrieved: int
    reports_assessed: int
    reports_excluded: int
    studies_included: int

    def __post_init__(self) -> None:
        values = (
            self.records_identified,
            self.duplicates_removed,
            self.records_screened,
            self.records_excluded,
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
        if self.records_excluded > self.records_screened:
            raise ValueError("Excluded records cannot exceed screened records")
        if self.reports_not_retrieved > self.reports_sought:
            raise ValueError("Not-retrieved reports cannot exceed reports sought")
        if self.reports_assessed + self.reports_not_retrieved != self.reports_sought:
            raise ValueError(
                "Reports sought must equal assessed plus not retrieved"
            )
        if self.reports_excluded > self.reports_assessed:
            raise ValueError("Excluded reports cannot exceed reports assessed")
        if self.studies_included > self.reports_assessed:
            raise ValueError("Included studies cannot exceed assessed reports")

    @property
    def unique_records(self) -> int:
        return self.records_identified - self.duplicates_removed

    @property
    def screening_included(self) -> int:
        return self.records_screened - self.records_excluded

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
        """Build the currently supported PRISMA stages from one screening run."""
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
            reports_sought=0,
            reports_not_retrieved=0,
            reports_assessed=0,
            reports_excluded=0,
            studies_included=included,
        )
