"""
Widget graphique du bloc Citation (PATCH 21).

QTextEdit en texte brut, avec une mise en forme dédiée (barre
verticale à gauche, italique, gris) pour se distinguer visuellement
d'un TextBlock ordinaire.
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QTextEdit

from blocks.quote_block import QuoteBlock


class QuoteBlockWidget(QTextEdit):
    """Représentation graphique éditable d'un QuoteBlock."""

    def __init__(self, block: QuoteBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        self.setAcceptRichText(False)
        self.setPlainText(block.content)
        self.setPlaceholderText("Citation...")
        self.setFrameStyle(0)

        font = QFont()
        font.setItalic(True)
        self.setFont(font)
        # Barre verticale dérivée de la palette courante (claire ou sombre,
        # PATCH 32) plutôt qu'une couleur fixe, pour rester lisible dans
        # les deux thèmes.
        border_color = self.palette().color(QPalette.Mid).name()
        self.setStyleSheet(f"QTextEdit {{ border-left: 3px solid {border_color}; padding-left: 10px; }}")

        self.textChanged.connect(self._on_text_changed)

    @property
    def block(self) -> QuoteBlock:
        return self._block

    def _on_text_changed(self) -> None:
        self._block.content = self.toPlainText()
