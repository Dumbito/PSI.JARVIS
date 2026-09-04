import json

from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import JSONRenderer, ReportBuilder
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


def test_json_renderer_returns_valid_json():
    report = build_report()

    rendered = JSONRenderer().render(report)
    payload = json.loads(rendered)

    assert payload["title"] == "PSI.JARVIS Screening Report"
    assert payload["statistics"]["total_input"] == 2
    assert payload["statistics"]["screened_papers"] == 2
    assert payload["decision_distribution"]["included"] == 1
    assert payload["decision_distribution"]["excluded"] == 1


def test_json_renderer_preserves_analysis_details():
    report = build_report()

    payload = json.loads(JSONRenderer().render(report))

    assert payload["authors"]["unique_authors"] == 2
    assert payload["journals"]["unique_journals"] == 2
    assert payload["publication_year"]["year_min"] == 2024
    assert payload["publication_year"]["year_max"] == 2025
    assert len(payload["rules"]) == report.rule_analysis.total_rules
    assert len(payload["criteria"]) == report.criteria_analysis.total_criteria


def test_json_renderer_is_deterministic():
    report = build_report()

    renderer = JSONRenderer()
    assert renderer.render(report) == renderer.render(report)
