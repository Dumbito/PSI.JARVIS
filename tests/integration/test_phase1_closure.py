from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.corpus.corpus import Corpus
from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.sqlite_project_repository import SQLiteProjectRepository
from psi_jarvis.infrastructure.sqlite_paper_repository import SQLitePaperRepository
from psi_jarvis.infrastructure.sqlite_corpus_repository import SQLiteCorpusRepository
from psi_jarvis.infrastructure.sqlite_screening_run_repository import SQLiteScreeningRunRepository

def test_phase1_repository_contracts_and_reproducibility(tmp_path):
    database_path = tmp_path / "phase1.db"
    project_repo = SQLiteProjectRepository(database_path)
    paper_repo = SQLitePaperRepository(database_path)
    corpus_repo = SQLiteCorpusRepository(database_path)
    run_repo = SQLiteScreeningRunRepository(database_path)
    criteria = ScreeningCriteria(topic="memory", inclusion=("cognition",), exclusion=("animal",))
    from psi_jarvis.domain.project import ReviewProject
    project = ReviewProject.create(name="Phase 1", criteria=criteria)
    paper_a = Paper(title="Memory and Cognition", abstract="Human memory and cognition are related.", doi="10.1000/phase1-1")
    paper_b = Paper(title="Animal Memory", abstract="Animal models study memory.", doi="10.1000/phase1-2")
    for repository in (project_repo, paper_repo, corpus_repo, run_repo):
        for method in ("save", "get", "list_all"):
            assert callable(getattr(repository, method, None))
    project_repo.save(project)
    paper_repo.save(paper_a)
    paper_repo.save(paper_b)
    corpus = Corpus.create(project_id=project.project_id, papers=(paper_a, paper_b))
    corpus_repo.save(corpus)
    assert project_repo.get(project.project_id) == project
    assert paper_repo.get(paper_a.id) == paper_a
    assert paper_repo.get(paper_b.id) == paper_b
    recovered_corpus = corpus_repo.get(corpus.corpus_id)
    assert recovered_corpus is not None
    assert recovered_corpus.project_id == project.project_id
    assert tuple(p.id for p in recovered_corpus.papers) == (paper_a.id, paper_b.id)
    first = PaperPipeline().process((paper_a, paper_b), criteria, project_id=project.project_id)
    second = PaperPipeline().process((paper_a, paper_b), criteria, project_id=project.project_id)
    first_semantics = tuple((r.paper_id, r.included, r.reason, r.matched_rules, r.failed_rules, r.matched_rule_ids, r.failed_rule_ids, r.criteria_version) for r in first.screening_results)
    second_semantics = tuple((r.paper_id, r.included, r.reason, r.matched_rules, r.failed_rules, r.matched_rule_ids, r.failed_rule_ids, r.criteria_version) for r in second.screening_results)
    assert first_semantics == second_semantics
    assert first.run.criteria_version == second.run.criteria_version
    assert first.run.project_id == second.run.project_id == project.project_id

def test_phase1_sqlite_run_contract(tmp_path):
    database_path = tmp_path / "run.db"
    repository = SQLiteScreeningRunRepository(database_path)
    assert repository.list_all() == ()
