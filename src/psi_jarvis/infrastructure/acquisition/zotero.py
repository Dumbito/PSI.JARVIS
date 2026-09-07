from __future__ import annotations

import json
from dataclasses import dataclass
from re import search
from typing import Callable
from uuid import UUID, uuid5

from psi_jarvis.application.acquisition.contracts import AcquisitionIssue, AcquisitionResult, BibliographicQuery
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt, BibliographicProvenance, sha256_text
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse, RemoteBibliographicAdapter
from psi_jarvis.infrastructure.acquisition.zotero_transport import ZoteroTransportConfig, ZoteroWebApiTransport


_PAPER_ID_NAMESPACE = UUID("6ba7b814-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class ZoteroJsonMapper:
    format_name: str = "Zotero Web API JSON"
    format_version: str = "3"
    mapping_version: str = "1"

    def map(self, response: RemoteAcquisitionResponse, receipt: AcquisitionReceipt) -> AcquisitionResult:
        try:
            payload = json.loads(response.raw_content)
        except json.JSONDecodeError as exc:
            return AcquisitionResult(receipt=receipt, issues=(AcquisitionIssue("invalid_format", f"Invalid Zotero JSON: {exc}"),))
        if not isinstance(payload, list):
            return AcquisitionResult(receipt=receipt, issues=(AcquisitionIssue("invalid_format", "Zotero response must be a list"),))
        papers: list[Paper] = []
        issues: list[AcquisitionIssue] = []
        for ordinal, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                issues.append(AcquisitionIssue("invalid_record", "Zotero item must be an object", "warning", ordinal))
                continue
            paper, record_issues = self._map_item(receipt, ordinal, item)
            issues.extend(record_issues)
            if paper is not None:
                papers.append(paper)
        return AcquisitionResult(receipt=receipt, papers=tuple(papers), issues=tuple(issues))

    def _map_item(self, receipt: AcquisitionReceipt, ordinal: int, item: dict):
        source_record_id = self._text(item.get("key"))
        data = item.get("data") if isinstance(item.get("data"), dict) else item
        title = self._text(data.get("title"))
        abstract = self._text(data.get("abstractNote"))
        doi = self._text(data.get("DOI"))
        journal = self._text(data.get("publicationTitle"))
        year = self._year(data.get("date"))
        authors = self._authors(data.get("creators"))
        issues: list[AcquisitionIssue] = []
        if not title:
            issues.append(AcquisitionIssue("missing_title", "Zotero item has no title", "warning", ordinal))
        if not source_record_id:
            issues.append(AcquisitionIssue("missing_zotero_id", "Zotero item has no item key", "warning", ordinal))
        raw_record = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        provenance = BibliographicProvenance(receipt=receipt, record_ordinal=ordinal, format_name=self.format_name, format_version=self.format_version, mapping_version=self.mapping_version, raw_record_sha256=sha256_text(raw_record), source_record_id=source_record_id)
        paper_id = uuid5(_PAPER_ID_NAMESPACE, "|".join((str(receipt.batch_id), str(ordinal), sha256_text(raw_record))))
        return Paper(id=paper_id, title=title or "", authors=authors, abstract=abstract, doi=doi, publication_year=year, journal=journal, provenances=(provenance,)), tuple(issues)

    @staticmethod
    def _text(value: object) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @classmethod
    def _authors(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        result: list[str] = []
        for creator in value:
            if not isinstance(creator, dict):
                continue
            name = cls._text(creator.get("name"))
            if not name:
                first = cls._text(creator.get("firstName"))
                last = cls._text(creator.get("lastName"))
                name = ", ".join(part for part in (last, first) if part)
            if name:
                result.append(name)
        return tuple(result)

    @staticmethod
    def _year(value: object) -> int | None:
        match = search(r"\b(\d{4})\b", str(value or ""))
        return int(match.group(1)) if match else None


class ZoteroAdapter(RemoteBibliographicAdapter):
    source_key = "zotero"
    adapter_key = "zotero-web-api"
    adapter_version = "1"
    format_name = "Zotero Web API JSON"
    format_version = "3"
    mapping_version = "1"

    def __init__(self, fetcher: Callable[[BibliographicQuery], RemoteAcquisitionResponse], clock=None, mapper: ZoteroJsonMapper | None = None) -> None:
        super().__init__(clock=clock)
        self._fetcher = fetcher
        self._mapper = mapper or ZoteroJsonMapper()

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        return self._fetcher(query)

    def map_response(self, response: RemoteAcquisitionResponse, receipt: AcquisitionReceipt) -> AcquisitionResult:
        return self._mapper.map(response, receipt)


def build_zotero_adapter(config: ZoteroTransportConfig, clock=None, opener: Callable[..., object] | None = None) -> ZoteroAdapter:
    transport = ZoteroWebApiTransport(config=config, opener=opener)
    return ZoteroAdapter(fetcher=transport.fetch, clock=clock)
