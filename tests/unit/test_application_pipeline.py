from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.paper import Paper
from psi_jarvis.domain.criteria.screening import ScreeningCriteria


def test_pipeline_exists():
    assert PaperPipeline() is not None


def test_pipeline_processes_papers():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Unrelated Topic", doi="10.1234/b"),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert result.total_input == 2
    assert result.unique_papers == 2
    assert result.screened_papers == 2


def test_pipeline_normalizes_and_deduplicates():
    papers = [
        Paper(
            title="  Memory   and   Intelligence  ",
            doi="https://doi.org/10.1234/ABC",
        ),
        Paper(
            title="Memory and Intelligence",
            doi="10.1234/abc",
        ),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert result.total_input == 2
    assert result.unique_papers == 1
    assert result.duplicates_removed == 1


def test_pipeline_returns_screening_results():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Unrelated Topic", doi="10.1234/b"),
    ]

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process(papers, criteria)

    assert len(result.screening_results) == 2
    assert result.screening_results[0].included is True
    assert result.screening_results[1].included is False


def test_pipeline_preserves_processing_order():
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Brain Study", doi="10.1234/b"),
        Paper(title="Cognition Study", doi="10.1234/c"),
    ]

    criteria = ScreeningCriteria(topic="study")

    result = PaperPipeline().process(papers, criteria)

    assert [paper.title for paper in result.papers] == [
        "Memory Study",
        "Brain Study",
        "Cognition Study",
    ]


def test_pipeline_returns_screening_audits():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Unrelated Topic", doi="10.1234/b"),
    ]

    criteria = ScreeningCriteria(topic="memory")
    result = PaperPipeline().process(papers, criteria)

    assert len(result.audits) == 2
    assert result.audits[0].paper_id == result.screening_results[0].paper_id
    assert result.audits[0].included is True
    assert result.audits[1].included is False


def test_pipeline_returns_screening_audit_report():
    papers = [
        Paper(title="Memory and Intelligence", doi="10.1234/a"),
        Paper(title="Memory Research", doi="10.1234/b"),
        Paper(title="Unrelated Topic", doi="10.1234/c"),
    ]

    criteria = ScreeningCriteria(topic="memory")
    result = PaperPipeline().process(papers, criteria)

    assert result.audit_report.total_evaluated == 3
    assert result.audit_report.included == 2
    assert result.audit_report.excluded == 1
    assert result.audit_report.inclusion_rate == 2 / 3
    assert result.audit_report.exclusion_rate == 1 / 3


def test_pipeline_reports_exclusion_reasons():
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Brain Study", doi="10.1234/b"),
        Paper(title="Memory Animal Study", doi="10.1234/c"),
    ]

    criteria = ScreeningCriteria(
        topic="memory",
        exclusion=("animal",),
    )

    result = PaperPipeline().process(papers, criteria)

    assert result.audit_report.exclusion_reason_counts == {
        "Topic not found: memory": 1,
        "Exclusion rule matched: animal": 1,
    }



def test_pipeline_reports_failed_rule_counts():
    papers = [
        Paper(
            title="Memory Animal Clinical Study",
            doi="10.1234/a",
        ),
        Paper(
            title="Memory Animal Study",
            doi="10.1234/b",
        ),
        Paper(
            title="Memory Human Study",
            doi="10.1234/c",
        ),
    ]

    criteria = ScreeningCriteria(
        topic="memory",
        exclusion=("animal", "clinical"),
    )

    result = PaperPipeline().process(papers, criteria)

    assert result.audit_report.failed_rule_counts == {
        "animal": 2,
        "clinical": 1,
    }

def test_pipeline_creates_screening_run():
    criteria = ScreeningCriteria(
        topic="memory",
        inclusion=("adults",),
    )
    papers = [
        Paper(
            title="Memory in adults",
            authors=("Author",),
            abstract="A study about memory in adults.",
        )
    ]

    result = PaperPipeline().process(papers, criteria)

    assert result.run.criteria_version == result.audit_report.criteria_version
    assert result.run.total_input == result.total_input
    assert result.run.unique_papers == result.unique_papers
    assert result.run.duplicates_removed == result.duplicates_removed
    assert result.run.screened_papers == result.screened_papers
    assert result.run.run_id is not None

def test_pipeline_creates_run_for_empty_input():
    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process([], criteria)

    expected_version = ScreeningCriteriaVersion.from_criteria(criteria).value

    assert result.run.criteria_version == expected_version
    assert result.run.total_input == 0
    assert result.run.unique_papers == 0
    assert result.run.duplicates_removed == 0
    assert result.run.screened_papers == 0
    assert result.run.run_id is not None


