import pytest

from psi_jarvis.infrastructure.acquisition.registry import BibliographicAdapterRegistry


class FakeAdapter:
    source_key = "fake"


def test_registry_registers_and_resolves_adapter_by_source_key():
    registry = BibliographicAdapterRegistry()
    registry.register(FakeAdapter)

    assert registry.resolve("fake") is FakeAdapter
    assert registry.sources() == ("fake",)


def test_registry_rejects_duplicate_source_keys():
    registry = BibliographicAdapterRegistry()
    registry.register(FakeAdapter)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(FakeAdapter)


def test_registry_rejects_unknown_source_keys():
    registry = BibliographicAdapterRegistry()

    with pytest.raises(KeyError, match="Unknown bibliographic source"):
        registry.resolve("missing")



def test_registry_resolves_a_remote_adapter_without_provider_specific_logic():
    from psi_jarvis.infrastructure.acquisition import RemoteBibliographicAdapter

    class FixtureRemoteAdapter(RemoteBibliographicAdapter):
        source_key = "fixture"
        adapter_key = "fixture-remote"
        adapter_version = "1"
        format_name = "fixture"
        format_version = "1"
        mapping_version = "1"

        def fetch(self, query):
            raise NotImplementedError

        def map_response(self, response, receipt):
            raise NotImplementedError

    registry = BibliographicAdapterRegistry()
    registry.register(FixtureRemoteAdapter)

    resolved = registry.resolve("fixture")
    assert resolved is FixtureRemoteAdapter
    assert issubclass(resolved, RemoteBibliographicAdapter)



def test_registry_factory_builds_registry_from_adapter_classes():
    from psi_jarvis.infrastructure.acquisition.registry import build_bibliographic_registry

    class FirstAdapter:
        source_key = "first"

    class SecondAdapter:
        source_key = "second"

    registry = build_bibliographic_registry(FirstAdapter, SecondAdapter)

    assert registry.sources() == ("first", "second")
    assert registry.resolve("first") is FirstAdapter
    assert registry.resolve("second") is SecondAdapter



def test_registry_can_resolve_a_preconfigured_adapter_instance():
    class ConfiguredAdapter:
        source_key = "configured"

    adapter = ConfiguredAdapter()
    registry = BibliographicAdapterRegistry()
    registry.register(adapter)

    assert registry.resolve("configured") is adapter
    assert registry.sources() == ("configured",)
