from pathlib import Path

from psi_jarvis.application.pipeline.pipeline import PaperPipeline, PipelineResult
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
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

        importer = self._select_importer(path)
        import_result = importer.import_file(path)

        if not import_result.success:
            raise ValueError(
                import_result.message or "Paper import failed"
            )

        papers = import_result.data or []

        return self.pipeline.process(papers, criteria)

    @staticmethod
    def _select_importer(path: Path):
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return CSVImporter()

        if suffix in {".xlsx", ".xls"}:
            return ExcelImporter()

        raise ValueError(f"Unsupported file format: {suffix}")
