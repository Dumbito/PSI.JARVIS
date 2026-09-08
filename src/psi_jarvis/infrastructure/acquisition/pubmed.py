from __future__ import annotations

from dataclasses import dataclass
from re import search
from collections.abc import Callable
from uuid import UUID, uuid5
from xml.etree import ElementTree

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
from psi_jarvis.infrastructure.acquisition.pubmed_transport import (
    PubMedEUtilsTransport,
    PubMedTransportConfig,
)


_PAPER_ID_NAMESPACE = UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class PubMedXmlMapper:
    """Mapeo determinista de PubMed XML hacia el dominio de PSI.JARVIS."""

    format_name: str = "PubMed XML"
    format_version: str = "1"
    mapping_version: str = "1"

    def map(
        self, response: RemoteAcquisitionResponse, receipt: AcquisitionReceipt
    ) -> AcquisitionResult:
        try:
            root = ElementTree.fromstring(response.raw_content)
        except ElementTree.ParseError as exc:
            return AcquisitionResult(
                receipt=receipt,
                issues=(
                    AcquisitionIssue("invalid_format", f"Invalid PubMed XML: {exc}"),
                ),
            )

        papers: list[Paper] = []
        issues: list[AcquisitionIssue] = []
        records = root.findall(".//PubmedArticle")

        for ordinal, article in enumerate(records, start=1):
            paper, record_issues = self._map_article(receipt, ordinal, article)
            issues.extend(record_issues)
            if paper is not None:
                papers.append(paper)

        return AcquisitionResult(
            receipt=receipt, papers=tuple(papers), issues=tuple(issues)
        )

    def _map_article(
        self, receipt: AcquisitionReceipt, ordinal: int, article: ElementTree.Element
    ):
        citation = article.find("MedlineCitation")
        if citation is None:
            return None, (
                AcquisitionIssue(
                    "missing_citation",
                    "PubMed record has no MedlineCitation",
                    "warning",
                    ordinal,
                ),
            )

        article_data = citation.find("Article")
        if article_data is None:
            return None, (
                AcquisitionIssue(
                    "missing_article",
                    "PubMed record has no Article element",
                    "warning",
                    ordinal,
                ),
            )

        raw_record = ElementTree.tostring(article, encoding="unicode")
        title = self._text(article_data.find("ArticleTitle"))
        pmid = self._text(citation.find("PMID"))
        abstract = self._abstract(article_data)
        authors = self._authors(article_data)
        doi = self._doi(article)
        journal = self._text(article_data.find("Journal/Title"))
        publication_year = self._publication_year(article_data)

        issues: list[AcquisitionIssue] = []
        if not title:
            issues.append(
                AcquisitionIssue(
                    "missing_title", "PubMed record has no title", "warning", ordinal
                )
            )
        if not pmid:
            issues.append(
                AcquisitionIssue(
                    "missing_pmid", "PubMed record has no PMID", "warning", ordinal
                )
            )
        if article_data.find("Journal") is None:
            issues.append(
                AcquisitionIssue(
                    "missing_journal",
                    "PubMed record has no journal",
                    "warning",
                    ordinal,
                )
            )

        provenance = BibliographicProvenance(
            receipt=receipt,
            record_ordinal=ordinal,
            format_name=self.format_name,
            format_version=self.format_version,
            mapping_version=self.mapping_version,
            raw_record_sha256=sha256_text(raw_record),
            source_record_id=pmid,
        )
        paper_id = uuid5(
            _PAPER_ID_NAMESPACE,
            "|".join((str(receipt.batch_id), str(ordinal), sha256_text(raw_record))),
        )

        return (
            Paper(
                id=paper_id,
                title=title,
                authors=authors,
                abstract=abstract,
                doi=doi,
                pmid=pmid,
                publication_year=publication_year,
                journal=journal,
                provenances=(provenance,),
            ),
            tuple(issues),
        )

    @staticmethod
    def _text(element: ElementTree.Element | None) -> str | None:
        if element is None:
            return None
        value = "".join(element.itertext()).strip()
        return value or None

    @classmethod
    def _authors(cls, article: ElementTree.Element) -> tuple[str, ...]:
        result: list[str] = []
        for author in article.findall("AuthorList/Author"):
            collective = cls._text(author.find("CollectiveName"))
            if collective:
                result.append(collective)
                continue
            last_name = cls._text(author.find("LastName"))
            initials = cls._text(author.find("Initials"))
            if last_name and initials:
                result.append(f"{last_name}, {initials}")
            elif last_name:
                result.append(last_name)
            elif initials:
                result.append(initials)
        return tuple(result)

    @classmethod
    def _abstract(cls, article: ElementTree.Element) -> str | None:
        parts: list[str] = []
        for abstract_text in article.findall("Abstract/AbstractText"):
            text = cls._text(abstract_text)
            if not text:
                continue
            label = abstract_text.attrib.get("Label", "").strip()
            parts.append(f"{label}: {text}" if label else text)
        return "\n".join(parts) or None

    @classmethod
    def _doi(cls, article: ElementTree.Element) -> str | None:
        for identifier in article.findall("PubmedData/ArticleIdList/ArticleId"):
            if identifier.attrib.get("IdType", "").lower() == "doi":
                return cls._text(identifier)
        return None

    @staticmethod
    def _publication_year(article: ElementTree.Element) -> int | None:
        for path in (
            "Journal/JournalIssue/PubDate/Year",
            "Journal/JournalIssue/PubDate/MedlineDate",
        ):
            value = article.findtext(path)
            if not value:
                continue
            match = search(r"\b(\d{4})\b", value)
            if match:
                return int(match.group(1))
        return None


class PubMedAdapter(RemoteBibliographicAdapter):
    """Adaptador PubMed con transporte inyectado y mapeo XML determinista."""

    source_key = "pubmed"
    adapter_key = "pubmed-efetch"
    adapter_version = "1"
    format_name = "PubMed XML"
    format_version = "1"
    mapping_version = "1"

    def __init__(
        self,
        fetcher: Callable[[BibliographicQuery], RemoteAcquisitionResponse],
        clock=None,
        mapper: PubMedXmlMapper | None = None,
    ) -> None:
        super().__init__(clock=clock)
        self._fetcher = fetcher
        self._mapper = mapper or PubMedXmlMapper(
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


def build_pubmed_adapter(
    config: PubMedTransportConfig,
    clock=None,
    opener: Callable[..., object] | None = None,
) -> PubMedAdapter:
    """Compone el adapter PubMed con su transporte E-utilities."""

    transport = PubMedEUtilsTransport(config=config, opener=opener)
    return PubMedAdapter(fetcher=transport.fetch, clock=clock)
