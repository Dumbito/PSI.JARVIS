import pandas as pd

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
