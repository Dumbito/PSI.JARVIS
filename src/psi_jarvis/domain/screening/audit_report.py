from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningAuditReport:
    "Resumen estadístico inmutable de una ejecución de cribado."

    total_evaluated: int
    included: int
    excluded: int
    exclusion_reasons: tuple[str, ...] = ()

    @property
    def inclusion_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.included / self.total_evaluated

    @property
    def exclusion_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.excluded / self.total_evaluated

    @property
    def exclusion_reason_counts(self) -> dict[str, int]:
        return dict(Counter(self.exclusion_reasons))
