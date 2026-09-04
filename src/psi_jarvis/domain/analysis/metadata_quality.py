from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class MetadataFieldStatistics:
    field: str
    present: int
    missing: int
    total: int

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("Metadata field cannot be empty")

        values = (self.present, self.missing, self.total)
        if any(value < 0 for value in values):
            raise ValueError("Metadata statistics cannot be negative")

        if self.present + self.missing != self.total:
            raise ValueError("Present and missing counts must equal total")

    @property
    def completeness_rate(self) -> float:
        return 0.0 if self.total == 0 else self.present / self.total


@dataclass(frozen=True)
class MetadataQuality:
    total_papers: int
    fields: tuple[MetadataFieldStatistics, ...]

    def __post_init__(self) -> None:
        if self.total_papers < 0:
            raise ValueError("Total papers cannot be negative")

        if any(field.total != self.total_papers for field in self.fields):
            raise ValueError("Every metadata field must use the total paper count")

    @classmethod
    def from_papers(cls, papers: Iterable[Paper]) -> "MetadataQuality":
        papers = tuple(papers)

        field_extractors = (
            ("title", lambda paper: bool(paper.title.strip())),
            ("authors", lambda paper: bool(paper.authors)),
            ("abstract", lambda paper: bool(paper.abstract and paper.abstract.strip())),
            ("doi", lambda paper: bool(paper.doi and paper.doi.strip())),
            ("pmid", lambda paper: bool(paper.pmid and paper.pmid.strip())),
            ("publication_year", lambda paper: paper.publication_year is not None),
            ("journal", lambda paper: bool(paper.journal and paper.journal.strip())),
        )

        statistics = []
        for field, extractor in field_extractors:
            present = sum(1 for paper in papers if extractor(paper))
            statistics.append(
                MetadataFieldStatistics(
                    field=field,
                    present=present,
                    missing=len(papers) - present,
                    total=len(papers),
                )
            )

        return cls(
            total_papers=len(papers),
            fields=tuple(statistics),
        )

    @property
    def total_fields(self) -> int:
        return len(self.fields)

    @property
    def overall_completeness_rate(self) -> float:
        if self.total_papers == 0 or not self.fields:
            return 0.0
        total_present = sum(field.present for field in self.fields)
        total_possible = self.total_papers * len(self.fields)
        return total_present / total_possible

    def by_field(self, field: str) -> MetadataFieldStatistics | None:
        return next(
            (item for item in self.fields if item.field == field),
            None,
        )
