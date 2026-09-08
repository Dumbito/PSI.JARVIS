from typing import Any

import pandas as pd

from psi_jarvis.domain.bibliography.provenance import (
    AcquisitionReceipt,
    BibliographicProvenance,
    canonical_json,
    sha256_text,
)
from psi_jarvis.domain.paper import Paper


class TabularImporter:
    @staticmethod
    def dataframe_to_papers(
        dataframe: pd.DataFrame,
        receipt: AcquisitionReceipt | None = None,
        format_name: str = "tabular",
    ) -> list[Paper]:
        return [
            TabularImporter.row_to_paper(
                row,
                receipt=receipt,
                format_name=format_name,
                record_ordinal=ordinal,
            )
            for ordinal, (_, row) in enumerate(dataframe.iterrows(), start=1)
        ]

    @staticmethod
    def row_to_paper(
        row: Any,
        receipt: AcquisitionReceipt | None = None,
        format_name: str = "tabular",
        record_ordinal: int = 1,
    ) -> Paper:
        provenances = ()
        if receipt is not None:
            raw_record = canonical_json(
                {
                    str(column): None if pd.isna(value) else str(value)
                    for column, value in row.items()
                }
            )
            provenances = (
                BibliographicProvenance(
                    receipt=receipt,
                    record_ordinal=record_ordinal,
                    format_name=format_name,
                    format_version="1",
                    mapping_version="1",
                    raw_record_sha256=sha256_text(raw_record),
                ),
            )
        return Paper(
            title=TabularImporter.value(row, "title", ""),
            authors=TabularImporter.authors(row.get("authors")),
            abstract=TabularImporter.value(row, "abstract"),
            doi=TabularImporter.value(row, "doi"),
            pmid=TabularImporter.value(row, "pmid"),
            publication_year=TabularImporter.year(row.get("publication_year")),
            journal=TabularImporter.value(row, "journal"),
            provenances=provenances,
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
            author.strip() for author in str(value).split(";") if author.strip()
        )

    @staticmethod
    def year(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None

        return int(value)
