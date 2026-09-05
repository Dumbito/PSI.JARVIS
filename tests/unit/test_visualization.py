from pathlib import Path

from psi_jarvis.application.visualization import SVGChartRenderer
from psi_jarvis.domain.analysis import (
    DecisionDistribution,
    ExclusionReasonAnalysis,
    ExclusionReasonStatistics,
    PublicationYearAnalysis,
)


def test_render_decision_distribution_is_deterministic():
    renderer = SVGChartRenderer()
    analysis = DecisionDistribution(
        total=10,
        included=4,
        excluded=6,
    )

    first = renderer.render_decision_distribution(analysis)
    second = renderer.render_decision_distribution(analysis)

    assert first == second
    assert first.startswith("<svg ")
    assert "Decision Distribution" in first
    assert ">4<" in first
    assert ">6<" in first


def test_render_publication_year_uses_existing_distribution():
    renderer = SVGChartRenderer()
    analysis = PublicationYearAnalysis(
        total_papers=3,
        papers_with_year=3,
        papers_without_year=0,
        year_min=2020,
        year_max=2022,
        by_year=(
            (2020, 1),
            (2021, 2),
        ),
    )

    result = renderer.render_publication_year(analysis)

    assert "Publication Year Distribution" in result
    assert ">2020<" in result
    assert ">2021<" in result


def test_render_exclusion_reasons_escapes_labels():
    renderer = SVGChartRenderer()
    analysis = ExclusionReasonAnalysis(
        reasons=(
            ExclusionReasonStatistics(
                reason="topic < mismatch",
                count=2,
                total_excluded=2,
            ),
        )
    )

    result = renderer.render_exclusion_reasons(analysis)

    assert "topic &lt; mismatch" in result
    assert ">2<" in result


def test_renderer_rejects_invalid_dimensions():
    try:
        SVGChartRenderer(width=0)
    except ValueError as error:
        assert str(error) == "SVG dimensions must be positive"
    else:
        raise AssertionError("Expected ValueError")

from psi_jarvis.application.visualization import VisualizationExporter


def test_visualization_exporter_creates_directory_and_writes_content(
    tmp_path: Path,
):
    output_dir = tmp_path / "nested" / "visualizations"
    exporter = VisualizationExporter(output_dir)

    path = exporter.export("<svg>test</svg>")

    assert path == output_dir / "visualization.svg"
    assert path.read_text(encoding="utf-8") == "<svg>test</svg>"


def test_visualization_exporter_accepts_custom_filename(
    tmp_path: Path,
):
    exporter = VisualizationExporter(tmp_path)

    path = exporter.export(
        "<svg>custom</svg>",
        "decision_distribution.svg",
    )

    assert path.name == "decision_distribution.svg"
    assert path.read_text(encoding="utf-8") == "<svg>custom</svg>"


def test_visualization_exporter_rejects_blank_filename(
    tmp_path: Path,
):
    exporter = VisualizationExporter(tmp_path)

    try:
        exporter.export("<svg>test</svg>", "   ")
    except ValueError as error:
        assert str(error) == (
            "Visualization filename cannot be empty"
        )
    else:
        raise AssertionError("Expected ValueError")


def test_visualization_exporter_rejects_blank_content(
    tmp_path: Path,
):
    exporter = VisualizationExporter(tmp_path)

    try:
        exporter.export("   ")
    except ValueError as error:
        assert str(error) == (
            "Visualization content cannot be empty"
        )
    else:
        raise AssertionError("Expected ValueError")