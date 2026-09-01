from pathlib import Path

from psi_jarvis.application.screening.import_and_screen import ImportAndScreenService
from psi_jarvis.domain.criteria.screening import ScreeningCriteria


def test_import_and_screen_service_exists():
    assert ImportAndScreenService() is not None


def test_import_and_screen_csv(tmp_path: Path):
    csv_file = tmp_path / "papers.csv"
    csv_file.write_text(chr(10).join([
        "title,authors,abstract,doi,pmid,publication_year,journal",
        "Memory and Intelligence,Author A,Study about memory,10.1234/a,,2024,Journal A",
        "Unrelated Topic,Author B,Other study,10.1234/b,,2023,Journal B",
    ]), encoding="utf-8")

    criteria = ScreeningCriteria(topic="memory")

    result = ImportAndScreenService().execute(
        file_path=csv_file,
        criteria=criteria,
    )

    assert result.total_input == 2
    assert result.unique_papers == 2
    assert result.screened_papers == 2
    assert result.screening_results[0].included is True
    assert result.screening_results[1].included is False
