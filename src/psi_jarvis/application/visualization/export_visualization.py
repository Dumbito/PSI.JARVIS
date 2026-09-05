from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisualizationExporter:
    output_dir: Path

    def __post_init__(self) -> None:
        if not str(self.output_dir).strip():
            raise ValueError(
                "Visualization output directory cannot be empty"
            )

    def export(
        self,
        content: str,
        filename: str = "visualization.svg",
    ) -> Path:
        if not content.strip():
            raise ValueError("Visualization content cannot be empty")

        if not filename.strip():
            raise ValueError(
                "Visualization filename cannot be empty"
            )

        path = self.output_dir / filename
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(content, encoding="utf-8")
        return path