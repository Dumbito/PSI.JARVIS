from dataclasses import dataclass

from psi_jarvis.application.pipeline.pipeline import PipelineResult
from psi_jarvis.application.visualization.chart import SVGChartRenderer


@dataclass(frozen=True)
class VisualizationBundle:
    decision_distribution: str
    publication_year: str
    exclusion_reasons: str


@dataclass(frozen=True)
class VisualizationBuilder:
    renderer: SVGChartRenderer

    def execute(self, result: PipelineResult) -> VisualizationBundle:
        return VisualizationBundle(
            decision_distribution=self.renderer.render_decision_distribution(
                result.decision_distribution
            ),
            publication_year=self.renderer.render_publication_year(
                result.publication_year_analysis
            ),
            exclusion_reasons=self.renderer.render_exclusion_reasons(
                result.exclusion_reason_analysis
            ),
        )
