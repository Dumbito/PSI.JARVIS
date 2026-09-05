from dataclasses import dataclass
from pathlib import Path

from psi_jarvis.application.reporting import JSONRenderer, MarkdownRenderer, ReportBuilder
from psi_jarvis.application.visualization import SVGChartRenderer, VisualizationBuilder
from psi_jarvis.application.pipeline.pipeline import PipelineResult


@dataclass(frozen=True)
class ReproducibleReportPackage:
    report_markdown: str
    report_json: str
    decision_distribution: str
    publication_year: str
    exclusion_reasons: str
    screening_flow: str


@dataclass(frozen=True)
class ReportPackageBuilder:
    report_builder: ReportBuilder = ReportBuilder()
    markdown_renderer: MarkdownRenderer = MarkdownRenderer()
    json_renderer: JSONRenderer = JSONRenderer()
    visualization_builder: VisualizationBuilder = VisualizationBuilder(SVGChartRenderer())

    def execute(self, result: PipelineResult) -> ReproducibleReportPackage:
        report = self.report_builder.execute(result)
        visualizations = self.visualization_builder.execute(result)
        return ReproducibleReportPackage(
            report_markdown=self.markdown_renderer.render(report),
            report_json=self.json_renderer.render(report),
            decision_distribution=visualizations.decision_distribution,
            publication_year=visualizations.publication_year,
            exclusion_reasons=visualizations.exclusion_reasons,
            screening_flow=visualizations.screening_flow,
        )


@dataclass(frozen=True)
class ReportPackageExporter:
    output_dir: Path

    def __post_init__(self) -> None:
        if not str(self.output_dir).strip():
            raise ValueError("Report package output directory cannot be empty")

    def export(self, package: ReproducibleReportPackage) -> tuple[Path, ...]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        files = (
            ("report.md", package.report_markdown),
            ("report.json", package.report_json),
            ("decision_distribution.svg", package.decision_distribution),
            ("publication_year.svg", package.publication_year),
            ("exclusion_reasons.svg", package.exclusion_reasons),
            ("screening_flow.svg", package.screening_flow),
        )
        paths = tuple(self.output_dir / filename for filename, _ in files)
        for path, (_, content) in zip(paths, files):
            if not content.strip():
                raise ValueError(f"Report package content cannot be empty: {path.name}")
            path.write_text(content, encoding="utf-8")
        return paths
