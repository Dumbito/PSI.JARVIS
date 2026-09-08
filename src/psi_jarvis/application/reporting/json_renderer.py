import json
from dataclasses import dataclass

from psi_jarvis.domain.reporting import Report


@dataclass(frozen=True)
class JSONRenderer:
    indent: int = 2

    def render(self, report: Report) -> str:
        payload = {
            "title": report.title,
            "statistics": {
                "total_input": report.statistics.total_input,
                "unique_papers": report.statistics.unique_papers,
                "duplicates_removed": report.statistics.duplicates_removed,
                "screened_papers": report.statistics.screened_papers,
                "included_papers": report.statistics.included_papers,
                "excluded_papers": report.statistics.excluded_papers,
                "inclusion_rate": report.statistics.inclusion_rate,
                "exclusion_rate": report.statistics.exclusion_rate,
                "deduplication_rate": report.statistics.deduplication_rate,
            },
            "screening_metrics": {
                "total_input": report.screening_metrics.total_input,
                "screened_papers": report.screening_metrics.screened_papers,
                "included_papers": report.screening_metrics.included_papers,
                "excluded_papers": report.screening_metrics.excluded_papers,
                "duplicates_removed": report.screening_metrics.duplicates_removed,
                "total_matched_rules": report.screening_metrics.total_matched_rules,
                "total_failed_rules": report.screening_metrics.total_failed_rules,
                "screening_completion_rate": report.screening_metrics.screening_completion_rate,
                "screening_yield": report.screening_metrics.screening_yield,
                "exclusion_yield": report.screening_metrics.exclusion_yield,
                "average_matched_rules": report.screening_metrics.average_matched_rules,
                "average_failed_rules": report.screening_metrics.average_failed_rules,
            },
            "decision_distribution": {
                "total": report.decision_distribution.total,
                "included": report.decision_distribution.included,
                "excluded": report.decision_distribution.excluded,
                "inclusion_rate": report.decision_distribution.inclusion_rate,
                "exclusion_rate": report.decision_distribution.exclusion_rate,
            },
            "deduplication_analysis": {
                "total_input": report.deduplication_analysis.total_input,
                "unique_papers": report.deduplication_analysis.unique_papers,
                "duplicate_papers": report.deduplication_analysis.duplicate_papers,
                "duplicate_rate": report.deduplication_analysis.duplicate_rate,
            },
            "metadata_quality": {
                "total_papers": report.metadata_quality.total_papers,
                "overall_completeness_rate": report.metadata_quality.overall_completeness_rate,
                "fields": [
                    {
                        "field": field.field,
                        "present": field.present,
                        "missing": field.missing,
                        "total": field.total,
                        "completeness_rate": field.completeness_rate,
                    }
                    for field in report.metadata_quality.fields
                ],
            },
            "authors": {
                "total_papers": report.author_analysis.total_papers,
                "papers_with_authors": report.author_analysis.papers_with_authors,
                "papers_without_authors": report.author_analysis.papers_without_authors,
                "unique_authors": report.author_analysis.unique_authors,
                "author_coverage_rate": report.author_analysis.author_coverage_rate,
                "by_author": [
                    {"author": author, "count": count}
                    for author, count in report.author_analysis.by_author
                ],
            },
            "journals": {
                "total_papers": report.journal_analysis.total_papers,
                "papers_with_journal": report.journal_analysis.papers_with_journal,
                "papers_without_journal": report.journal_analysis.papers_without_journal,
                "unique_journals": report.journal_analysis.unique_journals,
                "journal_coverage_rate": report.journal_analysis.journal_coverage_rate,
                "by_journal": [
                    {"journal": journal, "count": count}
                    for journal, count in report.journal_analysis.by_journal
                ],
            },
            "publication_year": {
                "total_papers": report.publication_year_analysis.total_papers,
                "papers_with_year": report.publication_year_analysis.papers_with_year,
                "papers_without_year": report.publication_year_analysis.papers_without_year,
                "year_min": report.publication_year_analysis.year_min,
                "year_max": report.publication_year_analysis.year_max,
                "year_coverage_rate": report.publication_year_analysis.year_coverage_rate,
                "by_year": [
                    {"year": year, "count": count}
                    for year, count in report.publication_year_analysis.by_year
                ],
            },
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "matched": rule.matched,
                    "failed": rule.failed,
                    "evaluated": rule.evaluated,
                    "match_rate": rule.match_rate,
                    "failure_rate": rule.failure_rate,
                }
                for rule in report.rule_analysis.rules
            ],
            "criteria": [
                {
                    "criterion_id": criterion.criterion_id,
                    "matched": criterion.matched,
                    "failed": criterion.failed,
                    "evaluated": criterion.evaluated,
                    "match_rate": criterion.match_rate,
                    "failure_rate": criterion.failure_rate,
                }
                for criterion in report.criteria_analysis.criteria
            ],
            "exclusion_reasons": [
                {
                    "reason": reason.reason,
                    "count": reason.count,
                    "total_excluded": reason.total_excluded,
                    "rate": reason.rate,
                }
                for reason in report.exclusion_reason_analysis.reasons
            ],
        }

        return json.dumps(
            payload,
            indent=self.indent,
            sort_keys=True,
            ensure_ascii=False,
        )
