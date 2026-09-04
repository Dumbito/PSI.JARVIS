from dataclasses import dataclass
from pathlib import Path

from psi_jarvis.application.reporting.json_renderer import JSONRenderer
from psi_jarvis.application.reporting.markdown_renderer import MarkdownRenderer
from psi_jarvis.domain.reporting import Report


@dataclass(frozen=True)
class ReportExporter:
    output_dir: Path
    json_renderer: JSONRenderer = JSONRenderer()
    markdown_renderer: MarkdownRenderer = MarkdownRenderer()

    def __post_init__(self) -> None:
        if not str(self.output_dir).strip():
            raise ValueError("Report output directory cannot be empty")

    def export_json(
        self,
        report: Report,
        filename: str = "report.json",
    ) -> Path:
        return self._export(
            self.json_renderer.render(report),
            filename,
        )

    def export_markdown(
        self,
        report: Report,
        filename: str = "report.md",
    ) -> Path:
        return self._export(
            self.markdown_renderer.render(report),
            filename,
        )

    def _export(self, content: str, filename: str) -> Path:
        if not filename.strip():
            raise ValueError("Report filename cannot be empty")

        path = self.output_dir / filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