def test_pipeline_empty_input_has_zero_audit_report_counts():
    criteria = ScreeningCriteria(topic="memory")

    result = PaperPipeline().process([], criteria)

    assert result.audit_report.total_evaluated == 0
    assert result.audit_report.included == 0
    assert result.audit_report.excluded == 0
    assert result.audit_report.criteria_version == ""

def test_pipeline_persists_screening_run():
    from psi_jarvis.infrastructure.screening_run_repository import InMemoryScreeningRunRepository

    repository = InMemoryScreeningRunRepository()
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline(run_repository=repository).process(papers, criteria)

    assert repository.get(result.run.run_id) == result.run
    assert repository.list_all() == (result.run,)

def test_pipeline_persists_screening_run_in_sqlite(tmp_path):
    from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository

    repository = SQLiteScreeningRunRepository(str(tmp_path / "screening_runs.db"))
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline(run_repository=repository).process(papers, criteria)

    reopened = SQLiteScreeningRunRepository(str(tmp_path / "screening_runs.db"))

    assert reopened.get(result.run.run_id) == result.run

def test_pipeline_links_screening_results_to_run():
    criteria = ScreeningCriteria(topic="memory")
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Memory Research", doi="10.1234/b"),
    ]

    result = PaperPipeline().process(papers, criteria)

    assert all(screening_result.run_id == result.run.run_id for screening_result in result.screening_results)


def test_pipeline_results_preserve_criteria_version():
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline().process(papers, criteria)

    assert all(
        screening_result.criteria_version == result.run.criteria_version
        for screening_result in result.screening_results
    )

def test_pipeline_links_audits_to_run():
    criteria = ScreeningCriteria(topic="memory")
    papers = [
        Paper(title="Memory Study", doi="10.1234/a"),
        Paper(title="Memory Research", doi="10.1234/b"),
    ]

    result = PaperPipeline().process(papers, criteria)

    assert all(audit.run_id == result.run.run_id for audit in result.audits)


def test_pipeline_preserves_run_id_across_results_and_audits():
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline().process(papers, criteria)

    assert result.screening_results[0].run_id == result.run.run_id
    assert result.audits[0].run_id == result.run.run_id
    assert result.audits[0].criteria_version == result.run.criteria_version

def test_pipeline_persists_results_with_sqlite_repository(tmp_path):
    from psi_jarvis.infrastructure.sqlite_screening_result_repository import (
        SQLiteScreeningResultRepository,
    )

    database_path = tmp_path / "screening.db"
    repository = SQLiteScreeningResultRepository(str(database_path))
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline(result_repository=repository).process(papers, criteria)

    stored = repository.get(result.papers[0].id, result.run.run_id)

    assert stored is not None
    assert stored == result.screening_results[0]

def test_pipeline_persists_audits_with_sqlite_repository(tmp_path):
    from psi_jarvis.infrastructure.sqlite_screening_audit_repository import (
        SQLiteScreeningAuditRepository,
    )

    database_path = tmp_path / "screening.db"
    repository = SQLiteScreeningAuditRepository(str(database_path))
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/a")]

    result = PaperPipeline(audit_repository=repository).process(papers, criteria)

    stored = repository.get(result.papers[0].id, result.run.run_id)

    assert stored is not None
    assert stored == result.audits[0]


def test_pipeline_persists_complete_screening_execution():
    from psi_jarvis.infrastructure.screening_execution_repository import InMemoryScreeningExecutionRepository

    repository = InMemoryScreeningExecutionRepository()
    criteria = ScreeningCriteria(topic="memory")
    papers = [Paper(title="Memory Study", doi="10.1234/execution")]

    result = PaperPipeline(execution_repository=repository).process(papers, criteria)
    stored = repository.get(result.run.run_id)

    assert stored is not None
    assert stored.run == result.run
    assert stored.results == result.screening_results
    assert stored.audits == result.audits


def test_pipeline_execution_contains_consistent_counts():
    from psi_jarvis.infrastructure.screening_execution_repository import InMemoryScreeningExecutionRepository

    repository = InMemoryScreeningExecutionRepository()
    criteria = ScreeningCriteria(topic="memory")
    papers = [
        Paper(title="Memory Study", doi="10.1234/execution-a"),
        Paper(title="Other Study", doi="10.1234/execution-b"),
    ]

    result = PaperPipeline(execution_repository=repository).process(papers, criteria)
    execution = repository.get(result.run.run_id)

    assert execution is not None
    assert execution.screened_papers == len(result.screening_results)
    assert execution.included + execution.excluded == execution.screened_papers
    assert execution.run.screened_papers == execution.screened_papers
