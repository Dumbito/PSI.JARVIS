from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid5

from psi_jarvis.application.acquisition.contracts import (
    AcquisitionIssue,
    AcquisitionRequest,
    AcquisitionResult,
)
from psi_jarvis.domain.bibliography.provenance import (
    AcquisitionReceipt,
    BibliographicProvenance,
    sha256_text,
)
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.text_encoding import read_text_with_encoding_fallback


class RISImporter:
    """Adaptador local para ficheros RIS; no realiza llamadas de red."""

    source_key = "ris"
    adapter_key = "local-ris"
    adapter_version = "1"
    format_name = "RIS"
    format_version = "1"
    mapping_version = "1"

    def __init__(self, clock=None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def acquire(self, request: AcquisitionRequest) -> AcquisitionResult:
        path = Path(request.location)
        if not path.exists():
            return AcquisitionResult(
                receipt=None,
                issues=(
                    AcquisitionIssue(
                        "source_unavailable", f"RIS file not found: {path}"
                    ),
                ),
            )
        if path.suffix.lower() != ".ris":
            return AcquisitionResult(
                receipt=None,
                issues=(AcquisitionIssue("invalid_format", "Expected a RIS file"),),
            )

        content = read_text_with_encoding_fallback(path)
        receipt = AcquisitionReceipt.create(
            source_key=self.source_key,
            adapter_key=self.adapter_key,
            adapter_version=self.adapter_version,
            acquired_at=request.acquired_at or self._clock(),
            request_payload=request.payload(),
            input_content=content,
            source_locator=request.location,
        )
        records, error = self._parse_records(content)
        if error is not None:
            return AcquisitionResult(
                receipt=receipt, issues=(AcquisitionIssue("invalid_format", error),)
            )

        papers = []
        issues = []
        for ordinal, fields, raw_record in records:
            paper, record_issues = self._map_record(
                receipt, ordinal, fields, raw_record
            )
            issues.extend(record_issues)
            if paper is not None:
                papers.append(paper)
        return AcquisitionResult(
            receipt=receipt, papers=tuple(papers), issues=tuple(issues)
        )

    @staticmethod
    def _parse_records(content: str):
        records = []
        current: dict[str, list[str]] | None = None
        raw_lines: list[str] = []
        ordinal = 0
        normalized_content = content.lstrip(chr(0xFEFF))
        for line in normalized_content.splitlines():
            if not line.strip():
                continue
            if len(line) < 5 or line[2:5] != "  -":
                return (), f"Malformed RIS line: {line}"
            tag = line[:2].upper()
            value = line[5:].strip()
            if tag == "TY":
                if current is not None:
                    return (), "RIS record started before previous record ended"
                current = {tag: [value]}
                raw_lines = [line]
                ordinal += 1
                continue
            if current is None:
                return (), "RIS content must begin each record with TY"
            raw_lines.append(line)
            if tag == "ER":
                records.append((ordinal, current, "\n".join(raw_lines)))
                current = None
                raw_lines = []
            else:
                current.setdefault(tag, []).append(value)
        if current is not None:
            return (), "RIS record is missing ER terminator"
        return tuple(records), None

    def _map_record(self, receipt, ordinal, fields, raw_record):
        issues = []
        title = self._first(fields, "TI", "T1") or ""
        if not title:
            issues.append(
                AcquisitionIssue(
                    "missing_title", "RIS record has no title", "warning", ordinal
                )
            )
        year, year_issue = self._year(self._first(fields, "PY", "Y1"), ordinal)
        if year_issue is not None:
            issues.append(year_issue)
        known_tags = {
            "TY",
            "ER",
            "TI",
            "T1",
            "AU",
            "AB",
            "DO",
            "ID",
            "PM",
            "PY",
            "Y1",
            "JO",
            "JF",
            "T2",
            "UR",
        }
        for tag in sorted(set(fields) - known_tags):
            issues.append(
                AcquisitionIssue(
                    "unknown_field", f"Unsupported RIS field: {tag}", "warning", ordinal
                )
            )
        provenance = BibliographicProvenance(
            receipt=receipt,
            record_ordinal=ordinal,
            format_name=self.format_name,
            format_version=self.format_version,
            mapping_version=self.mapping_version,
            raw_record_sha256=sha256_text(raw_record),
            source_record_id=self._first(fields, "ID", "UR"),
        )
        return (
            Paper(
                id=uuid5(
                    UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8"),
                    "|".join(
                        (str(receipt.batch_id), str(ordinal), sha256_text(raw_record))
                    ),
                ),
                title=title,
                authors=tuple(fields.get("AU", ())),
                abstract=self._first(fields, "AB"),
                doi=self._first(fields, "DO"),
                pmid=self._first(fields, "PM"),
                publication_year=year,
                journal=self._first(fields, "JO", "JF", "T2"),
                provenances=(provenance,),
            ),
            tuple(issues),
        )

    @staticmethod
    def _first(fields, *names):
        for name in names:
            values = fields.get(name, ())
            if values:
                return values[0]
        return None

    @staticmethod
    def _year(value, ordinal):
        if value is None:
            return None, None
        try:
            return int(value[:4]), None
        except ValueError:
            return None, AcquisitionIssue(
                "invalid_year",
                f"Invalid RIS publication year: {value}",
                "warning",
                ordinal,
            )
