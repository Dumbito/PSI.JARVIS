from dataclasses import dataclass

from psi_jarvis.application.visualization.screening_flow import ScreeningFlow
from psi_jarvis.domain.analysis import (
    DecisionDistribution,
    ExclusionReasonAnalysis,
    PublicationYearAnalysis,
)


@dataclass(frozen=True)
class SVGChartRenderer:
    width: int = 800
    height: int = 500

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("SVG dimensions must be positive")

    def render_decision_distribution(
        self,
        analysis: DecisionDistribution,
    ) -> str:
        return self._render_bar_chart(
            "Decision Distribution",
            tuple(analysis.counts.keys()),
            tuple(analysis.counts.values()),
        )

    def render_publication_year(
        self,
        analysis: PublicationYearAnalysis,
    ) -> str:
        return self._render_bar_chart(
            "Publication Year Distribution",
            tuple(str(year) for year, _ in analysis.by_year),
            tuple(count for _, count in analysis.by_year),
        )

    def render_exclusion_reasons(
        self,
        analysis: ExclusionReasonAnalysis,
    ) -> str:
        return self._render_bar_chart(
            "Exclusion Reasons",
            tuple(item.reason for item in analysis.reasons),
            tuple(item.count for item in analysis.reasons),
        )

    def render_screening_flow(self, flow: ScreeningFlow) -> str:
        stages = (
            ("Identified", flow.identified),
            ("Duplicates removed", flow.duplicates_removed),
            ("Screened", flow.screened),
            ("Excluded", flow.excluded),
            ("Included", flow.included),
        )

        parts = [
            f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{self.width}\" height=\"{self.height}\" viewBox=\"0 0 {self.width} {self.height}\">",
            f"<text x=\"{self.width / 2:.2f}\" y=\"35\" text-anchor=\"middle\" font-size=\"24\">Screening Flow</text>",
        ]

        box_width = self.width - 240
        box_height = 52
        x = 120
        start_y = 70
        gap = 22

        for index, (label, value) in enumerate(stages):
            y = start_y + index * (box_height + gap)
            parts.append(
                f"<rect x=\"{x}\" y=\"{y}\" width=\"{box_width}\" height=\"{box_height}\" fill=\"white\" stroke=\"black\"/>"
            )
            parts.append(
                f"<text x=\"{self.width / 2:.2f}\" y=\"{y + 22}\" text-anchor=\"middle\" font-size=\"14\">{_escape(label)}</text>"
            )
            parts.append(
                f"<text x=\"{self.width / 2:.2f}\" y=\"{y + 42}\" text-anchor=\"middle\" font-size=\"13\">{value}</text>"
            )
            if index < len(stages) - 1:
                arrow_y = y + box_height
                parts.append(
                    f"<line x1=\"{self.width / 2:.2f}\" y1=\"{arrow_y}\" x2=\"{self.width / 2:.2f}\" y2=\"{arrow_y + gap}\" stroke=\"black\"/>"
                )

        parts.append("</svg>")
        return "".join(parts)

    def _render_bar_chart(
        self,
        title: str,
        labels: tuple[str, ...],
        values: tuple[int, ...],
    ) -> str:
        if len(labels) != len(values):
            raise ValueError(
                "Chart labels and values must have equal length"
            )

        baseline = self.height - 60
        plot_height = self.height - 120
        plot_width = self.width - 120
        slot_width = (
            plot_width / len(values)
            if values
            else plot_width
        )
        maximum = max(values, default=0)

        parts = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{self.width}" '
                f'height="{self.height}" '
                f'viewBox="0 0 {self.width} {self.height}">'
            ),
            (
                f'<text x="{self.width / 2:.2f}" y="35" '
                f'text-anchor="middle" font-size="24">'
                f'{_escape(title)}</text>'
            ),
            (
                f'<line x1="60" y1="{baseline}" '
                f'x2="{self.width - 60}" '
                f'y2="{baseline}" stroke="black"/>'
            ),
        ]

        for index, (label, value) in enumerate(
            zip(labels, values)
        ):
            x = (
                60
                + index * slot_width
                + slot_width * 0.15
            )
            bar_width = slot_width * 0.7
            bar_height = (
                0
                if maximum == 0
                else value / maximum * plot_height
            )
            y = baseline - bar_height
            center = x + bar_width / 2

            parts.append(
                (
                    f'<rect x="{x:.2f}" y="{y:.2f}" '
                    f'width="{bar_width:.2f}" '
                    f'height="{bar_height:.2f}"/>'
                )
            )

            parts.append(
                (
                    f'<text x="{center:.2f}" '
                    f'y="{baseline + 20}" '
                    f'text-anchor="middle" '
                    f'font-size="12">'
                    f'{_escape(label)}</text>'
                )
            )

            parts.append(
                (
                    f'<text x="{center:.2f}" '
                    f'y="{max(y - 6, 50):.2f}" '
                    f'text-anchor="middle" '
                    f'font-size="12">{value}</text>'
                )
            )

        parts.append("</svg>")
        return "".join(parts)


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )