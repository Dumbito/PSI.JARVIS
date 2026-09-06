from datetime import datetime, timezone

import pandas as pd

from psi_jarvis.application.acquisition import AcquisitionRequest

from psi_jarvis.domain.paper import Paper
from psi_jarvis.infrastructure.importers.csv_importer import CSVImporter
from psi_jarvis.infrastructure.importers.excel_importer import ExcelImporter


def test_csv_importer_returns_papers(tmp_path):
    path = tmp_path / "papers.csv"

    pd.DataFrame([
        {
            "title": "Memory and Intelligence",
            "authors": "John Doe; Jane Doe",
            "abstract": "A study about memory.",
            "doi": "10.1234/test",
            "pmid": "123456",
            "publication_year": 2024,
            "journal": "Neuroscience Journal",
        }
    ]).to_csv(path, index=False)

    result = CSVImporter().import_file(path)

    assert result.success is True
    assert len(result.data) == 1
    assert isinstance(result.data[0], Paper)
    assert result.data[0].title == "Memory and Intelligence"
    assert result.data[0].provenances[0].source_key == "csv"


def test_excel_importer_returns_papers(tmp_path):
    path = tmp_path / "papers.xlsx"

    pd.DataFrame([
        {
            "title": "Brain Development",
            "authors": "Alice Smith; Bob Smith",
            "abstract": "A study about brain development.",
            "doi": "10.5678/test",
            "pmid": "789012",
            "publication_year": 2023,
            "journal": "Brain Research",
        }
    ]).to_excel(path, index=False)

    result = ExcelImporter().import_file(path)

    assert result.success is True
    assert len(result.data) == 1
    assert isinstance(result.data[0], Paper)
    assert result.data[0].title == "Brain Development"
    assert result.data[0].provenances[0].source_key == "excel"


def test_csv_importer_supports_multiple_papers(tmp_path):
    path = tmp_path / "papers.csv"

    pd.DataFrame([
        {"title": "Paper One"},
        {"title": "Paper Two"},
        {"title": "Paper Three"},
    ]).to_csv(path, index=False)

    result = CSVImporter().import_file(path)

    assert result.success is True
    assert len(result.data) == 3


def test_excel_importer_supports_multiple_papers(tmp_path):
    path = tmp_path / "papers.xlsx"

    pd.DataFrame([
        {"title": "Paper One"},
        {"title": "Paper Two"},
        {"title": "Paper Three"},
    ]).to_excel(path, index=False)

    result = ExcelImporter().import_file(path)

    assert result.success is True
    assert len(result.data) == 3


def test_csv_acquire_returns_new_acquisition_contract(tmp_path):
    path = tmp_path / "papers.csv"
    pd.DataFrame([{"title": "Memory Study"}]).to_csv(path, index=False)

    result = CSVImporter(clock=lambda: datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)).acquire(
        AcquisitionRequest(location=str(path))
    )

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "csv"
    assert result.receipt.acquired_at == datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert len(result.papers) == 1
    assert result.papers[0].provenances[0].source_key == "csv"


def test_excel_acquire_returns_new_acquisition_contract(tmp_path):
    path = tmp_path / "papers.xlsx"
    pd.DataFrame([{"title": "Brain Study"}]).to_excel(path, index=False)

    result = ExcelImporter(clock=lambda: datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)).acquire(
        AcquisitionRequest(location=str(path))
    )

    assert result.success is True
    assert result.receipt is not None
    assert result.receipt.source_key == "excel"
    assert result.receipt.acquired_at == datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    assert len(result.papers) == 1
    assert result.papers[0].provenances[0].source_key == "excel"
