from PySide6.QtWidgets import QApplication


STYLE = """
QWidget { background: #0a111c; color: #dce7f5; font-family: Inter, Noto Sans, sans-serif; font-size: 13px; }
QMainWindow { background: #08101a; }
QFrame#sidebar { background: #091522; border-right: 1px solid #1d3044; }
QLabel#brand { color: #f4f8ff; font-size: 19px; font-weight: 700; }
QLabel#version { color: #66809b; font-size: 11px; }
QLabel#tagline { color: #7188a4; font-size: 10px; }
QPushButton#nav { text-align: left; border: 0; border-radius: 8px; padding: 11px 13px; color: #9eb2ca; background: transparent; }
QPushButton#nav:hover { background: #12253a; color: #edf5ff; }
QPushButton#nav[active="true"] { background: #15385d; color: #7fc0ff; }
QLabel#pageTitle { font-size: 27px; font-weight: 700; color: #f1f6fc; }
QLabel#pageSubtitle { color: #8095ad; }
QLabel#dialogTitle { font-size: 20px; font-weight: 700; color: #f1f6fc; padding-bottom: 4px; }
QFrame#card { background: #0f1c2b; border: 1px solid #21374d; border-radius: 10px; }
QLabel#metricValue { font-size: 25px; font-weight: 700; color: #eef6ff; }
QLabel#metricLabel { color: #8da3bb; }
QLabel#metricAccent { color: #61b0ff; font-size: 11px; }
QLabel#sectionTitle { font-size: 15px; font-weight: 600; color: #eaf2fb; }
QProgressBar { background: #17273a; border: 0; border-radius: 6px; height: 12px; text-align: center; color: #dbeafe; }
QProgressBar::chunk { background: #4ba5ff; border-radius: 6px; }
QTableWidget, QListWidget, QTextEdit { background: #0c1826; alternate-background-color: #0f1e2f; border: 1px solid #21374d; gridline-color: #1a2c3f; border-radius: 8px; }
QHeaderView::section { background: #122235; color: #91a8c0; border: 0; padding: 9px; font-weight: 600; }
QTableWidget::item { padding: 7px; }
QTableWidget::item:selected, QListWidget::item:selected { background: #1a426a; color: white; }
QListWidget::item { padding: 12px; border-radius: 6px; }
QPushButton#primary { background: #2685e8; color: white; border: 0; border-radius: 7px; padding: 9px 14px; font-weight: 600; }
QPushButton#primary:hover { background: #3a96f4; }
QPushButton#secondary { background: #13253a; color: #b8c9db; border: 1px solid #29415b; border-radius: 7px; padding: 9px 14px; }
QPushButton#secondary:hover { background: #19304a; }
QLineEdit, QComboBox { background: #0b1725; border: 1px solid #29405a; border-radius: 7px; padding: 8px; color: #dce7f5; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #4b9be8; }
QComboBox QAbstractItemView { background: #0e1a29; color: #dce7f5; selection-background-color: #1a426a; }
QScrollBar:vertical { background: #0a1521; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #29415b; border-radius: 5px; min-height: 30px; }
QStatusBar { background: #08101a; color: #6f879f; border-top: 1px solid #1d3045; }
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
