from dataclasses import dataclass, field

from psi_jarvis.application.pipeline.pipeline import PipelineResult
from psi_jarvis.application.visualization.chart import SVGChartRenderer
from psi_jarvis.application.visualization.screening_flow import (
    ScreeningFlowBuilder,
)


@dataclass(frozen=True)
class VisualizationBundle:
    decision_distribution: str
    publication_year: str
    exclusion_reasons: str
    screening_flow: str
    criteria_analysis: str


@dataclass(frozen=True)
class VisualizationBuilder:
    renderer: SVGChartRenderer
    screening_flow_builder: ScreeningFlowBuilder = field(
        default_factory=ScreeningFlowBuilder
    )

    def execute(self, result: PipelineResult) -> VisualizationBundle:
        flow = self.screening_flow_builder.execute(result)
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
            screening_flow=self.renderer.render_screening_flow(flow),
            criteria_analysis=self.renderer.render_criteria_analysis(
                result.criteria_analysis
            ),
        )
