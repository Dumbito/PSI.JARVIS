from dataclasses import dataclass
from typing import Iterable

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class AuthorAnalysis:
    total_papers: int
    papers_with_authors: int
    papers_without_authors: int
    unique_authors: int
    by_author: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        values = (
            self.total_papers,
            self.papers_with_authors,
            self.papers_without_authors,
            self.unique_authors,
        )
        if any(value < 0 for value in values):
            raise ValueError("Author counts cannot be negative")

        if self.papers_with_authors + self.papers_without_authors != self.total_papers:
            raise ValueError("Author counts must equal total papers")

        if self.unique_authors != len(self.by_author):
            raise ValueError("Unique authors must equal author distribution size")

        if any(not author.strip() for author, _ in self.by_author):
            raise ValueError("Author names cannot be empty")

        if any(count < 0 for _, count in self.by_author):
            raise ValueError("Author distribution counts cannot be negative")

        if sum(count for _, count in self.by_author) < self.papers_with_authors:
            raise ValueError("Author distribution cannot be smaller than papers with authors")


    @classmethod
    def from_papers(cls, papers: Iterable[Paper]) -> "AuthorAnalysis":
        papers = tuple(papers)

        authors_by_paper: list[tuple[str, ...]] = []
        counts: dict[str, int] = {}

        for paper in papers:
            authors = tuple(
                author.strip()
                for author in paper.authors
                if author.strip()
            )
            authors_by_paper.append(authors)

            for author in authors:
                counts[author] = counts.get(author, 0) + 1

        ordered_by_author = tuple(sorted(counts.items()))
        papers_with_authors = sum(bool(authors) for authors in authors_by_paper)

        return cls(
            total_papers=len(papers),
            papers_with_authors=papers_with_authors,
            papers_without_authors=len(papers) - papers_with_authors,
            unique_authors=len(ordered_by_author),
            by_author=ordered_by_author,
        )

    @property
    def author_coverage_rate(self) -> float:
        if self.total_papers == 0:
            return 0.0
        return self.papers_with_authors / self.total_papers
