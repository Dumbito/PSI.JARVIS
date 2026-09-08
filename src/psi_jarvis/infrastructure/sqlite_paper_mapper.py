import json
import sqlite3
from datetime import datetime
from uuid import UUID

from psi_jarvis.domain.bibliography.provenance import (
    AcquisitionReceipt,
    BibliographicProvenance,
)
from psi_jarvis.domain.paper import Paper


def paper_from_row(connection: sqlite3.Connection, row: sqlite3.Row) -> Paper:
    provenance_rows = connection.execute(
        """
        SELECT pp.*, ab.source_key, ab.adapter_key, ab.adapter_version,
               ab.acquired_at, ab.request_json, ab.request_sha256,
               ab.input_sha256, ab.source_locator
        FROM paper_provenances pp
        JOIN acquisition_batches ab ON ab.batch_id = pp.batch_id
        WHERE pp.paper_id = ?
        ORDER BY ab.acquired_at, pp.record_ordinal, pp.provenance_key
        """,
        (row["paper_id"],),
    ).fetchall()
    provenances = tuple(
        _provenance_from_row(provenance_row) for provenance_row in provenance_rows
    )
    return Paper(
        id=UUID(row["paper_id"]),
        title=row["title"],
        authors=tuple(json.loads(row["authors"] or "[]")),
        abstract=row["abstract"],
        doi=row["doi"],
        pmid=row["pmid"],
        publication_year=row["publication_year"],
        journal=row["journal"],
        provenances=provenances,
    )


def _provenance_from_row(row: sqlite3.Row) -> BibliographicProvenance:
    receipt = AcquisitionReceipt(
        batch_id=UUID(row["batch_id"]),
        source_key=row["source_key"],
        adapter_key=row["adapter_key"],
        adapter_version=row["adapter_version"],
        acquired_at=datetime.fromisoformat(row["acquired_at"]),
        request_json=row["request_json"],
        request_sha256=row["request_sha256"],
        input_sha256=row["input_sha256"],
        source_locator=row["source_locator"],
    )
    return BibliographicProvenance(
        receipt=receipt,
        record_ordinal=row["record_ordinal"],
        format_name=row["format_name"],
        format_version=row["format_version"],
        mapping_version=row["mapping_version"],
        raw_record_sha256=row["raw_record_sha256"],
        source_record_id=row["source_record_id"],
    )
