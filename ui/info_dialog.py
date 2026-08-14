"""
Popup d'information : explications et choix de design du projet.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from ui.design_notes import get_design_notes
from ui.i18n import tr
from core.version import __version__


class InfoDialog(QDialog):
    """Fenêtre modale listant les choix de design faits jusqu'ici."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("info.title"))
        self.resize(520, 420)

        layout = QVBoxLayout(self)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(False)
        browser.setHtml(self._build_html())
        layout.addWidget(browser)

    @staticmethod
    def _build_html() -> str:
        parts = [
            f"<h3>{tr('info.heading')} {__version__}</h3>",
            f"<h4>{tr('info.subheading')}</h4>",
        ]
        for title, text in get_design_notes():
            parts.append(f"<p><b>{title}</b><br>{text}</p>")
        return "".join(parts)
