from psi_jarvis.domain.analysis.metadata_quality import (
    MetadataFieldStatistics,
    MetadataQuality,
)
from psi_jarvis.domain.paper import Paper


def test_metadata_field_statistics_completeness_rate():
    statistics = MetadataFieldStatistics(
        field="abstract",
        present=3,
        missing=1,
        total=4,
    )

    assert statistics.completeness_rate == 0.75


def test_metadata_quality_from_papers_counts_fields():
    papers = (
        Paper(
            title="Paper One",
            authors=("Author",),
            abstract="Abstract",
            doi="10.1234/one",
            pmid="123",
            publication_year=2026,
            journal="Journal",
        ),
        Paper(title="Paper Two"),
    )

    quality = MetadataQuality.from_papers(papers)

    assert quality.total_papers == 2
    assert quality.total_fields == 7
    assert quality.by_field("title").present == 2
    assert quality.by_field("authors").present == 1
    assert quality.by_field("abstract").present == 1
    assert quality.by_field("doi").present == 1
    assert quality.by_field("pmid").present == 1
    assert quality.by_field("publication_year").present == 1
    assert quality.by_field("journal").present == 1


def test_metadata_quality_overall_completeness_rate():
    papers = (
        Paper(
            title="Complete",
            authors=("Author",),
            abstract="Abstract",
            doi="10.1234/test",
            pmid="123",
            publication_year=2026,
            journal="Journal",
        ),
        Paper(title="Partial"),
    )

    quality = MetadataQuality.from_papers(papers)

    assert quality.overall_completeness_rate == 8 / 14


def test_metadata_quality_empty_corpus():
    quality = MetadataQuality.from_papers([])

    assert quality.total_papers == 0
    assert quality.total_fields == 7
    assert quality.overall_completeness_rate == 0.0
    assert all(field.present == 0 for field in quality.fields)
    assert all(field.missing == 0 for field in quality.fields)


def test_metadata_quality_by_field_returns_none_for_unknown_field():
    quality = MetadataQuality.from_papers([])

    assert quality.by_field("unknown") is None


def test_metadata_field_statistics_rejects_invalid_values():
    try:
        MetadataFieldStatistics(field="", present=0, missing=0, total=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Empty metadata field should fail")

    try:
        MetadataFieldStatistics(field="title", present=-1, missing=1, total=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative metadata statistics should fail")


def test_metadata_field_statistics_rejects_inconsistent_counts():
    try:
        MetadataFieldStatistics(field="title", present=2, missing=1, total=2)
    except ValueError:
        pass
    else:
        raise AssertionError("Inconsistent metadata statistics should fail")


def test_metadata_quality_rejects_negative_total():
    try:
        MetadataQuality(total_papers=-1, fields=())
    except ValueError:
        pass
    else:
        raise AssertionError("Negative total papers should fail")


def test_metadata_quality_is_deterministic():
    papers = (
        Paper(title="B"),
        Paper(title="A"),
    )

    first = MetadataQuality.from_papers(papers)
    second = MetadataQuality.from_papers(papers)

    assert first == second
    assert [field.field for field in first.fields] == [
        "title",
        "authors",
        "abstract",
        "doi",
        "pmid",
        "publication_year",
        "journal",
    ]
