from PySide6.QtWidgets import QApplication


STYLE = """
QWidget {
    background: #0b1320;
    color: #dce7f5;
    font-family: Inter, Noto Sans, sans-serif;
    font-size: 13px;
}
QMainWindow { background: #08111d; }
QFrame#sidebar {
    background: #0a1625;
    border-right: 1px solid #203248;
}
QLabel#brand { color: #f4f8ff; font-size: 19px; font-weight: 700; }
QLabel#version { color: #6e849e; font-size: 11px; }
QLabel#tagline { color: #7188a4; font-size: 10px; }
QPushButton#nav {
    text-align: left;
    border: 0;
    border-radius: 8px;
    padding: 11px 13px;
    color: #9eb2ca;
    background: transparent;
}
QPushButton#nav:hover { background: #13243a; color: #e8f1fc; }
QPushButton#nav[active="true"] { background: #16365b; color: #73b6ff; }
QLabel#pageTitle { font-size: 27px; font-weight: 700; color: #f1f6fc; }
QLabel#pageSubtitle { color: #8095ad; }
QFrame#card {
    background: #101d2d;
    border: 1px solid #22364d;
    border-radius: 10px;
}
QLabel#metricValue { font-size: 25px; font-weight: 700; color: #eef6ff; }
QLabel#metricLabel { color: #8da3bb; }
QLabel#metricAccent { color: #61b0ff; font-size: 11px; }
QLabel#sectionTitle { font-size: 15px; font-weight: 600; color: #eaf2fb; }
QProgressBar {
    background: #1a2a3d;
    border: 0;
    border-radius: 6px;
    height: 10px;
}
QProgressBar::chunk { background: #4ba5ff; border-radius: 6px; }
QTableWidget {
    background: #0e1a29;
    alternate-background-color: #101f31;
    border: 1px solid #22364d;
    gridline-color: #1c2d40;
    border-radius: 8px;
}
QHeaderView::section {
    background: #132235;
    color: #8fa6bf;
    border: 0;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #1a4168; color: white; }
QPushButton#primary {
    background: #2685e8;
    color: white;
    border: 0;
    border-radius: 7px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton#primary:hover { background: #3a96f4; }
QPushButton#secondary {
    background: #14253a;
    color: #b8c9db;
    border: 1px solid #29415b;
    border-radius: 7px;
    padding: 9px 14px;
}
QLineEdit, QComboBox {
    background: #0d1a29;
    border: 1px solid #29405a;
    border-radius: 7px;
    padding: 8px;
    color: #dce7f5;
}
QScrollArea { border: 0; }
QStatusBar { background: #08111d; color: #6f879f; border-top: 1px solid #1d3045; }
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
