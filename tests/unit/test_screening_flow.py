from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.visualization import ScreeningFlowBuilder, SVGChartRenderer
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_screening_flow_uses_existing_pipeline_counts():
    result = PaperPipeline().process(
        (
            Paper(title="Intelligence study", abstract="Intelligence research."),
            Paper(title="Animal study", abstract="Animal research."),
        ),
        ScreeningCriteria(topic="intelligence"),
    )

    flow = ScreeningFlowBuilder().execute(result)

    assert flow.identified == result.total_input
    assert flow.duplicates_removed == result.duplicates_removed
    assert flow.screened == result.screened_papers
    assert flow.excluded == result.statistics.excluded_papers
    assert flow.included == result.statistics.included_papers


def test_screening_flow_is_deterministic():
    result = PaperPipeline().process(
        (Paper(title="Intelligence", abstract="Intelligence research."),),
        ScreeningCriteria(topic="intelligence"),
    )

    builder = ScreeningFlowBuilder()
    assert builder.execute(result) == builder.execute(result)


def test_screening_flow_renderer_returns_svg():
    result = PaperPipeline().process(
        (Paper(title="Intelligence", abstract="Intelligence research."),),
        ScreeningCriteria(topic="intelligence"),
    )
    flow = ScreeningFlowBuilder().execute(result)

    svg = SVGChartRenderer().render_screening_flow(flow)

    assert svg.startswith("<svg")
    assert "Screening Flow" in svg
    assert "Identified" in svg
    assert "Included" in svg
