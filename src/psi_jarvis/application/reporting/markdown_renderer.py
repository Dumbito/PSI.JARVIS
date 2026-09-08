from dataclasses import dataclass

from psi_jarvis.domain.reporting import Report


@dataclass(frozen=True)
class MarkdownRenderer:
    def render(self, report: Report) -> str:
        lines = [
            f"# {report.title}",
            "",
            "## Statistics",
            "",
            f"- Total input: {report.statistics.total_input}",
            f"- Unique papers: {report.statistics.unique_papers}",
            f"- Duplicates removed: {report.statistics.duplicates_removed}",
            f"- Screened papers: {report.statistics.screened_papers}",
            f"- Included papers: {report.statistics.included_papers}",
            f"- Excluded papers: {report.statistics.excluded_papers}",
            f"- Inclusion rate: {report.statistics.inclusion_rate}",
            f"- Exclusion rate: {report.statistics.exclusion_rate}",
            f"- Deduplication rate: {report.statistics.deduplication_rate}",
            "",
            "## Screening Metrics",
            "",
            f"- Total input: {report.screening_metrics.total_input}",
            f"- Screened papers: {report.screening_metrics.screened_papers}",
            f"- Included papers: {report.screening_metrics.included_papers}",
            f"- Excluded papers: {report.screening_metrics.excluded_papers}",
            f"- Duplicates removed: {report.screening_metrics.duplicates_removed}",
            f"- Total matched rules: {report.screening_metrics.total_matched_rules}",
            f"- Total failed rules: {report.screening_metrics.total_failed_rules}",
            f"- Screening completion rate: {report.screening_metrics.screening_completion_rate}",
            f"- Screening yield: {report.screening_metrics.screening_yield}",
            f"- Exclusion yield: {report.screening_metrics.exclusion_yield}",
            f"- Average matched rules: {report.screening_metrics.average_matched_rules}",
            f"- Average failed rules: {report.screening_metrics.average_failed_rules}",
            "",
            "## Decision Distribution",
            "",
            "| Decision | Count | Rate |",
            "|---|---:|---:|",
            f"| Included | {report.decision_distribution.included} | {report.decision_distribution.inclusion_rate} |",
            f"| Excluded | {report.decision_distribution.excluded} | {report.decision_distribution.exclusion_rate} |",
            "",
            "## Deduplication",
            "",
            f"- Total input: {report.deduplication_analysis.total_input}",
            f"- Unique papers: {report.deduplication_analysis.unique_papers}",
            f"- Duplicate papers: {report.deduplication_analysis.duplicate_papers}",
            f"- Duplicate rate: {report.deduplication_analysis.duplicate_rate}",
            "",
            "## Metadata Quality",
            "",
            f"- Total papers: {report.metadata_quality.total_papers}",
            f"- Overall completeness rate: {report.metadata_quality.overall_completeness_rate}",
            "",
            "| Field | Present | Missing | Total | Completeness rate |",
            "|---|---:|---:|---:|---:|",
        ]

        lines.extend(
            f"| {field.field} | {field.present} | {field.missing} | "
            f"{field.total} | {field.completeness_rate} |"
            for field in report.metadata_quality.fields
        )

        lines.extend(
            [
                "",
                "## Authors",
                "",
                f"- Total papers: {report.author_analysis.total_papers}",
                f"- Papers with authors: {report.author_analysis.papers_with_authors}",
                f"- Papers without authors: {report.author_analysis.papers_without_authors}",
                f"- Unique authors: {report.author_analysis.unique_authors}",
                f"- Author coverage rate: {report.author_analysis.author_coverage_rate}",
                "",
                "| Author | Count |",
                "|---|---:|",
            ]
        )

        lines.extend(
            f"| {author} | {count} |"
            for author, count in report.author_analysis.by_author
        )

        lines.extend(
            [
                "",
                "## Journals",
                "",
                f"- Total papers: {report.journal_analysis.total_papers}",
                f"- Papers with journal: {report.journal_analysis.papers_with_journal}",
                f"- Papers without journal: {report.journal_analysis.papers_without_journal}",
                f"- Unique journals: {report.journal_analysis.unique_journals}",
                f"- Journal coverage rate: {report.journal_analysis.journal_coverage_rate}",
                "",
                "| Journal | Count |",
                "|---|---:|",
            ]
        )

        lines.extend(
            f"| {journal} | {count} |"
            for journal, count in report.journal_analysis.by_journal
        )

        lines.extend(
            [
                "",
                "## Publication Year",
                "",
                f"- Total papers: {report.publication_year_analysis.total_papers}",
                f"- Papers with year: {report.publication_year_analysis.papers_with_year}",
                f"- Papers without year: {report.publication_year_analysis.papers_without_year}",
                f"- Minimum year: {report.publication_year_analysis.year_min}",
                f"- Maximum year: {report.publication_year_analysis.year_max}",
                f"- Year coverage rate: {report.publication_year_analysis.year_coverage_rate}",
                "",
                "| Year | Count |",
                "|---:|---:|",
            ]
        )

        lines.extend(
            f"| {year} | {count} |"
            for year, count in report.publication_year_analysis.by_year
        )

        lines.extend(
            [
                "",
                "## Rules",
                "",
                "| Rule | Matched | Failed | Evaluated | Match rate | Failure rate |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )

        lines.extend(
            f"| {rule.rule_id} | {rule.matched} | {rule.failed} | {rule.evaluated} | "
            f"{rule.match_rate} | {rule.failure_rate} |"
            for rule in report.rule_analysis.rules
        )

        lines.extend(
            [
                "",
                "## Criteria",
                "",
                "| Criterion | Matched | Failed | Evaluated | Match rate | Failure rate |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )

        lines.extend(
            f"| {criterion.criterion_id} | {criterion.matched} | {criterion.failed} | "
            f"{criterion.evaluated} | {criterion.match_rate} | {criterion.failure_rate} |"
            for criterion in report.criteria_analysis.criteria
        )

        lines.extend(
            [
                "",
                "## Exclusion Reasons",
                "",
                "| Reason | Count | Total excluded | Rate |",
                "|---|---:|---:|---:|",
            ]
        )

        lines.extend(
            f"| {reason.reason} | {reason.count} | {reason.total_excluded} | {reason.rate} |"
            for reason in report.exclusion_reason_analysis.reasons
        )

        return "\n".join(lines) + "\n"
