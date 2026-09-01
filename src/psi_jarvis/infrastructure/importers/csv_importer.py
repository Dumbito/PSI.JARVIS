from pathlib import Path

import pandas as pd

from psi_jarvis.core.result import Result
from psi_jarvis.infrastructure.importers.tabular import TabularImporter
from psi_jarvis.domain.normalization.normalizer import PaperNormalizer


class CSVImporter:
    def import_file(self, path: str | Path) -> Result:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if file_path.suffix.lower() != ".csv":
            raise ValueError("Expected a CSV file")

        dataframe = pd.read_csv(file_path)
        papers = TabularImporter.dataframe_to_papers(dataframe)
        papers = [PaperNormalizer().normalize(paper) for paper in papers]

        return Result.ok(data=papers)
