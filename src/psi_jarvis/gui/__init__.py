"""Professional desktop GUI for PSI.JARVIS."""

import sys

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui import app as _app
from psi_jarvis.gui.enhanced import EnhancedMainWindow, install_presentation_patches
from psi_jarvis.gui.reports import ReportsPage as _ReportsPage
from psi_jarvis.gui.theme import apply_theme
from psi_jarvis.gui.tutorial import TutorialDialog

_app.ReportsPage = _ReportsPage
install_presentation_patches()


def main() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    apply_theme(application)
    window = EnhancedMainWindow()
    window.show()
    TutorialDialog(window).exec()
    return application.exec()


__all__ = ["main"]
