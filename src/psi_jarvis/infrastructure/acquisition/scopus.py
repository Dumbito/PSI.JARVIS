from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from re import search
from uuid import UUID, uuid5

from psi_jarvis.application.acquisition.contracts import (
    AcquisitionIssue,
    AcquisitionResult,
    BibliographicQuery,
)
from psi_jarvis.domain.bibliography.provenance import (
    AcquisitionReceipt,
    BibliographicProvenance,
    sha256_text,
)
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.acquisition.remote_base import (
    RemoteAcquisitionResponse,
    RemoteBibliographicAdapter,
)
from psi_jarvis.infrastructure.acquisition.scopus_transport import (
    ScopusSearchTransport,
    ScopusTransportConfig,
)

_PAPER_ID_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class ScopusJsonMapper:
    """Mapeo determinista del Scopus Search JSON hacia el dominio."""

    format_name: str = "Scopus Search JSON"
    format_version: str = "1"
    mapping_version: str = "1"

    def map(
        self, response: RemoteAcquisitionResponse, receipt: AcquisitionReceipt
    ) -> AcquisitionResult:
        try:
            payload = json.loads(response.raw_content)
        except json.JSONDecodeError as exc:
            return AcquisitionResult(
                receipt=receipt,
                issues=(
                    AcquisitionIssue("invalid_format", f"Invalid Scopus JSON: {exc}"),
                ),
            )

        entries = payload.get("search-results", {}).get("entry", [])
        if not isinstance(entries, list):
            return AcquisitionResult(
                receipt=receipt,
                issues=(
                    AcquisitionIssue(
                        "invalid_format", "Scopus search-results.entry must be a list"
                    ),
                ),
            )

        papers: list[Paper] = []
        issues: list[AcquisitionIssue] = []
        for ordinal, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                issues.append(
                    AcquisitionIssue(
                        "invalid_record",
                        "Scopus entry must be an object",
                        "warning",
                        ordinal,
                    )
                )
                continue
            paper, record_issues = self._map_entry(receipt, ordinal, entry)
            issues.extend(record_issues)
            if paper is not None:
                papers.append(paper)

        return AcquisitionResult(
            receipt=receipt, papers=tuple(papers), issues=tuple(issues)
        )

    def _map_entry(self, receipt: AcquisitionReceipt, ordinal: int, entry: dict):
        source_record_id = self._text(entry.get("dc:identifier"))
        title = self._text(entry.get("dc:title"))
        abstract = self._text(entry.get("dc:description"))
        journal = self._text(entry.get("prism:publicationName"))
        doi = self._text(entry.get("prism:doi"))
        publication_year = self._publication_year(entry.get("prism:coverDate"))
        authors = self._authors(entry.get("dc:creator"))

        issues: list[AcquisitionIssue] = []
        if not title:
            issues.append(
                AcquisitionIssue(
                    "missing_title", "Scopus record has no title", "warning", ordinal
                )
            )
        if not source_record_id:
            issues.append(
                AcquisitionIssue(
                    "missing_scopus_id",
                    "Scopus record has no identifier",
                    "warning",
                    ordinal,
                )
            )
        if not journal:
            issues.append(
                AcquisitionIssue(
                    "missing_journal",
                    "Scopus record has no publication name",
                    "warning",
                    ordinal,
                )
            )

        raw_record = json.dumps(
            entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        provenance = BibliographicProvenance(
            receipt=receipt,
            record_ordinal=ordinal,
            format_name=self.format_name,
            format_version=self.format_version,
            mapping_version=self.mapping_version,
            raw_record_sha256=sha256_text(raw_record),
            source_record_id=source_record_id,
        )
        paper_id = uuid5(
            _PAPER_ID_NAMESPACE,
            "|".join((str(receipt.batch_id), str(ordinal), sha256_text(raw_record))),
        )

        return (
            Paper(
                id=paper_id,
                title=title or "",
                authors=authors,
                abstract=abstract,
                doi=doi,
                publication_year=publication_year,
                journal=journal,
                provenances=(provenance,),
            ),
            tuple(issues),
        )

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _authors(cls, value: object) -> tuple[str, ...]:
        text = cls._text(value)
        if not text:
            return ()
        return tuple(part.strip() for part in text.split(",") if part.strip())

    @staticmethod
    def _publication_year(value: object) -> int | None:
        text = str(value).strip() if value is not None else ""
        match = search(r"\b(\d{4})\b", text)
        return int(match.group(1)) if match else None


class ScopusAdapter(RemoteBibliographicAdapter):
    """Adaptador Scopus con transporte inyectado y mapeo JSON determinista."""

    source_key = "scopus"
    adapter_key = "scopus-search"
    adapter_version = "1"
    format_name = "Scopus Search JSON"
    format_version = "1"
    mapping_version = "1"

    def __init__(
        self,
        fetcher: Callable[[BibliographicQuery], RemoteAcquisitionResponse],
        clock=None,
        mapper: ScopusJsonMapper | None = None,
    ) -> None:
        super().__init__(clock=clock)
        self._fetcher = fetcher
        self._mapper = mapper or ScopusJsonMapper(
            format_name=self.format_name,
            format_version=self.format_version,
            mapping_version=self.mapping_version,
        )

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        return self._fetcher(query)

    def map_response(
        self,
        response: RemoteAcquisitionResponse,
        receipt: AcquisitionReceipt,
    ) -> AcquisitionResult:
        return self._mapper.map(response, receipt)


def build_scopus_adapter(
    config: ScopusTransportConfig,
    clock=None,
    opener: Callable[..., object] | None = None,
) -> ScopusAdapter:
    """Compone el adapter Scopus con su transporte Search API."""

    transport = ScopusSearchTransport(config=config, opener=opener)
    return ScopusAdapter(fetcher=transport.fetch, clock=clock)
