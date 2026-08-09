"""
Popup d'information : explications et choix de design du projet.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from ui.design_notes import DESIGN_NOTES
from core.version import __version__


class InfoDialog(QDialog):
    """Fenêtre modale listant les choix de design faits jusqu'ici."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("À propos de ce projet")
        self.resize(520, 420)

        layout = QVBoxLayout(self)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(False)
        browser.setHtml(self._build_html())
        layout.addWidget(browser)

    @staticmethod
    def _build_html() -> str:
        parts = [f"<h3>Notion Lite {__version__}</h3>", "<h4>Explications et choix de design</h4>"]
        for title, text in DESIGN_NOTES:
            parts.append(f"<p><b>{title}</b><br>{text}</p>")
        return "".join(parts)
