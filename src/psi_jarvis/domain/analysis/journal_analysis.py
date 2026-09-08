from collections.abc import Iterable
from dataclasses import dataclass

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class JournalAnalysis:
    total_papers: int
    papers_with_journal: int
    papers_without_journal: int
    unique_journals: int
    by_journal: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        values = (
            self.total_papers,
            self.papers_with_journal,
            self.papers_without_journal,
            self.unique_journals,
        )
        if any(value < 0 for value in values):
            raise ValueError("Journal counts cannot be negative")

        if self.papers_with_journal + self.papers_without_journal != self.total_papers:
            raise ValueError("Journal counts must equal total papers")

        if self.unique_journals != len(self.by_journal):
            raise ValueError("Unique journals must equal journal distribution size")

        if sum(count for _, count in self.by_journal) != self.papers_with_journal:
            raise ValueError(
                "Journal distribution counts must equal papers with journal"
            )

        if any(not journal.strip() for journal, _ in self.by_journal):
            raise ValueError("Journal names cannot be empty")

        if any(count < 0 for _, count in self.by_journal):
            raise ValueError("Journal distribution counts cannot be negative")

    @classmethod
    def from_papers(cls, papers: Iterable[Paper]) -> "JournalAnalysis":
        papers = tuple(papers)
        journals = tuple(
            paper.journal.strip()
            for paper in papers
            if paper.journal is not None and paper.journal.strip()
        )

        counts: dict[str, int] = {}
        for journal in journals:
            counts[journal] = counts.get(journal, 0) + 1

        ordered_by_journal = tuple(sorted(counts.items()))

        return cls(
            total_papers=len(papers),
            papers_with_journal=len(journals),
            papers_without_journal=len(papers) - len(journals),
            unique_journals=len(ordered_by_journal),
            by_journal=ordered_by_journal,
        )

    @property
    def journal_coverage_rate(self) -> float:
        if self.total_papers == 0:
            return 0.0
        return self.papers_with_journal / self.total_papers
