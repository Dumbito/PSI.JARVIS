from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path

from psi_jarvis.application.acquisition import AcquisitionRequest, AcquisitionService
from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.engine import ScreeningEngine
from psi_jarvis.infrastructure.acquisition import RISImporter
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository


FIXTURES = Path(__file__).parents[1] / "fixtures"
FIXED_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def acquire():
    return AcquisitionService(RISImporter()).execute(
        AcquisitionRequest(
            location=str(FIXTURES / "local_records.ris"),
            context="integration fixture",
            acquired_at=FIXED_TIME,
        )
    )


def test_ris_acquisition_pipeline_preserves_scientific_decisions_and_provenance():
    acquisition = acquire()
    result = PaperPipeline().process(acquisition.papers, ScreeningCriteria(topic="memory"))

    assert acquisition.success is True
    assert result.screened_papers == 2
    assert result.papers[0].provenances[0].source_key == "ris"
    assert [item.included for item in result.screening_results] == [True, True]


def test_same_ris_fixture_and_criteria_have_same_decisions_audits_and_metrics():
    criteria = ScreeningCriteria(topic="memory")
    first = PaperPipeline().process(acquire().papers, criteria)
    second = PaperPipeline().process(acquire().papers, criteria)

    first_decisions = tuple((item.paper_id, item.included, item.reason, item.criteria_version) for item in first.screening_results)
    second_decisions = tuple((item.paper_id, item.included, item.reason, item.criteria_version) for item in second.screening_results)
    first_audits = tuple((item.paper_id, item.included, item.reason, item.criteria_version) for item in first.audits)
    second_audits = tuple((item.paper_id, item.included, item.reason, item.criteria_version) for item in second.audits)

    assert first_decisions == second_decisions
    assert first_audits == second_audits
    assert first.screening_metrics == second.screening_metrics


def test_ris_acquisition_persists_provenance_through_sqlite(tmp_path):
    acquisition = acquire()
    repository = SQLitePaperRepository(tmp_path / "ris.db")

    for paper in acquisition.papers:
        repository.save(paper)

    reloaded = repository.list_all()

    assert len(reloaded) == len(acquisition.papers)
    assert [paper.id for paper in reloaded] == [paper.id for paper in acquisition.papers]
    assert [paper.provenances for paper in reloaded] == [paper.provenances for paper in acquisition.papers]
    assert all(paper.provenances[0].source_key == "ris" for paper in reloaded)


def test_provenance_does_not_change_screening_engine_decision():
    paper = acquire().papers[0]
    criteria = ScreeningCriteria(topic="memory")
    engine = ScreeningEngine(criteria)

    with_provenance = engine.evaluate(paper)
    without_provenance = engine.evaluate(replace(paper, provenances=()))

    assert with_provenance == without_provenance
