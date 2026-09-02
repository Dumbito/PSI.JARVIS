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

def test_persistence_recovery_after_repository_reinitialization(tmp_path):
    database_path = tmp_path / "recovery.db"
    project_repository = SQLiteProjectRepository(database_path)
    paper_repository = SQLitePaperRepository(database_path)
    corpus_repository = SQLiteCorpusRepository(database_path)
    run_repository = SQLiteScreeningRunRepository(database_path)
    pipeline = PaperPipeline(run_repository=run_repository)
    create_project = CreateReviewProjectService(project_repository)
    screen_project = ScreenReviewProjectService(project_repository, pipeline)
    criteria = ScreeningCriteria(topic="memory", inclusion=("cognition",))
    project = create_project.execute(name="Recovery Review", criteria=criteria)
    paper = Paper(title="Memory and Cognition", abstract="Memory and cognition are related.", doi="10.1000/recovery-1")
    paper_repository.save(paper)
    corpus = Corpus.create(project_id=project.project_id, papers=(paper,))
    corpus_repository.save(corpus)
    result = screen_project.execute(project.project_id, (paper,))
    run_id = result.run.run_id
    del project_repository, paper_repository, corpus_repository, run_repository, pipeline, create_project, screen_project
    recovered_project_repository = SQLiteProjectRepository(database_path)
    recovered_paper_repository = SQLitePaperRepository(database_path)
    recovered_corpus_repository = SQLiteCorpusRepository(database_path)
    recovered_run_repository = SQLiteScreeningRunRepository(database_path)
    recovered_project = recovered_project_repository.get(project.project_id)
    recovered_paper = recovered_paper_repository.get(paper.id)
    recovered_corpus = recovered_corpus_repository.get(corpus.corpus_id)
    recovered_run = recovered_run_repository.get(run_id)
    assert recovered_project is not None
    assert recovered_project.project_id == project.project_id
    assert recovered_project.criteria == project.criteria
    assert recovered_paper is not None
    assert recovered_paper.id == paper.id
    assert recovered_paper.doi == paper.doi
    assert recovered_corpus is not None
    assert recovered_corpus.project_id == project.project_id
    assert len(recovered_corpus.papers) == 1
    assert recovered_corpus.papers[0].id == paper.id
    assert recovered_run is not None
    assert recovered_run.run_id == run_id
    assert recovered_run.project_id == project.project_id
