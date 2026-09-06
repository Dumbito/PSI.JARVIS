from datetime import datetime, timezone
from pathlib import Path

from psi_jarvis.application.acquisition import AcquisitionRequest, AcquisitionService
from psi_jarvis.infrastructure.acquisition import RISImporter


FIXED_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parents[1] / "fixtures"


def request(name: str) -> AcquisitionRequest:
    return AcquisitionRequest(location=str(FIXTURES / name), context="deterministic fixture", acquired_at=FIXED_TIME)


def test_ris_importer_maps_valid_and_incomplete_records_with_provenance():
    result = RISImporter().acquire(request("local_records.ris"))

    assert result.success is True
    assert len(result.papers) == 2
    first, second = result.papers
    assert first.title == "Memory and Intelligence"
    assert first.authors == ("Doe, Jane", "Smith, John")
    assert first.doi == "https://doi.org/10.1000/RIS-1"
    assert first.pmid == "PMID: 12345"
    assert first.provenances[0].record_ordinal == 1
    assert second.title == "Memory without optional metadata"
    assert any(issue.code == "unknown_field" and issue.severity == "warning" for issue in result.issues)


def test_ris_importer_is_deterministic_for_same_fixture_and_controlled_clock():
    first = RISImporter().acquire(request("local_records.ris"))
    second = AcquisitionService(RISImporter()).execute(request("local_records.ris"))

    assert first == second
    assert first.receipt is not None
    assert first.receipt.acquired_at == FIXED_TIME


def test_ris_importer_reports_malformed_input_without_papers():
    result = RISImporter().acquire(request("malformed_records.ris"))

    assert result.success is False
    assert result.papers == ()
    assert result.issues[0].code == "invalid_format"


def test_ris_importer_reports_missing_source_without_network_access(tmp_path):
    result = RISImporter().acquire(
        AcquisitionRequest(location=str(tmp_path / "missing.ris"), acquired_at=FIXED_TIME)
    )

    assert result.success is False
    assert result.issues[0].code == "source_unavailable"
