from pathlib import Path

from psi_jarvis.application.acquisition import AcquisitionRequest, AcquisitionService
from psi_jarvis.application.pipeline.pipeline import PaperPipeline, PipelineResult
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.infrastructure.acquisition import RISImporter
from psi_jarvis.infrastructure.importers.csv_importer import CSVImporter
from psi_jarvis.infrastructure.importers.excel_importer import ExcelImporter


class ImportAndScreenService:
    """Coordina la importación de papers y su procesamiento científico."""

    def __init__(self, pipeline: PaperPipeline | None = None) -> None:
        self.pipeline = pipeline or PaperPipeline()

    def execute(
        self,
        file_path: str | Path,
        criteria: ScreeningCriteria,
    ) -> PipelineResult:
        path = Path(file_path)
        acquisition = AcquisitionService(self._select_acquisition_port(path)).execute(
            AcquisitionRequest(location=str(path))
        )
        if not acquisition.success:
            message = (
                acquisition.issues[0].message
                if acquisition.issues
                else "Paper acquisition failed"
            )
            raise ValueError(message)
        return self.pipeline.process(acquisition.papers, criteria)

    @staticmethod
    def _select_acquisition_port(path: Path):
        suffix = path.suffix.lower()

        if suffix == ".ris":
            return RISImporter()

        if suffix == ".csv":
            return CSVImporter()

        if suffix in {".xlsx", ".xls"}:
            return ExcelImporter()

        raise ValueError(f"Unsupported file format: {suffix}")
