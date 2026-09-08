from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import secrets
import threading
import webbrowser
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from psi_jarvis.infrastructure.acquisition.remote_base import read_remote_response

DEFAULT_REDIRECT_HOST = "127.0.0.1"
DEFAULT_REDIRECT_PATH = "/oauth/callback"
DEFAULT_TIMEOUT_SECONDS = 20.0
MAX_OAUTH_TOKEN_RESPONSE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ScopusOAuthConfig:
    """Configuración OAuth de Scopus suministrada por una app habilitada por Elsevier."""

    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    client_secret: str | None = None
    scopes: tuple[str, ...] = ()
    redirect_host: str = DEFAULT_REDIRECT_HOST
    redirect_port: int = 0
    redirect_path: str = DEFAULT_REDIRECT_PATH
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        for field_name in (
            "client_id",
            "authorization_endpoint",
            "token_endpoint",
            "redirect_host",
            "redirect_path",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"Scopus OAuth {field_name} cannot be empty")
        if not _is_loopback_host(self.redirect_host):
            raise ValueError(
                "Scopus OAuth redirect host must be loopback (127.0.0.1 or ::1)"
            )
        if not 0 <= self.redirect_port <= 65535:
            raise ValueError("Scopus OAuth redirect port must be between 0 and 65535")
        if not self.redirect_path.startswith("/"):
            raise ValueError("Scopus OAuth redirect path must start with '/'")
        if self.timeout_seconds <= 0:
            raise ValueError("Scopus OAuth timeout must be positive")


@dataclass(frozen=True)
class ScopusOAuthToken:
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    refresh_token: str | None = None
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(UTC)


