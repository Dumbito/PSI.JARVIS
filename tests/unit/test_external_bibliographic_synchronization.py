from dataclasses import dataclass
from datetime import datetime, timezone

from psi_jarvis.application.acquisition.contracts import AcquisitionResult, BibliographicQuery
from psi_jarvis.application.synchronization import (
    ExternalBibliographicSynchronizationService,
    BibliographicSynchronizationService,
)
from psi_jarvis.domain.paper import Paper


FIXED_TIME = datetime(2026, 9, 7, 4, 45, tzinfo=timezone.utc)


@dataclass
class FakeAcquisitionService:
    result: AcquisitionResult
    received_source: str | None = None
    received_query: BibliographicQuery | None = None

    def execute_query_from_source(self, source_key: str, query: BibliographicQuery) -> AcquisitionResult:
        self.received_source = source_key
        self.received_query = query
        return self.result


@dataclass
class FakePaperRepository:
    papers: list[Paper]

    def save(self, paper: Paper) -> None:
        for index, current in enumerate(self.papers):
            if current.id == paper.id:
                self.papers[index] = paper
                return
        self.papers.append(paper)

    def get(self, paper_id):
        return next((paper for paper in self.papers if paper.id == paper_id), None)

    def list_all(self):
        return tuple(self.papers)

    def delete(self, paper_id):
        self.papers[:] = [paper for paper in self.papers if paper.id != paper_id]


class FakeHistoryRepository:
    def record(self, change):
        pass


def test_external_sync_delegates_source_query_and_applies_acquired_papers():
    query = BibliographicQuery(text="memory")
    acquisition = AcquisitionResult(receipt=None, papers=(), issues=())
    acquisition_service = FakeAcquisitionService(acquisition)
    sync_service = BibliographicSynchronizationService(
        FakePaperRepository([]),
        FakeHistoryRepository(),
        lambda: FIXED_TIME,
    )
    orchestrator = ExternalBibliographicSynchronizationService(acquisition_service, sync_service)

    result = orchestrator.synchronize("pubmed", query)

    assert result.success
    assert acquisition_service.received_source == "pubmed"
    assert acquisition_service.received_query == query
    assert result.synchronization.new_records == 0


def test_external_sync_does_not_mutate_repository_when_acquisition_fails():
    from psi_jarvis.application.acquisition.contracts import AcquisitionIssue

    failed = AcquisitionResult(
        receipt=None,
        papers=(),
        issues=(AcquisitionIssue(code="auth_required", message="Authentication required"),),
    )
    acquisition_service = FakeAcquisitionService(failed)
    repository = FakePaperRepository([])
    sync_service = BibliographicSynchronizationService(repository, FakeHistoryRepository(), lambda: FIXED_TIME)
    orchestrator = ExternalBibliographicSynchronizationService(acquisition_service, sync_service)

    result = orchestrator.synchronize("scopus", BibliographicQuery(text="memory"))

    assert not result.success
    assert result.synchronization is None
    assert repository.papers == []
