from typing import Any

import pandas as pd

from psi_jarvis.domain.paper import Paper


class TabularImporter:
    @staticmethod
    def dataframe_to_papers(dataframe: pd.DataFrame) -> list[Paper]:
        return [
            TabularImporter.row_to_paper(row)
            for _, row in dataframe.iterrows()
        ]

    @staticmethod
    def row_to_paper(row: Any) -> Paper:
        return Paper(
            title=TabularImporter.value(row, "title", ""),
            authors=TabularImporter.authors(row.get("authors")),
            abstract=TabularImporter.value(row, "abstract"),
            doi=TabularImporter.value(row, "doi"),
            pmid=TabularImporter.value(row, "pmid"),
            publication_year=TabularImporter.year(row.get("publication_year")),
            journal=TabularImporter.value(row, "journal"),
        )

    @staticmethod
    def value(row: Any, column: str, default: str | None = None) -> str | None:
        value = row.get(column, default)

        if value is None or pd.isna(value):
            return default

        return str(value).strip()

    @staticmethod
    def authors(value: Any) -> tuple[str, ...]:
        if value is None or pd.isna(value):
            return ()

        return tuple(
            author.strip()
            for author in str(value).split(";")
            if author.strip()
        )

    @staticmethod
    def year(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None

        return int(value)
