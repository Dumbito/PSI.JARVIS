from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import MarkdownRenderer, ReportBuilder
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


def test_markdown_renderer_contains_report_structure():
    report = build_report()

    rendered = MarkdownRenderer().render(report)

    assert rendered.startswith("# PSI.JARVIS Screening Report")
    assert "## Statistics" in rendered
    assert "## Screening Metrics" in rendered
    assert "## Decision Distribution" in rendered
    assert "## Metadata Quality" in rendered
    assert "## Authors" in rendered
    assert "## Journals" in rendered
    assert "## Publication Year" in rendered
    assert "## Rules" in rendered
    assert "## Criteria" in rendered
    assert "## Exclusion Reasons" in rendered


def test_markdown_renderer_preserves_analysis_values():
    report = build_report()
    rendered = MarkdownRenderer().render(report)

    assert "- Total input: 2" in rendered
    assert "- Unique papers: 2" in rendered
    assert "| Included | 1 |" in rendered
    assert "| Excluded | 1 |" in rendered
    assert "| Alice | 1 |" in rendered
    assert "| Bob | 1 |" in rendered
    assert "| Journal A | 1 |" in rendered
    assert "| Journal B | 1 |" in rendered
    assert "| 2024 | 1 |" in rendered
    assert "| 2025 | 1 |" in rendered


def test_markdown_renderer_is_deterministic():
    report = build_report()

    renderer = MarkdownRenderer()
    assert renderer.render(report) == renderer.render(report)
    assert renderer.render(report).endswith("\n")
