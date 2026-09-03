from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper


def test_pipeline_produces_screening_metrics():
    criteria = ScreeningCriteria(topic="cognition")
    papers = (
        Paper(title="Cognition study", abstract="cognition"),
        Paper(title="Animal study", abstract="animal"),
        Paper(title="Animal study", abstract="animal"),
    )

    result = PaperPipeline().process(papers, criteria)
    metrics = result.screening_metrics

    assert metrics.total_input == 3
    assert metrics.screened_papers == 2
    assert metrics.included_papers == 1
    assert metrics.excluded_papers == 1
    assert metrics.duplicates_removed == 1
    assert metrics.screening_completion_rate == 2 / 3
    assert metrics.screening_yield == 1 / 3
    assert metrics.exclusion_yield == 1 / 3
    assert metrics.total_matched_rules == sum(len(audit.matched_rule_ids) for audit in result.audits)
    assert metrics.total_failed_rules == sum(len(audit.failed_rule_ids) for audit in result.audits)
