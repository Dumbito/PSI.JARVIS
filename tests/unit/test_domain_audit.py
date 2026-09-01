from uuid import uuid4

from psi_jarvis.domain.screening.audit import ScreeningAudit


def test_screening_audit_exists():
    audit = ScreeningAudit(
        paper_id=uuid4(),
        included=True,
        reason="Paper matches screening criteria",
        matched_rules=("memory",),
        failed_rules=(),
    )

    assert audit.included is True
    assert audit.reason == "Paper matches screening criteria"
    assert audit.matched_rules == ("memory",)
    assert audit.failed_rules == ()


def test_screening_audit_is_immutable():
    audit = ScreeningAudit(
        paper_id=uuid4(),
        included=True,
        reason="Included",
    )

    try:
        audit.included = False
        assert False, "ScreeningAudit should be immutable"
    except AttributeError:
        pass


def test_screening_audit_can_be_created_from_screening_result():
    from psi_jarvis.domain.paper import Paper
    from psi_jarvis.domain.criteria.screening import ScreeningCriteria
    from psi_jarvis.domain.screening.engine import ScreeningEngine

    paper = Paper(title="Memory and Intelligence")
    criteria = ScreeningCriteria(topic="memory")
    result = ScreeningEngine(criteria).evaluate(paper)

    audit = ScreeningAudit(
        paper_id=result.paper_id,
        included=result.included,
        reason=result.reason,
        matched_rules=result.matched_rules,
        failed_rules=result.failed_rules,
    )

    assert audit.paper_id == result.paper_id
    assert audit.included == result.included
    assert audit.reason == result.reason
    assert audit.matched_rules == result.matched_rules
    assert audit.failed_rules == result.failed_rules


def test_screening_audit_from_result_factory():
    from psi_jarvis.domain.paper import Paper
    from psi_jarvis.domain.criteria.screening import ScreeningCriteria
    from psi_jarvis.domain.screening.engine import ScreeningEngine

    paper = Paper(title="Memory and Intelligence")
    result = ScreeningEngine(ScreeningCriteria(topic="memory")).evaluate(paper)

    audit = ScreeningAudit.from_result(result)

    assert audit.paper_id == result.paper_id
    assert audit.included == result.included
    assert audit.reason == result.reason
    assert audit.matched_rules == result.matched_rules
    assert audit.failed_rules == result.failed_rules


def test_screening_audit_from_result_factory():
    from psi_jarvis.domain.paper import Paper
    from psi_jarvis.domain.criteria.screening import ScreeningCriteria
    from psi_jarvis.domain.screening.engine import ScreeningEngine

    paper = Paper(title="Memory and Intelligence")
    result = ScreeningEngine(ScreeningCriteria(topic="memory")).evaluate(paper)

    audit = ScreeningAudit.from_result(result)

    assert audit.paper_id == result.paper_id
    assert audit.included == result.included
    assert audit.reason == result.reason
    assert audit.matched_rules == result.matched_rules
    assert audit.failed_rules == result.failed_rules


def test_screening_audit_report_exists():
    from psi_jarvis.domain.screening.audit_report import ScreeningAuditReport

    report = ScreeningAuditReport(
        total_evaluated=10,
        included=4,
        excluded=6,
    )

    assert report.total_evaluated == 10
    assert report.included == 4
    assert report.excluded == 6
    assert report.inclusion_rate == 0.4
    assert report.exclusion_rate == 0.6


def test_screening_audit_report_counts_reasons():
    from psi_jarvis.domain.screening.audit_report import ScreeningAuditReport

    report = ScreeningAuditReport(
        total_evaluated=6,
        included=2,
        excluded=4,
        exclusion_reasons=(
            "Topic not found: memory",
            "Topic not found: memory",
            "Exclusion rule matched: animal",
            "Exclusion rule matched: animal",
        ),
    )

    assert report.exclusion_reason_counts == {
        "Topic not found: memory": 2,
        "Exclusion rule matched: animal": 2,
    }
