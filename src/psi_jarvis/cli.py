import os
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> int:
    """Ejecuta un comando y devuelve su código de salida."""
    return subprocess.run(command).returncode


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
        oauth_client=ScopusOAuthClient(config.oauth) if config.oauth is not None else None,
    )


def scopus_status() -> int:
    manager = _scopus_manager_from_environment()
    connection = manager.inspect()
    labels = {
        "unconfigured": "No configurado",
        "disconnected": "Desconectado",
        "connected": "Conectado",
        "expired": "Sesión expirada",
    }
    print(f"Scopus: {labels[connection.status.value]}")
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

    if command == "scopus":
        if len(sys.argv) < 3:
            print("Uso: psi scopus {status|login|logout}")
            return 1
        subcommand = sys.argv[2]
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
