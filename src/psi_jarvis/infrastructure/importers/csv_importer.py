from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from psi_jarvis.core.result import Result
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.importers.tabular import TabularImporter


class CSVImporter:
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
