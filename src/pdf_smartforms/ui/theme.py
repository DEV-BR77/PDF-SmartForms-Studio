"""Accessible application theme."""


def application_stylesheet() -> str:
    """Return a calm, high-contrast light theme."""
    return """
        QWidget {
            color: #172033;
            background: #f4f7fb;
            font-family: "Segoe UI";
            font-size: 10.5pt;
        }
        QMainWindow { background: #f4f7fb; }
        QFrame#hero {
            background: #ffffff;
            border: 1px solid #dfe6f0;
            border-radius: 18px;
        }
        QLabel#eyebrow { color: #3366cc; font-weight: 700; }
        QLabel#title { font-size: 24pt; font-weight: 700; color: #111827; }
        QLabel#subtitle { color: #5b6474; font-size: 11pt; }
        QPushButton {
            min-height: 42px;
            padding: 4px 18px;
            border-radius: 10px;
            border: 1px solid #ccd6e4;
            background: #ffffff;
            font-weight: 600;
        }
        QPushButton:hover { border-color: #4778df; background: #f3f7ff; }
        QPushButton:focus { border: 2px solid #235dcc; }
        QPushButton#primary {
            color: white;
            background: #235dcc;
            border-color: #235dcc;
        }
        QPushButton#primary:hover { background: #194cae; }
        QStatusBar { background: #ffffff; border-top: 1px solid #dfe6f0; }
    """
