from uuid import uuid4

from psi_jarvis.domain.analysis.configuration_comparison import (
    ConfigurationComparison,
)
from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.screening.result import ScreeningResult


def make_result(paper_id, criteria_version, included):
    return ScreeningResult(
        paper_id=paper_id,
        included=included,
        reason="test",
        criteria_version=criteria_version,
    )


def test_configuration_comparison_requires_two_configurations():
    try:
        ConfigurationComparison.from_runs(())
    except ValueError as exc:
        assert str(exc) == (
            "Configuration comparison requires at least two configurations"
        )
    else:
        raise AssertionError("At least two configurations must be required")


def test_configuration_comparison_rejects_duplicate_result_papers():
    paper_id = uuid4()
    criteria = ScreeningCriteria(topic="cognition")

    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    version = ScreeningCriteriaVersion.from_criteria(criteria).value
    result = make_result(paper_id, version, True)

    runs = (
        (criteria, (result, result)),
        (ScreeningCriteria(topic="memory"), (
            make_result(
                paper_id,
                ScreeningCriteriaVersion.from_criteria(
                    ScreeningCriteria(topic="memory")
                ).value,
                True,
            ),
        )),
    )

    try:
        ConfigurationComparison.from_runs(runs)
    except ValueError as exc:
        assert str(exc) == "Configuration 0 results must not contain duplicate papers"
    else:
        raise AssertionError("Duplicate result papers must be rejected")


def test_configuration_comparison_rejects_mismatched_criteria_version():
    paper_id = uuid4()
    criteria = ScreeningCriteria(topic="cognition")
    wrong_criteria = ScreeningCriteria(topic="memory")

    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    result = make_result(
        paper_id,
        ScreeningCriteriaVersion.from_criteria(wrong_criteria).value,
        True,
    )

    runs = (
        (criteria, (result,)),
        (wrong_criteria, (
            make_result(
                paper_id,
                ScreeningCriteriaVersion.from_criteria(
                    wrong_criteria
                ).value,
                True,
            ),
        )),
    )

    try:
        ConfigurationComparison.from_runs(runs)
    except ValueError as exc:
        assert str(exc) == "Configuration 0 results do not match its criteria version"
    else:
        raise AssertionError("Mismatched criteria versions must be rejected")


def test_configuration_comparison_preserves_custom_logic_metadata():
    paper_id = uuid4()
    criteria = ScreeningCriteria(
        topic="cognition",
        inclusion=("memory",),
    )
    second_criteria = ScreeningCriteria(topic="memory")

    from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion

    runs = (
        (
            criteria,
            (
                make_result(
                    paper_id,
                    ScreeningCriteriaVersion.from_criteria(criteria).value,
                    True,
                ),
            ),
        ),
        (
            second_criteria,
            (
                make_result(
                    paper_id,
                    ScreeningCriteriaVersion.from_criteria(
                        second_criteria
                    ).value,
                    True,
                ),
            ),
        ),
    )

    comparison = ConfigurationComparison.from_runs(runs)

    assert all(
        not profile.has_custom_logic
        for profile in comparison.profiles
    )


def test_configuration_comparison_rejects_duplicate_versions():
    paper_id = uuid4()
    criteria = ScreeningCriteria(topic="cognition")
    result = make_result(
        paper_id,
        criteria_version=__import__(
            "psi_jarvis.domain.criteria.version",
            fromlist=["ScreeningCriteriaVersion"],
        ).ScreeningCriteriaVersion.from_criteria(criteria).value,
        included=True,
    )

    runs = (
        (criteria, (result,)),
        (criteria, (result,)),
    )

    try:
        ConfigurationComparison.from_runs(runs)
    except ValueError as exc:
        assert str(exc) == "Configuration criteria versions must be unique"
    else:
        raise AssertionError("Duplicate configuration versions must be rejected")
