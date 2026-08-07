"""
Widget graphique des blocs Titre.

Utilise QLineEdit : édition libre sur une seule ligne, avec une
police dont la taille dépend du niveau du titre (H1 > H2 > H3).
"""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit

from blocks.heading_block import HeadingBlock

# Taille de police par niveau de titre.
_FONT_SIZES = {1: 28, 2: 22, 3: 18}


class HeadingBlockWidget(QLineEdit):
    """Représentation graphique éditable d'un HeadingBlock."""

    def __init__(self, block: HeadingBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        self.setText(block.content)
        self.setPlaceholderText(f"Titre {block.level}")
        self.setFrame(False)

        font = QFont()
        font.setPointSize(_FONT_SIZES.get(block.level, 16))
        font.setBold(True)
        self.setFont(font)

        self.textChanged.connect(self._on_text_changed)

    @property
    def block(self) -> HeadingBlock:
        return self._block

    def _on_text_changed(self, text: str) -> None:
        """Synchronise le contenu du widget vers le bloc de données."""
        self._block.content = text
