class BibliographicAdapterRegistry:
    """Registro determinista de adaptadores bibliográficos por fuente."""

    def __init__(self) -> None:
        self._adapters: dict[str, type] = {}

    def register(self, adapter: type) -> None:
        source_key = getattr(adapter, "source_key", "")
        if not isinstance(source_key, str) or not source_key.strip():
            raise ValueError("Bibliographic adapter source_key cannot be empty")
        if source_key in self._adapters:
            raise ValueError(f"Bibliographic source already registered: {source_key}")
        self._adapters[source_key] = adapter

    def resolve(self, source_key: str) -> type:
        try:
            return self._adapters[source_key]
        except KeyError as exc:
            raise KeyError(f"Unknown bibliographic source: {source_key}") from exc

    def sources(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))



def build_bibliographic_registry(*adapters: type) -> BibliographicAdapterRegistry:
    """Construye un registro a partir de clases de adaptadores explícitas."""
    registry = BibliographicAdapterRegistry()
    for adapter in adapters:
        registry.register(adapter)
    return registry
