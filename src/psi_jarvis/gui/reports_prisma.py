from __future__ import annotations

from psi_jarvis.gui.prisma_panel import PrismaReportPanel


def install_prisma_reports(app_module) -> None:
    """Attach the PRISMA panel to ReportsPage without changing report semantics."""
    reports_page = app_module.ReportsPage
    original_init = reports_page.__init__
    if getattr(reports_page, "_prisma_installed", False):
        return

    def init_with_prisma(self, data, workflow):
        original_init(self, data, workflow)
        panel = PrismaReportPanel(data, self)
        self.layout().insertWidget(max(0, self.layout().count() - 1), panel)
        self.prisma_panel = panel

    reports_page.__init__ = init_with_prisma
    reports_page._prisma_installed = True
