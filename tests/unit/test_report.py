from dataclasses import replace

from psi_jarvis.domain.analysis.author_analysis import AuthorAnalysis
from psi_jarvis.domain.analysis.criteria_analysis import CriteriaAnalysis
from psi_jarvis.domain.analysis.decision_distribution import DecisionDistribution
from psi_jarvis.domain.analysis.deduplication_analysis import DeduplicationAnalysis
from psi_jarvis.domain.analysis.exclusion_reason_analysis import ExclusionReasonAnalysis
from psi_jarvis.domain.analysis.journal_analysis import JournalAnalysis
from psi_jarvis.domain.analysis.metadata_quality import MetadataQuality
from psi_jarvis.domain.analysis.publication_year_analysis import PublicationYearAnalysis
from psi_jarvis.domain.analysis.rule_analysis import RuleAnalysis
from psi_jarvis.domain.analysis.screening_metrics import ScreeningMetrics
from psi_jarvis.domain.analysis.statistics import StatisticalSummary
from psi_jarvis.domain.reporting import Report


def build_report() -> Report:
    return Report(
        title="Screening Report",
        statistics=StatisticalSummary(10, 8, 2, 8, 3, 5),
        screening_metrics=ScreeningMetrics(10, 8, 3, 5, 2, 4, 3),
        rule_analysis=RuleAnalysis(()),
        criteria_analysis=CriteriaAnalysis(()),
        decision_distribution=DecisionDistribution(8, 3, 5),
        exclusion_reason_analysis=ExclusionReasonAnalysis(()),
        metadata_quality=MetadataQuality(8, ()),
        deduplication_analysis=DeduplicationAnalysis(10, 8, 2),
        author_analysis=AuthorAnalysis(8, 0, 8, 0, ()),
        journal_analysis=JournalAnalysis(8, 0, 8, 0, ()),
        publication_year_analysis=PublicationYearAnalysis(8, 0, 8, None, None, ()),
    )


def test_report_stores_existing_analysis_results():
    report = build_report()

    assert report.title == "Screening Report"
    assert report.statistics.screened_papers == 8
    assert report.screening_metrics.included_papers == 3
    assert report.decision_distribution.excluded == 5
    assert report.deduplication_analysis.duplicate_papers == 2
    assert report.section_count == 11


def test_report_exposes_analysis_by_section_name():
    report = build_report()

    assert report.section("statistics") is report.statistics
    assert report.section("screening_metrics") is report.screening_metrics
    assert report.section("metadata_quality") is report.metadata_quality
    assert report.section("publication_year_analysis") is report.publication_year_analysis


def test_report_returns_none_for_unknown_section():
    report = build_report()

    assert report.section("missing") is None


def test_report_rejects_empty_title():
    report = build_report()

    try:
        replace(report, title="   ")
    except ValueError as exc:
        assert str(exc) == "Report title cannot be empty"
    else:
        raise AssertionError("Expected ValueError")
