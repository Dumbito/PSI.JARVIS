from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from psi_jarvis.application.acquisition.contracts import AcquisitionIssue, AcquisitionRequest, AcquisitionResult
from psi_jarvis.core.result import Result
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.importers.tabular import TabularImporter


class CSVImporter:
    source_key = "csv"
    adapter_key = "local-csv"
    adapter_version = "1"
    format_name = "CSV"

    def __init__(self, clock=None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def acquire(self, request: AcquisitionRequest) -> AcquisitionResult:
        file_path = Path(request.location)
        if not file_path.exists():
            return AcquisitionResult(receipt=None, issues=(AcquisitionIssue("source_unavailable", f"CSV file not found: {file_path}"),))
        if file_path.suffix.lower() != ".csv":
            return AcquisitionResult(receipt=None, issues=(AcquisitionIssue("invalid_format", "Expected a CSV file"),))
        content = file_path.read_text(encoding="utf-8")
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
            dataframe = pd.read_csv(file_path)
        except (ValueError, pd.errors.ParserError) as exc:
            return AcquisitionResult(receipt=receipt, issues=(AcquisitionIssue("invalid_format", str(exc)),))
        papers = TabularImporter.dataframe_to_papers(dataframe, receipt, self.format_name)
        return AcquisitionResult(receipt=receipt, papers=tuple(papers))

    def import_file(self, path: str | Path) -> Result:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_path.suffix.lower() != ".csv":
            raise ValueError("Expected a CSV file")

        content = file_path.read_text(encoding="utf-8")
        receipt = AcquisitionReceipt.create(
            source_key="csv",
            adapter_key="local-csv",
            adapter_version="1",
            acquired_at=datetime.now(timezone.utc),
            request_payload={"location": str(file_path), "context": ""},
            input_content=content,
            source_locator=str(file_path),
        )
        dataframe = pd.read_csv(file_path)
        papers = TabularImporter.dataframe_to_papers(dataframe, receipt, "CSV")

        return Result.ok(data=papers)
