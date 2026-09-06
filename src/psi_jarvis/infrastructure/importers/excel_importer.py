from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from psi_jarvis.core.result import Result
from psi_jarvis.domain.bibliography.provenance import AcquisitionReceipt
from psi_jarvis.infrastructure.importers.tabular import TabularImporter


class ExcelImporter:
    def import_file(self, path: str | Path) -> Result:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Expected an Excel file")

        content = file_path.read_bytes().hex()
        receipt = AcquisitionReceipt.create(
            source_key="excel",
            adapter_key="local-excel",
            adapter_version="1",
            acquired_at=datetime.now(timezone.utc),
            request_payload={"location": str(file_path), "context": ""},
            input_content=content,
            source_locator=str(file_path),
        )
        dataframe = pd.read_excel(file_path)
        papers = TabularImporter.dataframe_to_papers(dataframe, receipt, "Excel")

        return Result.ok(data=papers)
