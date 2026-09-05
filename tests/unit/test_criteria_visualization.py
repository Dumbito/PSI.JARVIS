from psi_jarvis.application.visualization import SVGChartRenderer
from psi_jarvis.domain.analysis import CriteriaAnalysis, CriterionStatistics


def test_render_criteria_analysis_is_deterministic():
    renderer = SVGChartRenderer()
    analysis = CriteriaAnalysis(
        criteria=(
            CriterionStatistics(criterion_id="criterion_a", matched=4, failed=2),
            CriterionStatistics(criterion_id="criterion_b", matched=1, failed=3),
        )
    )

    first = renderer.render_criteria_analysis(analysis)
    second = renderer.render_criteria_analysis(analysis)

    assert first == second
    assert first.startswith("<svg ")
    assert "Criteria Analysis" in first
    assert "criterion_a" in first
    assert "criterion_b" in first
    assert ">4<" in first
    assert ">2<" in first
    assert ">1<" in first
    assert ">3<" in first


def test_render_criteria_analysis_escapes_labels():
    renderer = SVGChartRenderer()
    analysis = CriteriaAnalysis(
        criteria=(
            CriterionStatistics(criterion_id="criterion <A>", matched=2, failed=1),
        )
    )

    result = renderer.render_criteria_analysis(analysis)

    assert "criterion &lt;A&gt;" in result


def test_render_criteria_analysis_handles_empty_analysis():
    renderer = SVGChartRenderer()
    analysis = CriteriaAnalysis(criteria=())

    result = renderer.render_criteria_analysis(analysis)

    assert result.startswith("<svg ")
    assert "Criteria Analysis" in result
