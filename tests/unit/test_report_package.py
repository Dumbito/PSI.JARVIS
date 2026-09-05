from pathlib import Path

from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import ReportPackageBuilder, ReportPackageExporter
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_report_package_builder_is_deterministic():
    result = PaperPipeline().process(
        (
            Paper(title="Intelligence study", abstract="Intelligence research.", publication_year=2025),
            Paper(title="Animal study", abstract="Animal research.", publication_year=2024),
        ),
        ScreeningCriteria(topic="intelligence"),
    )
    builder = ReportPackageBuilder()
    first = builder.execute(result)
    second = builder.execute(result)
    assert first == second


def test_report_package_contains_report_and_visualizations():
    result = PaperPipeline().process(
        (Paper(title="Intelligence study", abstract="Intelligence research.", publication_year=2025),),
        ScreeningCriteria(topic="intelligence"),
    )
    package = ReportPackageBuilder().execute(result)
    assert package.report_markdown.startswith("# PSI.JARVIS Screening Report")
    assert package.report_json.startswith("{")
    assert package.decision_distribution.startswith("<svg")
    assert package.publication_year.startswith("<svg")
    assert package.exclusion_reasons.startswith("<svg")
    assert package.screening_flow.startswith("<svg")
    assert package.criteria_analysis.startswith("<svg")


def test_report_package_export_writes_expected_files(tmp_path: Path):
    result = PaperPipeline().process(
        (Paper(title="Intelligence study", abstract="Intelligence research.", publication_year=2025),),
        ScreeningCriteria(topic="intelligence"),
    )
    package = ReportPackageBuilder().execute(result)
    paths = ReportPackageExporter(tmp_path).export(package)
    assert tuple(path.name for path in paths) == (
        "report.md",
        "report.json",
        "decision_distribution.svg",
        "publication_year.svg",
        "exclusion_reasons.svg",
        "screening_flow.svg",
            "criteria_analysis.svg",
            "report_manifest.json",
    )
    assert all(path.exists() for path in paths)


def test_report_package_export_rejects_empty_content(tmp_path: Path):
    result = PaperPipeline().process(
        (Paper(title="Intelligence study", abstract="Intelligence research."),),
        ScreeningCriteria(topic="intelligence"),
    )
    package = ReportPackageBuilder().execute(result)
    broken = type(package)(
        report_markdown="",
        report_json=package.report_json,
        decision_distribution=package.decision_distribution,
        publication_year=package.publication_year,
        exclusion_reasons=package.exclusion_reasons,
        screening_flow=package.screening_flow,
                criteria_analysis=package.criteria_analysis,
    )
    try:
        ReportPackageExporter(tmp_path).export(broken)
    except ValueError as exc:
        assert "report.md" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
