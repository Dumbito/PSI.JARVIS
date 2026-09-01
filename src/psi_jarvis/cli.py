import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print("PSI.JARVIS CLI")
        print("Uso: psi test | psi status | psi check")
        return 0
    command = sys.argv[1]
    if command == "test":
        return subprocess.run([sys.executable, "-m", "pytest", "-v"]).returncode
    if command == "status":
        return subprocess.run(["git", "status"]).returncode
    if command == "check":
        result = subprocess.run([sys.executable, "-m", "pytest", "-v"])
        if result.returncode != 0:
            return result.returncode
        print()
        print("===== GIT STATUS =====")
        return subprocess.run(["git", "status"]).returncode
    print(f"Comando desconocido: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
