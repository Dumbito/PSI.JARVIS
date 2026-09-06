from dataclasses import dataclass, replace

from psi_jarvis.domain.paper import Paper


@dataclass(frozen=True)
class DeduplicationResult:
    papers: tuple[Paper, ...]
    total_input: int
    unique_papers: int
    duplicates_removed: int


class PaperDeduplicator:
    def deduplicate(self, papers: list[Paper] | tuple[Paper, ...]) -> DeduplicationResult:
        unique: list[Paper] = []
        positions: dict[str, int] = {}

        for paper in papers:
            key = self._identity_key(paper)

            if key in positions:
                position = positions[key]
                unique[position] = replace(
                    unique[position],
                    provenances=self._merged_provenances(
                        unique[position].provenances,
                        paper.provenances,
                    ),
                )
                continue

            positions[key] = len(unique)
            unique.append(paper)

        total_input = len(papers)
        unique_papers = len(unique)

        return DeduplicationResult(
            papers=tuple(unique),
            total_input=total_input,
            unique_papers=unique_papers,
            duplicates_removed=total_input - unique_papers,
        )

    @staticmethod
    def _identity_key(paper: Paper) -> str:
        if paper.doi:
            return f"doi:{paper.doi.strip().lower()}"

        if paper.pmid:
            return f"pmid:{paper.pmid.strip()}"

        title = " ".join(paper.title.lower().split())

        return f"title:{title}"

    @staticmethod
    def _merged_provenances(first, second):
        by_key = {provenance.key: provenance for provenance in (*first, *second)}
        return tuple(
            by_key[key]
            for key in sorted(by_key)
        )
