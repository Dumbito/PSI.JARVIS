import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> int:
    """Ejecuta un comando y devuelve su código de salida."""
    return subprocess.run(command).returncode


def doctor() -> int:
    """Ejecuta una revisión básica de salud del proyecto."""
    print("PSI.JARVIS DOCTOR")
    print("────────────────────────────────")
    print()

    checks = []

    # Python
    python_ok = sys.version_info >= (3, 12)
    checks.append(("Python >= 3.12", python_ok))

    # Entorno virtual
    venv_ok = sys.prefix != sys.base_prefix
    checks.append(("Entorno virtual", venv_ok))

    # Estructura
    required_paths = [
        Path("pyproject.toml"),
        Path("src/psi_jarvis"),
        Path("tests"),
    ]

    structure_ok = all(path.exists() for path in required_paths)
    checks.append(("Estructura del proyecto", structure_ok))

    # Importación
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

    # Tests
    print("Ejecutando tests...")
    print()

    tests_ok = run_command(
        [sys.executable, "-m", "pytest", "-q"]
    ) == 0

    checks.append(("Tests", tests_ok))
    print()

    # Git
    git_repo_ok = run_command(
        ["git", "rev-parse", "--is-inside-work-tree"]
    ) == 0

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

    # Resultado
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
        return 0

    command = sys.argv[1]

    if command == "test":
        return run_command(
            [sys.executable, "-m", "pytest", "-v"]
        )

    if command == "status":
        return run_command(["git", "status"])

    if command == "check":
        result = run_command(
            [sys.executable, "-m", "pytest", "-v"]
        )

        if result != 0:
            return result

        print()
        print("===== GIT STATUS =====")
        return run_command(["git", "status"])

    if command == "doctor":
        return doctor()

    print(f"Comando desconocido: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
