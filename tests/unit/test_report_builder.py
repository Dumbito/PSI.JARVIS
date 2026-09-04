from psi_jarvis.application.pipeline import PaperPipeline
from psi_jarvis.application.reporting import ReportBuilder
from psi_jarvis.domain.criteria import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_report_builder_maps_pipeline_result_without_recomputing():
    pipeline = PaperPipeline()
    criteria = ScreeningCriteria(
        topic="intelligence",
        inclusion=("memory",),
        exclusion=("animal",),
    )
    papers = (
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
    )

    pipeline_result = pipeline.process(papers, criteria)
    report = ReportBuilder().execute(pipeline_result)

    assert report.title == "PSI.JARVIS Screening Report"
    assert report.statistics is pipeline_result.statistics
    assert report.screening_metrics is pipeline_result.screening_metrics
    assert report.rule_analysis is pipeline_result.rule_analysis
    assert report.criteria_analysis is pipeline_result.criteria_analysis
    assert report.decision_distribution is pipeline_result.decision_distribution
    assert report.exclusion_reason_analysis is pipeline_result.exclusion_reason_analysis
    assert report.metadata_quality is pipeline_result.metadata_quality
    assert report.deduplication_analysis is pipeline_result.deduplication_analysis
    assert report.author_analysis is pipeline_result.author_analysis
    assert report.journal_analysis is pipeline_result.journal_analysis
    assert report.publication_year_analysis is pipeline_result.publication_year_analysis


def test_report_builder_allows_custom_title():
    pipeline = PaperPipeline()
    criteria = ScreeningCriteria(topic="intelligence")

    result = pipeline.process(
        (Paper(title="Intelligence study", abstract="Intelligence research."),),
        criteria,
    )

    report = ReportBuilder(title="Custom Report").execute(result)

    assert report.title == "Custom Report"
