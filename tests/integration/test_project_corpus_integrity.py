from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.application.project.create_review_project import CreateReviewProjectService
from psi_jarvis.application.project.screen_review_project import ScreenReviewProjectService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.corpus.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository

def test_project_corpus_paper_run_integrity(tmp_path):
    database_path = tmp_path / "integrity.db"
    project_repository = SQLiteProjectRepository(database_path)
    paper_repository = SQLitePaperRepository(database_path)
    corpus_repository = SQLiteCorpusRepository(database_path)
    run_repository = SQLiteScreeningRunRepository(database_path)
    pipeline = PaperPipeline(run_repository=run_repository)
    create_project = CreateReviewProjectService(project_repository)
    screen_project = ScreenReviewProjectService(project_repository, pipeline)
    criteria = ScreeningCriteria(topic="memory", inclusion=("cognition",))
    project = create_project.execute(name="Integrity Review", criteria=criteria)
    papers = (
        Paper(title="Memory and Cognition", abstract="Memory and cognition are related.", doi="10.1000/integrity-1"),
        Paper(title="Memory", abstract="Memory without the required concept.", doi="10.1000/integrity-2"),
    )
    for paper in papers:
        paper_repository.save(paper)
    corpus = Corpus.create(project_id=project.project_id, papers=papers)
    corpus_repository.save(corpus)
    stored_project = project_repository.get(project.project_id)
    stored_corpus = corpus_repository.get(corpus.corpus_id)
    assert stored_project is not None
    assert stored_corpus is not None
    assert stored_corpus.project_id == stored_project.project_id
    assert tuple(p.id for p in stored_corpus.papers) == tuple(p.id for p in papers)
    stored_papers = tuple(paper_repository.get(paper.id) for paper in papers)
    assert all(paper is not None for paper in stored_papers)
    result = screen_project.execute(project.project_id, papers)
    assert result.run.project_id == project.project_id
    assert run_repository.get(result.run.run_id) is not None
    assert result.screened_papers == 2
