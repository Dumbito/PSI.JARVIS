"""Professional desktop GUI for PSI.JARVIS."""

import sys

from PySide6.QtWidgets import QApplication

from psi_jarvis.gui import app as _app
from psi_jarvis.gui.reports import ReportsPage as _ReportsPage

_app.ReportsPage = _ReportsPage


def main() -> int:
    from psi_jarvis.gui.enhanced import EnhancedMainWindow, install_presentation_patches
    from psi_jarvis.gui.i18n_manager import LanguageManager, install_language_selector
    from psi_jarvis.gui.theme import apply_theme
    from psi_jarvis.gui.tutorial import TutorialDialog

    install_presentation_patches()
    application = QApplication.instance() or QApplication(sys.argv)
    apply_theme(application)

    # One application-wide translation service. Individual pages do not need
    # hand-written translation calls; the manager walks the widget tree.
    language_manager = LanguageManager(application)
    window = EnhancedMainWindow()
    window._language_manager = language_manager
    install_language_selector(window, language_manager)
    window.show()
    TutorialDialog(window).exec()
    return application.exec()


__all__ = ["main"]
