from psi_jarvis.domain.normalization.normalizer import PaperNormalizer
from psi_jarvis.domain.paper import Paper


def test_normalizer_exists():
    assert PaperNormalizer() is not None


def test_normalizer_normalizes_title():
    paper = Paper(title="  Memory   and   Intelligence  ")

    result = PaperNormalizer().normalize(paper)

    assert result.title == "Memory and Intelligence"


def test_normalizer_normalizes_authors():
    paper = Paper(authors=("  John Doe  ", "Jane Doe  "))

    result = PaperNormalizer().normalize(paper)

    assert result.authors == ("John Doe", "Jane Doe")


def test_normalizer_normalizes_doi():
    paper = Paper(doi=" https://doi.org/10.1234/TEST ")

    result = PaperNormalizer().normalize(paper)

    assert result.doi == "10.1234/TEST"


def test_normalizer_normalizes_pmid():
    paper = Paper(pmid=" PMID: 123456 ")

    result = PaperNormalizer().normalize(paper)

    assert result.pmid == "123456"


def test_normalizer_does_not_mutate_original():
    paper = Paper(title="  Original   Title  ")

    result = PaperNormalizer().normalize(paper)

    assert paper.title == "  Original   Title  "
    assert result.title == "Original Title"
