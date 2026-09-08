from dataclasses import dataclass

from psi_jarvis.domain.criteria.screening import ScreeningCriteria
from psi_jarvis.domain.criteria.version import ScreeningCriteriaVersion
from psi_jarvis.domain.screening.result import ScreeningResult


@dataclass(frozen=True)
class ConfigurationProfile:
    criteria_version: str
    topic: str
    inclusion_rule_count: int
    exclusion_rule_count: int
    has_custom_logic: bool
    total_papers: int
    included_papers: int
    excluded_papers: int

    def __post_init__(self) -> None:
        counts = (
            self.inclusion_rule_count,
            self.exclusion_rule_count,
            self.total_papers,
            self.included_papers,
            self.excluded_papers,
        )

        if any(value < 0 for value in counts):
            raise ValueError("Configuration counts cannot be negative")

        if self.included_papers + self.excluded_papers != self.total_papers:
            raise ValueError("Included and excluded papers must equal total papers")

        if not self.criteria_version:
            raise ValueError("Configuration criteria version cannot be empty")

        if not self.topic.strip():
            raise ValueError("Configuration topic cannot be empty")


@dataclass(frozen=True)
class ConfigurationComparison:
    profiles: tuple[ConfigurationProfile, ...]
    total_papers: int

    def __post_init__(self) -> None:
        if len(self.profiles) < 2:
            raise ValueError(
                "Configuration comparison requires at least two configurations"
            )

        if self.total_papers < 0:
            raise ValueError("Total papers cannot be negative")

        versions = [profile.criteria_version for profile in self.profiles]
        if len(set(versions)) != len(versions):
            raise ValueError("Configuration criteria versions must be unique")

        if any(profile.total_papers != self.total_papers for profile in self.profiles):
            raise ValueError(
                "All configuration profiles must use the same total papers"
            )

    @property
    def configuration_count(self) -> int:
        return len(self.profiles)

    @property
    def minimum_included(self) -> int:
        return min(profile.included_papers for profile in self.profiles)

    @property
    def maximum_included(self) -> int:
        return max(profile.included_papers for profile in self.profiles)

    @property
    def included_range(self) -> int:
        return self.maximum_included - self.minimum_included

    @classmethod
    def from_runs(
        cls,
        runs: tuple[
            tuple[ScreeningCriteria, tuple[ScreeningResult, ...]],
            ...,
        ],
    ) -> "ConfigurationComparison":
        if len(runs) < 2:
            raise ValueError(
                "Configuration comparison requires at least two configurations"
            )

        profiles: list[ConfigurationProfile] = []
        paper_ids_reference: set = set()
        total_papers: int | None = None

        for index, (criteria, results) in enumerate(runs):
            paper_ids = {result.paper_id for result in results}

            if len(paper_ids) != len(results):
                raise ValueError(
                    f"Configuration {index} results must not contain duplicate papers"
                )

            expected_version = ScreeningCriteriaVersion.from_criteria(criteria).value

            result_versions = {result.criteria_version for result in results}

            if result_versions != {expected_version}:
                raise ValueError(
                    f"Configuration {index} results do not match its criteria version"
                )

            if index == 0:
                paper_ids_reference = paper_ids
                total_papers = len(results)
            elif paper_ids != paper_ids_reference:
                raise ValueError("All configurations must contain the same papers")

            included = sum(result.included for result in results)
            excluded = len(results) - included

            profiles.append(
                ConfigurationProfile(
                    criteria_version=expected_version,
                    topic=criteria.topic.strip(),
                    inclusion_rule_count=len(criteria.inclusion),
                    exclusion_rule_count=len(criteria.exclusion),
                    has_custom_logic=criteria.has_custom_logic,
                    total_papers=len(results),
                    included_papers=included,
                    excluded_papers=excluded,
                )
            )

        profiles.sort(key=lambda profile: profile.criteria_version)

        return cls(
            profiles=tuple(profiles),
            total_papers=total_papers if total_papers is not None else 0,
        )
