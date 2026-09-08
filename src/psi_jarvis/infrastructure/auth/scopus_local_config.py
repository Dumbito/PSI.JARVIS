from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from getpass import getpass
from pathlib import Path

DEFAULT_SCOPUS_CONFIG_PATH = (
    Path.home() / ".config" / "psi-jarvis" / "connections" / "scopus_config.json"
)


@dataclass(frozen=True)
class ScopusLocalConfig:
    api_key: str
    insttoken: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    scopes: tuple[str, ...] = ()
    base_url: str = "https://api.elsevier.com/content/search/scopus"
    redirect_port: int = 0


class ScopusLocalConfigStore:
    def __init__(self, path: Path = DEFAULT_SCOPUS_CONFIG_PATH) -> None:
        self._path = path

    def save(self, config: ScopusLocalConfig) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.parent.chmod(0o700)
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        temporary.replace(self._path)
        self._path.chmod(0o600)

    def load(self) -> ScopusLocalConfig | None:
        if not self._path.exists():
            return None
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return ScopusLocalConfig(
            api_key=payload["api_key"],
            insttoken=payload.get("insttoken"),
            client_id=payload.get("client_id"),
            client_secret=payload.get("client_secret"),
            authorization_endpoint=payload.get("authorization_endpoint"),
            token_endpoint=payload.get("token_endpoint"),
            scopes=tuple(payload.get("scopes", ())),
            base_url=payload.get(
                "base_url", "https://api.elsevier.com/content/search/scopus"
            ),
            redirect_port=int(payload.get("redirect_port", 0)),
        )

    def delete(self) -> None:
        self._path.unlink(missing_ok=True)


def configure_scopus_interactively(store: ScopusLocalConfigStore) -> ScopusLocalConfig:
    print("Configuración local de Scopus")
    print("La API key se solicitará de forma oculta y no se mostrará en pantalla.")
    api_key = getpass("Scopus API key: ").strip()
    if not api_key:
        raise ValueError("Scopus API key cannot be empty")

    insttoken = getpass("Institution token (Enter para omitir): ").strip() or None
    client_id = input("OAuth client ID (Enter si no usarás OAuth): ").strip() or None
    client_secret = None
    authorization_endpoint = None
    token_endpoint = None
    scopes: tuple[str, ...] = ()

    if client_id:
        client_secret = (
            getpass("OAuth client secret (Enter si no aplica): ").strip() or None
        )
        authorization_endpoint = input("OAuth authorization endpoint: ").strip() or None
        token_endpoint = input("OAuth token endpoint: ").strip() or None
        if not authorization_endpoint or not token_endpoint:
            raise ValueError(
                "OAuth authorization and token endpoints are required when client ID is set"
            )
        scopes = tuple(
            input("OAuth scopes (separados por espacios, Enter para omitir): ").split()
        )

    config = ScopusLocalConfig(
        api_key=api_key,
        insttoken=insttoken,
        client_id=client_id,
        client_secret=client_secret,
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        scopes=scopes,
    )
    store.save(config)
    return config
