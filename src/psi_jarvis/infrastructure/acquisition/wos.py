from __future__ import annotations

import json
from dataclasses import dataclass
from re import search
from collections.abc import Callable
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
from psi_jarvis.infrastructure.acquisition.wos_transport import (
    WebOfScienceStarterTransport,
    WebOfScienceTransportConfig,
)


_PAPER_ID_NAMESPACE = UUID("6ba7b813-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class WebOfScienceJsonMapper:
    format_name: str = "Web of Science Starter JSON"
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
                    AcquisitionIssue(
                        "invalid_format", f"Invalid Web of Science JSON: {exc}"
                    ),
                ),
            )
        hits = payload.get("hits", [])
        if not isinstance(hits, list):
            return AcquisitionResult(
                receipt=receipt,
                issues=(
                    AcquisitionIssue(
                        "invalid_format", "Web of Science hits must be a list"
                    ),
                ),
            )
        papers: list[Paper] = []
        issues: list[AcquisitionIssue] = []
        for ordinal, entry in enumerate(hits, start=1):
            if not isinstance(entry, dict):
                issues.append(
                    AcquisitionIssue(
                        "invalid_record",
                        "Web of Science hit must be an object",
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
        source_record_id = self._text(entry.get("uid"))
        title = self._text(entry.get("title"))
        source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
        identifiers = (
            entry.get("identifiers")
            if isinstance(entry.get("identifiers"), dict)
            else {}
        )
        names = entry.get("names") if isinstance(entry.get("names"), dict) else {}
        authors_raw = names.get("authors", [])
        authors = tuple(
            self._text(
                author.get("displayName") if isinstance(author, dict) else author
            )
            for author in authors_raw
            if self._text(
                author.get("displayName") if isinstance(author, dict) else author
            )
        )
        doi = self._text(identifiers.get("doi"))
        journal = self._text(source.get("sourceTitle"))
        year = self._year(source.get("publishYear"))
        issues: list[AcquisitionIssue] = []
        if not title:
            issues.append(
                AcquisitionIssue(
                    "missing_title",
                    "Web of Science record has no title",
                    "warning",
                    ordinal,
                )
            )
        if not source_record_id:
            issues.append(
                AcquisitionIssue(
                    "missing_wos_id",
                    "Web of Science record has no UID",
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
        return Paper(
            id=paper_id,
            title=title or "",
            authors=authors,
            doi=doi,
            publication_year=year,
            journal=journal,
            provenances=(provenance,),
        ), tuple(issues)

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _year(value: object) -> int | None:
        match = search(r"\b(\d{4})\b", str(value or ""))
        return int(match.group(1)) if match else None


class WebOfScienceAdapter(RemoteBibliographicAdapter):
    source_key = "web_of_science"
    adapter_key = "wos-starter"
    adapter_version = "1"
    format_name = "Web of Science Starter JSON"
    format_version = "1"
    mapping_version = "1"

    def __init__(
        self,
        fetcher: Callable[[BibliographicQuery], RemoteAcquisitionResponse],
        clock=None,
        mapper: WebOfScienceJsonMapper | None = None,
    ) -> None:
        super().__init__(clock=clock)
        self._fetcher = fetcher
        self._mapper = mapper or WebOfScienceJsonMapper()

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        return self._fetcher(query)

    def map_response(
        self, response: RemoteAcquisitionResponse, receipt: AcquisitionReceipt
    ) -> AcquisitionResult:
        return self._mapper.map(response, receipt)


def build_wos_adapter(
    config: WebOfScienceTransportConfig,
    clock=None,
    opener: Callable[..., object] | None = None,
) -> WebOfScienceAdapter:
    transport = WebOfScienceStarterTransport(config=config, opener=opener)
    return WebOfScienceAdapter(fetcher=transport.fetch, clock=clock)
