from collections.abc import Iterable
from dataclasses import dataclass

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class PublicationYearAnalysis:
    total_papers: int
    papers_with_year: int
    papers_without_year: int
    year_min: int | None
    year_max: int | None
    by_year: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        values = (
            self.total_papers,
            self.papers_with_year,
            self.papers_without_year,
        )
        if any(value < 0 for value in values):
            raise ValueError("Publication year counts cannot be negative")

        if self.papers_with_year + self.papers_without_year != self.total_papers:
            raise ValueError("Year counts must equal total papers")

        if self.year_min is None and self.year_max is not None:
            raise ValueError("Year minimum cannot be missing when maximum exists")

        if self.year_min is not None and self.year_max is None:
            raise ValueError("Year maximum cannot be missing when minimum exists")

        if (
            self.year_min is not None
            and self.year_max is not None
            and self.year_min > self.year_max
        ):
            raise ValueError("Year minimum cannot exceed year maximum")

        if sum(count for _, count in self.by_year) != self.papers_with_year:
            raise ValueError("Year distribution counts must equal papers with year")

        if any(count < 0 for _, count in self.by_year):
            raise ValueError("Year distribution counts cannot be negative")

    @classmethod
    def from_papers(cls, papers: Iterable[Paper]) -> "PublicationYearAnalysis":
        papers = tuple(papers)
        years = tuple(
            paper.publication_year
            for paper in papers
            if paper.publication_year is not None
        )

        counts: dict[int, int] = {}
        for year in years:
            counts[year] = counts.get(year, 0) + 1

        ordered_by_year = tuple(sorted(counts.items()))

        return cls(
            total_papers=len(papers),
            papers_with_year=len(years),
            papers_without_year=len(papers) - len(years),
            year_min=min(years) if years else None,
            year_max=max(years) if years else None,
            by_year=ordered_by_year,
        )

    @property
    def year_coverage_rate(self) -> float:
        if self.total_papers == 0:
            return 0.0
        return self.papers_with_year / self.total_papers
