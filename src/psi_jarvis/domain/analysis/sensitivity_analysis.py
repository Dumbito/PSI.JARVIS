from dataclasses import dataclass

from psi_jarvis.domain.screening.result import ScreeningResult


@dataclass(frozen=True)
class SensitivityAnalysis:
    """Describe how screening decisions change between two criteria configurations."""

    total_papers: int
    base_criteria_version: str
    alternative_criteria_version: str
    base_included: int
    base_excluded: int
    alternative_included: int
    alternative_excluded: int
    changed_decisions: int
    newly_included: int
    newly_excluded: int
    unchanged_decisions: int

    def __post_init__(self) -> None:
        values = (
            self.total_papers,
            self.base_included,
            self.base_excluded,
            self.alternative_included,
            self.alternative_excluded,
            self.changed_decisions,
            self.newly_included,
            self.newly_excluded,
            self.unchanged_decisions,
        )

        if any(value < 0 for value in values):
            raise ValueError("Sensitivity counts cannot be negative")

        if self.base_included + self.base_excluded != self.total_papers:
            raise ValueError("Base decisions must equal total papers")

        if self.alternative_included + self.alternative_excluded != self.total_papers:
            raise ValueError("Alternative decisions must equal total papers")

        if self.changed_decisions + self.unchanged_decisions != self.total_papers:
            raise ValueError("Changed and unchanged decisions must equal total papers")

        if self.newly_included + self.newly_excluded != self.changed_decisions:
            raise ValueError("Newly included and newly excluded decisions must equal changed decisions")

        if not self.base_criteria_version:
            raise ValueError("Base criteria version cannot be empty")

        if not self.alternative_criteria_version:
            raise ValueError("Alternative criteria version cannot be empty")

        if self.base_criteria_version == self.alternative_criteria_version:
            raise ValueError("Base and alternative criteria versions must differ")

    @classmethod
    def from_results(
        cls,
        base_results: tuple[ScreeningResult, ...],
        alternative_results: tuple[ScreeningResult, ...],
    ) -> "SensitivityAnalysis":
        if len({result.paper_id for result in base_results}) != len(base_results):
            raise ValueError("Base results must not contain duplicate papers")

        if len({result.paper_id for result in alternative_results}) != len(alternative_results):
            raise ValueError("Alternative results must not contain duplicate papers")

        base_by_id = {result.paper_id: result for result in base_results}
        alternative_by_id = {
            result.paper_id: result for result in alternative_results
        }

        if set(base_by_id) != set(alternative_by_id):
            raise ValueError("Base and alternative results must contain the same papers")

        base_versions = {result.criteria_version for result in base_by_id.values()}
        alternative_versions = {
            result.criteria_version for result in alternative_by_id.values()
        }

        if len(base_versions) != 1:
            raise ValueError("Base results must use a single criteria version")

        if len(alternative_versions) != 1:
            raise ValueError("Alternative results must use a single criteria version")

        base_criteria_version = next(iter(base_versions))
        alternative_criteria_version = next(iter(alternative_versions))

        if not base_criteria_version:
            raise ValueError("Base criteria version cannot be empty")

        if not alternative_criteria_version:
            raise ValueError("Alternative criteria version cannot be empty")

        if base_criteria_version == alternative_criteria_version:
            raise ValueError("Base and alternative criteria versions must differ")

        total_papers = len(base_by_id)
        base_included = sum(result.included for result in base_by_id.values())
        base_excluded = total_papers - base_included
        alternative_included = sum(
            result.included for result in alternative_by_id.values()
        )
        alternative_excluded = total_papers - alternative_included

        changed_decisions = 0
        newly_included = 0
        newly_excluded = 0

        for paper_id, base_result in base_by_id.items():
            alternative_result = alternative_by_id[paper_id]

            if base_result.included == alternative_result.included:
                continue

            changed_decisions += 1

            if alternative_result.included:
                newly_included += 1
            else:
                newly_excluded += 1

        return cls(
            total_papers=total_papers,
            base_criteria_version=base_criteria_version,
            alternative_criteria_version=alternative_criteria_version,
            base_included=base_included,
            base_excluded=base_excluded,
            alternative_included=alternative_included,
            alternative_excluded=alternative_excluded,
            changed_decisions=changed_decisions,
            newly_included=newly_included,
            newly_excluded=newly_excluded,
            unchanged_decisions=total_papers - changed_decisions,
        )
