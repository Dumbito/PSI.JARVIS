from pathlib import Path

from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import ReportBuilder, ReportExporter
from psi_jarvis.application.reporting.json_renderer import JSONRenderer
from psi_jarvis.application.reporting.markdown_renderer import MarkdownRenderer
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def build_report():
    result = PaperPipeline().process(
        (
            Paper(
                title="Memory and intelligence",
                abstract="Study of memory and intelligence.",
                authors=("Alice",),
                journal="Journal A",
                publication_year=2025,
                doi="10.1000/example",
            ),
            Paper(
                title="Animal intelligence",
                abstract="Animal cognition study.",
                authors=("Bob",),
                journal="Journal B",
                publication_year=2024,
                doi="10.1000/example-2",
            ),
        ),
        ScreeningCriteria(
            topic="intelligence",
            inclusion=("memory",),
            exclusion=("animal",),
        ),
    )
    return ReportBuilder().execute(result)


def test_export_json_creates_directory_and_matches_renderer(tmp_path: Path):
    report = build_report()
    output_dir = tmp_path / "nested" / "reports"

    exported = ReportExporter(output_dir).export_json(report)

    assert exported == output_dir / "report.json"
    assert exported.exists()
    assert exported.read_text(encoding="utf-8") == JSONRenderer().render(report)


def test_export_markdown_creates_file_and_matches_renderer(tmp_path: Path):
    report = build_report()
    output_dir = tmp_path / "reports"

    exported = ReportExporter(output_dir).export_markdown(report)

    assert exported == output_dir / "report.md"
    assert exported.exists()
    assert exported.read_text(encoding="utf-8") == MarkdownRenderer().render(report)


def test_export_supports_custom_filenames(tmp_path: Path):
    report = build_report()
    exporter = ReportExporter(tmp_path)

    json_path = exporter.export_json(report, "screening-results.json")
    markdown_path = exporter.export_markdown(report, "screening-results.md")

    assert json_path.name == "screening-results.json"
    assert markdown_path.name == "screening-results.md"


def test_export_rejects_empty_filename(tmp_path: Path):
    report = build_report()
    exporter = ReportExporter(tmp_path)

    try:
        exporter.export_json(report, "   ")
    except ValueError as exc:
        assert str(exc) == "Report filename cannot be empty"
    else:
        raise AssertionError("Expected ValueError")

def test_exporter_accepts_custom_renderers(tmp_path: Path):
    report = build_report()

    class StubJSONRenderer:
        def render(self, report):
            return "custom-json"

    class StubMarkdownRenderer:
        def render(self, report):
            return "custom-markdown"

    exporter = ReportExporter(
        tmp_path,
        json_renderer=StubJSONRenderer(),
        markdown_renderer=StubMarkdownRenderer(),
    )

    json_path = exporter.export_json(report, "custom.json")
    markdown_path = exporter.export_markdown(report, "custom.md")

    assert json_path.read_text(encoding="utf-8") == "custom-json"
    assert markdown_path.read_text(encoding="utf-8") == "custom-markdown"
