from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pandas as pd

from psi_jarvis.application.acquisition.contracts import (
    AcquisitionIssue,
    AcquisitionRequest,
    AcquisitionResult,
)
from psi_jarvis.core.result import Result
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.importers.tabular import TabularImporter
from psi_jarvis.infrastructure.text_encoding import read_text_with_encoding_fallback


class CSVImporter:
    source_key = "csv"
    adapter_key = "local-csv"
    adapter_version = "1"
    format_name = "CSV"

    def __init__(self, clock=None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def acquire(self, request: AcquisitionRequest) -> AcquisitionResult:
        file_path = Path(request.location)
        if not file_path.exists():
            return AcquisitionResult(
                receipt=None,
                issues=(
                    AcquisitionIssue(
                        "source_unavailable", f"CSV file not found: {file_path}"
                    ),
                ),
            )
        if file_path.suffix.lower() != ".csv":
            return AcquisitionResult(
                receipt=None,
                issues=(AcquisitionIssue("invalid_format", "Expected a CSV file"),),
            )
        content = read_text_with_encoding_fallback(file_path)
        receipt = AcquisitionReceipt.create(
            source_key=self.source_key,
            adapter_key=self.adapter_key,
            adapter_version=self.adapter_version,
            acquired_at=request.acquired_at or self._clock(),
            request_payload=request.payload(),
            input_content=content,
            source_locator=str(file_path),
        )
        try:
            dataframe = pd.read_csv(StringIO(content))
        except pd.errors.EmptyDataError:
            return AcquisitionResult(
                receipt=receipt,
                issues=(AcquisitionIssue("invalid_format", "The file is empty."),),
            )
        except (ValueError, pd.errors.ParserError) as exc:
            return AcquisitionResult(
                receipt=receipt, issues=(AcquisitionIssue("invalid_format", str(exc)),)
            )
        papers = TabularImporter.dataframe_to_papers(
            dataframe, receipt, self.format_name
        )
        return AcquisitionResult(receipt=receipt, papers=tuple(papers))

    def import_file(self, path: str | Path) -> Result:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_path.suffix.lower() != ".csv":
            raise ValueError("Expected a CSV file")

        content = read_text_with_encoding_fallback(file_path)
        receipt = AcquisitionReceipt.create(
            source_key="csv",
            adapter_key="local-csv",
            adapter_version="1",
            acquired_at=datetime.now(UTC),
            request_payload={"location": str(file_path), "context": ""},
            input_content=content,
            source_locator=str(file_path),
        )
        dataframe = pd.read_csv(StringIO(content))
        papers = TabularImporter.dataframe_to_papers(dataframe, receipt, "CSV")

        return Result.ok(data=papers)
