"""
Notion Lite - Point d'entrée de l'application.
"""
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.themes.theme import apply_theme, detect_system_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Notion Lite")
    apply_theme(app, detect_system_theme())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
