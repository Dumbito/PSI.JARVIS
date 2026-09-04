from psi_jarvis.domain.analysis.deduplication_analysis import DeduplicationAnalysis


def test_deduplication_analysis_counts_input_and_unique_papers():
    analysis = DeduplicationAnalysis(
        total_input=10,
        unique_papers=7,
        duplicate_papers=3,
    )

    assert analysis.total_input == 10
    assert analysis.unique_papers == 7
    assert analysis.duplicate_papers == 3
    assert analysis.duplicate_rate == 0.3


def test_deduplication_analysis_empty_input():
    analysis = DeduplicationAnalysis(
        total_input=0,
        unique_papers=0,
        duplicate_papers=0,
    )

    assert analysis.duplicate_rate == 0.0


def test_deduplication_analysis_is_frozen():
    analysis = DeduplicationAnalysis(
        total_input=5,
        unique_papers=4,
        duplicate_papers=1,
    )

    try:
        analysis.total_input = 6
    except AttributeError:
        pass
    else:
        raise AssertionError("DeduplicationAnalysis must be immutable")


def test_deduplication_analysis_rejects_invalid_counts():
    try:
        DeduplicationAnalysis(
            total_input=5,
            unique_papers=3,
            duplicate_papers=1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Inconsistent counts should fail")


def test_deduplication_analysis_rejects_negative_values():
    try:
        DeduplicationAnalysis(
            total_input=-1,
            unique_papers=0,
            duplicate_papers=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Negative counts should fail")
