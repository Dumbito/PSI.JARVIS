from psi_jarvis.application.pipeline.pipeline import PaperPipeline
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.paper import Paper

def test_pipeline_returns_correct_statistical_summary():
    papers = (
        Paper(title="Memory and Cognition", abstract="Memory and cognition are related.", doi="10.1000/stats-1"),
        Paper(title="Memory and Cognition", abstract="Memory and cognition are related.", doi="10.1000/stats-1"),
        Paper(title="Memory in Animal Models", abstract="Animal models study memory.", doi="10.1000/stats-2"),
    )
    criteria = ScreeningCriteria(topic="memory", inclusion=("cognition",), exclusion=("animal",))
    result = PaperPipeline().process(papers, criteria)
    statistics = result.statistics
    assert statistics.total_input == 3
    assert statistics.unique_papers == 2
    assert statistics.duplicates_removed == 1
    assert statistics.screened_papers == 2
    assert statistics.included_papers == 1
    assert statistics.excluded_papers == 1
    assert statistics.inclusion_rate == 0.5
    assert statistics.exclusion_rate == 0.5
    assert statistics.deduplication_rate == 1 / 3
