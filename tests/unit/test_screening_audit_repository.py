from uuid import uuid4

from psi_jarvis.domain.screening.audit import ScreeningAudit
from psi_jarvis.infrastructure.screening_audit_repository import (
    InMemoryScreeningAuditRepository,
)


def make_audit(run_id=None):
    return ScreeningAudit(
        paper_id=uuid4(),
        included=False,
        reason="Inclusion rule not matched: randomized",
        run_id=run_id,
        matched_rules=("adult",),
        failed_rules=("randomized",),
        matched_rule_ids=("text:adult",),
        failed_rule_ids=("text:randomized",),
        criteria_version="abc123",
    )


def test_save_and_get_audit():
    repository = InMemoryScreeningAuditRepository()
    run_id = uuid4()
    audit = make_audit(run_id)

    repository.save(audit)

    assert repository.get(audit.paper_id, run_id) == audit


def test_get_unknown_audit_returns_none():
    repository = InMemoryScreeningAuditRepository()

    assert repository.get(uuid4()) is None


def test_list_all_returns_saved_audits():
    repository = InMemoryScreeningAuditRepository()
    first = make_audit(uuid4())
    second = make_audit(uuid4())

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == (first, second)


def test_save_replaces_same_audit_identity():
    repository = InMemoryScreeningAuditRepository()
    run_id = uuid4()
    first = make_audit(run_id)
    replacement = ScreeningAudit(
        paper_id=first.paper_id,
        included=True,
        reason="Paper matches screening criteria",
        run_id=run_id,
        criteria_version="abc123",
    )

    repository.save(first)
    repository.save(replacement)

    assert repository.get(first.paper_id, run_id) == replacement
    assert len(repository.list_all()) == 1


def test_same_paper_can_have_audits_in_different_runs():
    repository = InMemoryScreeningAuditRepository()
    paper_id = uuid4()
    first_run = uuid4()
    second_run = uuid4()

    first = ScreeningAudit(
        paper_id=paper_id,
        included=True,
        reason="Included",
        run_id=first_run,
    )
    second = ScreeningAudit(
        paper_id=paper_id,
        included=False,
        reason="Excluded",
        run_id=second_run,
    )

    repository.save(first)
    repository.save(second)

    assert repository.get(paper_id, first_run) == first
    assert repository.get(paper_id, second_run) == second
    assert len(repository.list_all()) == 2


def test_audit_without_run_id_is_persisted():
    repository = InMemoryScreeningAuditRepository()
    audit = make_audit()

    repository.save(audit)

    assert repository.get(audit.paper_id) == audit
