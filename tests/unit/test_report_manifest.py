from pathlib import Path

from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import ReportPackageBuilder, ReportPackageExporter
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def build_package():
    result = PaperPipeline().process(
        (Paper(title="Intelligence study", abstract="Intelligence research.", publication_year=2025),),
        ScreeningCriteria(topic="intelligence"),
    )
    return ReportPackageBuilder().execute(result)


def test_report_package_manifest_is_deterministic(tmp_path: Path):
    package = build_package()
    ReportPackageExporter(tmp_path).export(package)
    first = (tmp_path / "report_manifest.json").read_text(encoding="utf-8")

    second_dir = tmp_path / "second"
    ReportPackageExporter(second_dir).export(package)
    second = (second_dir / "report_manifest.json").read_text(encoding="utf-8")

    assert first == second


def test_report_package_manifest_declares_expected_files(tmp_path: Path):
    package = build_package()
    ReportPackageExporter(tmp_path).export(package)
    manifest = (tmp_path / "report_manifest.json").read_text(encoding="utf-8")

    assert "\"format\": \"psi-jarvis-report-package\"" in manifest
    assert "\"version\": 1" in manifest
    assert "\"report.md\"" in manifest
    assert "\"report.json\"" in manifest
    assert "\"decision_distribution.svg\"" in manifest
    assert "\"publication_year.svg\"" in manifest
    assert "\"exclusion_reasons.svg\"" in manifest
    assert "\"screening_flow.svg\"" in manifest
    assert "\"criteria_analysis.svg\"" in manifest
