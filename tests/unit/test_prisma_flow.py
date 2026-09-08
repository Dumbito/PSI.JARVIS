import pytest

from psi_jarvis.domain.analysis.prisma_flow import PrismaFlow


def test_from_run_maps_persisted_screening_stages():
    flow = PrismaFlow.from_run(
        total_input=120,
        unique_papers=95,
        duplicates_removed=25,
        screened_papers=95,
        included=18,
        excluded=77,
    )

    assert flow.records_identified == 120
    assert flow.unique_records == 95
    assert flow.records_screened == 95
    assert flow.records_excluded == 77
    assert flow.records_included_for_next_stage == 18
    assert flow.studies_included == 0
    assert flow.reports_sought == 0


def test_from_run_rejects_inconsistent_unique_and_screened_counts():
    with pytest.raises(ValueError, match="unique papers"):
        PrismaFlow.from_run(
            total_input=10,
            unique_papers=8,
            duplicates_removed=2,
            screened_papers=7,
            included=3,
            excluded=4,
        )


def test_prisma_flow_rejects_invalid_stage_relationships():
    with pytest.raises(ValueError, match="Identified records"):
        PrismaFlow(
            records_identified=10,
            duplicates_removed=2,
            records_screened=7,
            records_excluded=2,
            records_included_for_next_stage=5,
        )


def test_prisma_flow_rejects_invalid_later_stage_relationships():
    with pytest.raises(ValueError, match="Reports sought"):
        PrismaFlow(
            records_identified=10,
            duplicates_removed=2,
            records_screened=8,
            records_excluded=4,
            records_included_for_next_stage=4,
            reports_sought=3,
            reports_not_retrieved=1,
            reports_assessed=1,
        )


def test_prisma_flow_rates_are_safe_for_empty_screening():
    flow = PrismaFlow(
        records_identified=0,
        duplicates_removed=0,
        records_screened=0,
        records_excluded=0,
        records_included_for_next_stage=0,
    )

    assert flow.screening_exclusion_rate == 0.0
