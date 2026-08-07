"""
Widget graphique du bloc Texte.

Utilise QTextEdit qui fournit nativement : édition libre, retour
à la ligne, sélection, copier/coller (Ctrl+C / Ctrl+V / clic droit).
"""
from __future__ import annotations

from PySide6.QtWidgets import QTextEdit

from blocks.text_block import TextBlock


class TextBlockWidget(QTextEdit):
    """Représentation graphique éditable d'un TextBlock.

    Toute modification du texte est répercutée immédiatement dans
    le bloc de données associé (le document reste la source de vérité).
    """

    def __init__(self, block: TextBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        self.setAcceptRichText(False)
        self.setPlainText(block.content)
        self.setPlaceholderText("Tapez du texte...")
        self.setFrameStyle(0)

        self.textChanged.connect(self._on_text_changed)

    @property
    def block(self) -> TextBlock:
        return self._block

    def _on_text_changed(self) -> None:
        """Synchronise le contenu du widget vers le bloc de données."""
        self._block.content = self.toPlainText()
