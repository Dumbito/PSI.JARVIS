import pytest

from psi_jarvis.domain.analysis.statistics import StatisticalSummary

def test_statistical_summary_calculates_rates():
    summary = StatisticalSummary(
        total_input=100,
        unique_papers=80,
        duplicates_removed=20,
        screened_papers=80,
        included_papers=50,
        excluded_papers=30,
    )
    assert summary.inclusion_rate == 0.625
    assert summary.exclusion_rate == 0.375
    assert summary.deduplication_rate == 0.20

def test_statistical_summary_accepts_zero_counts():
    summary = StatisticalSummary(0, 0, 0, 0, 0, 0)
    assert summary.inclusion_rate == 0.0
    assert summary.exclusion_rate == 0.0
    assert summary.deduplication_rate == 0.0

def test_statistical_summary_rejects_negative_counts():
    with pytest.raises(ValueError, match="cannot be negative"):
        StatisticalSummary(10, 10, -1, 10, 5, 5)

def test_statistical_summary_rejects_invalid_screening_total():
    with pytest.raises(ValueError, match="Included and excluded"):
        StatisticalSummary(10, 10, 0, 10, 6, 3)

def test_statistical_summary_rejects_invalid_deduplication_total():
    with pytest.raises(ValueError, match="Unique papers and duplicates"):
        StatisticalSummary(10, 8, 1, 8, 4, 4)
