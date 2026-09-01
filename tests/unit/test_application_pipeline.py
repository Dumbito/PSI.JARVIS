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
