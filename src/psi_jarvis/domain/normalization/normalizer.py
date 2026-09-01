import re
from dataclasses import replace

from psi_jarvis.domain.paper import Paper


class PaperNormalizer:
    def normalize(self, paper: Paper) -> Paper:
        return replace(
            paper,
            title=self._text(paper.title),
            authors=tuple(self._text(author) for author in paper.authors if self._text(author)),
            abstract=self._optional_text(paper.abstract),
            doi=self._normalize_doi(paper.doi),
            pmid=self._normalize_pmid(paper.pmid),
            publication_year=paper.publication_year,
            journal=self._optional_text(paper.journal),
        )

    @staticmethod
    def _text(value: str | None) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        normalized = cls._text(value)
        return normalized or None

    @classmethod
    def _normalize_doi(cls, value: str | None) -> str | None:
        normalized = cls._optional_text(value)
        if normalized is None:
            return None

        prefixes = (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
        )

        lowered = normalized.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break

        return normalized or None

    @classmethod
    def _normalize_pmid(cls, value: str | None) -> str | None:
        normalized = cls._optional_text(value)
        if normalized is None:
            return None

        if normalized.lower().startswith("pmid:"):
            normalized = normalized[5:].strip()

        return normalized or None
