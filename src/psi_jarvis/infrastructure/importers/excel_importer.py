from pathlib import Path

import pandas as pd

from psi_jarvis.core.result import Result
from psi_jarvis.infrastructure.importers.tabular import TabularImporter
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer


class ExcelImporter:
    def import_file(self, path: str | Path) -> Result:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Expected an Excel file")

        dataframe = pd.read_excel(file_path)
        papers = TabularImporter.dataframe_to_papers(dataframe)
        papers = [PaperNormalizer().normalize(paper) for paper in papers]

        return Result.ok(data=papers)