class JsonTokenStore:
    """Almacén local mínimo con permisos de propietario para un token OAuth."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, token: ScopusOAuthToken) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.parent.chmod(0o700)
        payload = {
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "refresh_token": token.refresh_token,
            "scope": token.scope,
        }
        temporary = self._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(self._path)
        self._path.chmod(0o600)

    def load(self) -> ScopusOAuthToken | None:
        if not self._path.exists():
            return None
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        expires_at = payload.get("expires_at")
        return ScopusOAuthToken(
            access_token=payload["access_token"],
            token_type=payload.get("token_type", "Bearer"),
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            refresh_token=payload.get("refresh_token"),
            scope=payload.get("scope"),
        )

    def delete(self) -> None:
        self._path.unlink(missing_ok=True)


@dataclass(frozen=True)
class OAuthAuthorizationRequest:
    authorization_url: str
    state: str
    code_verifier: str
    redirect_uri: str


class ScopusOAuthClient:
    """Cliente OAuth 2.0 con PKCE y callback loopback para aplicaciones de escritorio."""

    def __init__(
        self,
        config: ScopusOAuthConfig,
        *,
        opener: Callable[..., object] | None = None,
        browser_opener: Callable[[str], object] | None = None,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen
        self._browser_opener = browser_opener or webbrowser.open

    def prepare_authorization(self) -> OAuthAuthorizationRequest:
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        challenge = _pkce_challenge(code_verifier)
        redirect_uri = self._redirect_uri(self._config.redirect_port)
        params = {
            "response_type": "code",
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        if self._config.scopes:
            params["scope"] = " ".join(self._config.scopes)
        return OAuthAuthorizationRequest(
            authorization_url=f"{self._config.authorization_endpoint}?{urlencode(params)}",
            state=state,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
        )

    def build_authorization_url(self, request: OAuthAuthorizationRequest) -> str:
        return request.authorization_url

    def exchange_code(
        self, code: str, request: OAuthAuthorizationRequest
    ) -> ScopusOAuthToken:
        if not code.strip():
            raise ValueError("Scopus OAuth authorization code cannot be empty")
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": request.redirect_uri,
            "client_id": self._config.client_id,
            "code_verifier": request.code_verifier,
        }
        if self._config.client_secret:
            payload["client_secret"] = self._config.client_secret
        return self._token_request(payload)

    def refresh_token(self, refresh_token: str) -> ScopusOAuthToken:
        if not refresh_token.strip():
            raise ValueError("Scopus OAuth refresh token cannot be empty")
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
        }
        if self._config.client_secret:
            payload["client_secret"] = self._config.client_secret
        return self._token_request(payload)

    def login(self, timeout_seconds: float = 300.0) -> ScopusOAuthToken:
        authorization = self.prepare_authorization()
        callback = _LoopbackCallbackServer(
            host=self._config.redirect_host,
            port=self._config.redirect_port,
            path=self._config.redirect_path,
            expected_state=authorization.state,
        )
        callback.start()
        bound_redirect_uri = self._redirect_uri(callback.port)
        authorization = OAuthAuthorizationRequest(
            authorization_url=self._replace_redirect_uri(
                authorization.authorization_url, bound_redirect_uri
            ),
            state=authorization.state,
            code_verifier=authorization.code_verifier,
            redirect_uri=bound_redirect_uri,
        )
        self._browser_opener(authorization.authorization_url)
        callback.wait(timeout_seconds)
        if callback.error:
            raise RuntimeError(f"Scopus OAuth authorization failed: {callback.error}")
        if not callback.code:
            raise TimeoutError(
                "Scopus OAuth callback did not return an authorization code"
            )
        return self.exchange_code(callback.code, authorization)

    def _token_request(self, payload: Mapping[str, str]) -> ScopusOAuthToken:
        http_request = Request(
            self._config.token_endpoint,
            data=urlencode(dict(payload)).encode("utf-8"),
            method="POST",
        )
        http_request.add_header("Accept", "application/json")
        http_request.add_header("Content-Type", "application/x-www-form-urlencoded")
        with self._opener(
            http_request, timeout=self._config.timeout_seconds
        ) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(
                    f"Scopus OAuth token endpoint returned HTTP {status}"
                )
            raw = read_remote_response(
                response, max_bytes=MAX_OAUTH_TOKEN_RESPONSE_BYTES
            ).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid Scopus OAuth token JSON: {exc}") from exc
        access_token = str(payload.get("access_token", "")).strip()
        if not access_token:
            raise RuntimeError("Scopus OAuth token response has no access_token")
        expires_at = None
        if payload.get("expires_in") is not None:
            expires_at = datetime.now(UTC) + timedelta(
                seconds=int(payload["expires_in"])
            )
        return ScopusOAuthToken(
            access_token=access_token,
            token_type=str(payload.get("token_type", "Bearer")),
            expires_at=expires_at,
            refresh_token=payload.get("refresh_token"),
            scope=payload.get("scope"),
        )

    def _redirect_uri(self, port: int) -> str:
        host = self._config.redirect_host
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"http://{host}:{port}{self._config.redirect_path}"

    @staticmethod
    def _replace_redirect_uri(url: str, redirect_uri: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params["redirect_uri"] = [redirect_uri]
        query = urlencode(params, doseq=True)
        return parsed._replace(query=query).geturl()


class _LoopbackCallbackServer:
    def __init__(self, host: str, port: int, path: str, expected_state: str) -> None:
        self._expected_state = expected_state
        self._path = path
        self._server = _CallbackHTTPServer((host, port), self)
        self.code: str | None = None
        self.error: str | None = None
        self.port = self._server.server_port
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def wait(self, timeout_seconds: float) -> None:
        if self._thread is not None:
            self._thread.join(timeout_seconds)
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1)

    def handle(self, path: str) -> tuple[int, str]:
        parsed = urlparse(path)
        if parsed.path != self._path:
            return 404, "Not found"
        params = parse_qs(parsed.query)
        state = params.get("state", [""])[0]
        self.error = params.get("error", [None])[0]
        if state != self._expected_state:
            self.error = "OAuth state mismatch"
            return 400, "Authorization rejected"
        self.code = params.get("code", [None])[0]
        if not self.code and not self.error:
            self.error = "Missing authorization code"
            return 400, "Authorization rejected"
        return (
            200,
            "PSI.JARVIS: Scopus authorization received. You can close this window.",
        )


class _CallbackHTTPServer(HTTPServer):
    def __init__(self, server_address, callback: _LoopbackCallbackServer) -> None:
        self.callback = callback
        super().__init__(server_address, _CallbackHandler)


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status, body = self.server.callback.handle(self.path)
        body_bytes = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def log_message(self, format: str, *args) -> None:
        return


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def default_scopus_token_store(home: Path | None = None) -> JsonTokenStore:
    base = home or Path.home()
    return JsonTokenStore(
        base / ".config" / "psi-jarvis" / "connections" / "scopus.json"
    )
