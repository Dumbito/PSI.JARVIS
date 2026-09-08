import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> int:
    """Ejecuta un comando y devuelve su código de salida."""
    return subprocess.run(command, check=False).returncode


def _scopus_manager_from_environment():
    from psi_jarvis.infrastructure.auth import (
        ScopusConnectionManager,
        ScopusOAuthClient,
        default_scopus_token_store,
        load_scopus_environment,
    )

    config = load_scopus_environment()
    return ScopusConnectionManager(
        config.oauth,
        default_scopus_token_store(),
        oauth_client=ScopusOAuthClient(config.oauth)
        if config.oauth is not None
        else None,
        transport_config=config.transport,
    )


def _source_registry_from_environment():
    from psi_jarvis.infrastructure.connections import (
        build_default_source_connection_registry,
    )

    return build_default_source_connection_registry(_scopus_manager_from_environment())


def scopus_configure() -> int:
    from psi_jarvis.infrastructure.auth.scopus_local_config import (
        ScopusLocalConfigStore,
        configure_scopus_interactively,
    )

    try:
        configure_scopus_interactively(ScopusLocalConfigStore())
    except Exception as exc:
        print(f"No se pudo guardar la configuración de Scopus: {exc}")
        return 1
    print("Scopus: configuración local guardada")
    print("Ejecuta 'psi scopus status' para comprobar el estado.")
    return 0


def scopus_status() -> int:
    state = _source_registry_from_environment().inspect("scopus")
    labels = {
        "unavailable": "No disponible",
        "configured": "Configurado (sin verificar acceso)",
        "auth_required": "Requiere autenticación",
        "auth_expired": "Sesión expirada",
        "access_limited": "Acceso limitado",
        "available": "Disponible",
        "error": "Error",
    }
    print(f"Scopus: {labels[state.status.value]}")
    if state.credential_method.value != "none":
        print(f"Método: {state.credential_method.value}")
    if state.detail:
        print(f"Detalle: {state.detail}")
    return 0


def sources_status() -> int:
    registry = _source_registry_from_environment()
    for state in registry.inspect_all():
        labels = {
            "unavailable": "NO DISPONIBLE",
            "configured": "CONFIGURADO",
            "auth_required": "REQUIERE AUTENTICACIÓN",
            "auth_expired": "SESIÓN EXPIRADA",
            "access_limited": "ACCESO LIMITADO",
            "available": "DISPONIBLE",
            "error": "ERROR",
        }
        print(f"{state.source.display_name}: {labels[state.status.value]}")
    return 0


def scopus_login() -> int:
    manager = _scopus_manager_from_environment()
    try:
        connection = manager.login()
    except Exception as exc:
        print(f"No se pudo conectar con Scopus: {exc}")
        return 1
    print(f"Scopus: {connection.status.value}")
    return 0


def scopus_logout() -> int:
    manager = _scopus_manager_from_environment()
    manager.logout()
    print("Scopus: sesión local eliminada")
    return 0


def doctor() -> int:
    """Ejecuta una revisión básica de salud del proyecto."""
    print("PSI.JARVIS DOCTOR")
    print("────────────────────────────────")
    print()

    checks = []

    python_ok = sys.version_info >= (3, 12)
    checks.append(("Python >= 3.12", python_ok))

    venv_ok = sys.prefix != sys.base_prefix
    checks.append(("Entorno virtual", venv_ok))

    required_paths = [
        Path("pyproject.toml"),
        Path("src/psi_jarvis"),
        Path("tests"),
    ]
    structure_ok = all(path.exists() for path in required_paths)
    checks.append(("Estructura del proyecto", structure_ok))

    try:
        from psi_jarvis.core import Result, Settings
        from psi_jarvis.domain import Paper
        from psi_jarvis.domain.screening import (
            ScreeningDecision,
            ScreeningEngine,
            ScreeningResult,
        )

        _ = (
            Result,
            Settings,
            Paper,
            ScreeningDecision,
            ScreeningEngine,
            ScreeningResult,
        )
        imports_ok = True
    except Exception:
        imports_ok = False

    checks.append(("Importaciones", imports_ok))

    print("Ejecutando tests...")
    print()
    tests_ok = run_command([sys.executable, "-m", "pytest", "-q"]) == 0
    checks.append(("Tests", tests_ok))
    print()

    git_repo_ok = run_command(["git", "rev-parse", "--is-inside-work-tree"]) == 0

    if git_repo_ok:
        git_status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        git_clean = git_status.returncode == 0 and not git_status.stdout.strip()
    else:
        git_clean = False

    checks.append(("Git repository", git_repo_ok))
    checks.append(("Git working tree clean", git_clean))

    print("===== DIAGNÓSTICO =====")
    print()
    for name, ok in checks:
        symbol = "✓" if ok else "✗"
        print(f"{symbol} {name}")
    print()

    if all(ok for _, ok in checks):
        print("RESULTADO: SISTEMA SALUDABLE")
        return 0

    print("RESULTADO: SE DETECTARON PROBLEMAS")
    return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("PSI.JARVIS CLI")
        print()
        print("Uso:")
        print("  psi test")
        print("  psi status")
        print("  psi check")
        print("  psi doctor")
        print("  psi sources status")
        print("  psi scopus configure")
        print("  psi scopus status")
        print("  psi scopus login")
        print("  psi scopus logout")
        return 0

    command = sys.argv[1]

    if command == "test":
        return run_command([sys.executable, "-m", "pytest", "-v"])

    if command == "status":
        return run_command(["git", "status"])

    if command == "check":
        result = run_command([sys.executable, "-m", "pytest", "-v"])
        if result != 0:
            return result
        print()
        print("===== GIT STATUS =====")
        return run_command(["git", "status"])

    if command == "doctor":
        return doctor()

    if command == "sources":
        if len(sys.argv) < 3 or sys.argv[2] != "status":
            print("Uso: psi sources status")
            return 1
        return sources_status()

    if command == "scopus":
        if len(sys.argv) < 3:
            print("Uso: psi scopus {configure|status|login|logout}")
            return 1
        subcommand = sys.argv[2]
        if subcommand == "configure":
            return scopus_configure()
        if subcommand == "status":
            return scopus_status()
        if subcommand == "login":
            return scopus_login()
        if subcommand == "logout":
            return scopus_logout()

    print(f"Comando desconocido: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
