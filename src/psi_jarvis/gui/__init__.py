"""Professional desktop GUI for PSI.JARVIS."""

from psi_jarvis.gui import app as _app
from psi_jarvis.gui.reports import ReportsPage as _ReportsPage

_app.ReportsPage = _ReportsPage


def main() -> int:
    return _app.main()


__all__ = ["main"]
