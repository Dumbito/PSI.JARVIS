from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from psi_jarvis.application.acquisition.contracts import BibliographicQuery
from psi_jarvis.infrastructure.acquisition.remote_base import RemoteAcquisitionResponse


DEFAULT_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass(frozen=True)
class PubMedTransportConfig:
    """Configuración del transporte NCBI E-utilities sin secretos persistidos."""

    tool: str
    email: str
    api_key: str | None = None
    base_url: str = DEFAULT_EUTILS_BASE_URL
    timeout_seconds: float = 20.0
    retmax: int = 20

    def __post_init__(self) -> None:
        if not self.tool.strip() or " " in self.tool.strip():
            raise ValueError("NCBI tool must be a non-empty string without spaces")
        if not self.email.strip() or " " in self.email.strip() or "@" not in self.email:
            raise ValueError("NCBI email must be a valid non-empty email-like value")
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("NCBI API key cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("NCBI timeout must be positive")
        if not 1 <= self.retmax <= 10000:
            raise ValueError("NCBI PubMed retmax must be between 1 and 10000")


class PubMedEUtilsTransport:
    """Transporte HTTP mínimo: ESearch para UIDs seguido de EFetch en XML."""

    def __init__(
        self,
        config: PubMedTransportConfig,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen

    def fetch(self, query: BibliographicQuery) -> RemoteAcquisitionResponse:
        search_params = self._common_params()
        search_params.update(self._query_parameters(query))
        search_params["db"] = "pubmed"
        search_params["term"] = query.text
        search_params["retmode"] = "xml"
        search_params["retmax"] = str(self._config.retmax)

        search_xml = self._request("esearch.fcgi", search_params)
        pmids = self._parse_pmids(search_xml)
        if not pmids:
            return RemoteAcquisitionResponse(
                raw_content="<PubmedArticleSet />",
                source_locator=self._source_locator("esearch.fcgi", search_params),
            )

        fetch_params = self._common_params()
        fetch_params.update(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            }
        )
        fetch_xml = self._request("efetch.fcgi", fetch_params)
        return RemoteAcquisitionResponse(
            raw_content=fetch_xml,
            source_locator=self._source_locator("efetch.fcgi", fetch_params),
        )

    def _request(self, endpoint: str, params: Mapping[str, str]) -> str:
        url = f"{self._config.base_url.rstrip('/')}/{endpoint}"
        request = Request(url, data=urlencode(dict(params)).encode("utf-8"), method="POST")
        request.add_header("Accept", "application/xml")
        request.add_header("User-Agent", self._config.tool)
        with self._opener(request, timeout=self._config.timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"NCBI E-utilities returned HTTP {status}")
            content = response.read()
        return content.decode("utf-8")

    def _common_params(self) -> dict[str, str]:
        params = {"tool": self._config.tool, "email": self._config.email}
        if self._config.api_key:
            params["api_key"] = self._config.api_key
        return params

    @staticmethod
    def _query_parameters(query: BibliographicQuery) -> dict[str, str]:
        allowed = {"retstart", "sort", "datetype", "reldate", "mindate", "maxdate", "field"}
        parameters: dict[str, str] = {}
        for name, value in query.parameters:
            if name not in allowed:
                raise ValueError(f"Unsupported PubMed E-utilities parameter: {name}")
            parameters[name] = value
        return parameters

    @staticmethod
    def _parse_pmids(xml_content: str) -> tuple[str, ...]:
        try:
            root = ElementTree.fromstring(xml_content)
        except ElementTree.ParseError as exc:
            raise RuntimeError(f"Invalid NCBI ESearch XML: {exc}") from exc
        return tuple(
            value.strip()
            for element in root.findall(".//Id")
            if (value := element.text or "").strip()
        )

    def _source_locator(self, endpoint: str, params: Mapping[str, str]) -> str:
        safe_params = dict(params)
        safe_params.pop("api_key", None)
        safe_params.pop("email", None)
        safe_params.pop("tool", None)
        return f"{self._config.base_url.rstrip('/')}/{endpoint}?{urlencode(safe_params)}"
