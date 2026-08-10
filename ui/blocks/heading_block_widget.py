"""
Widget graphique des blocs Titre.

Utilise QLineEdit : édition libre sur une seule ligne, avec une
police dont la taille dépend du niveau du titre (H1 > H2 > H3).
"""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit

from blocks.heading_block import HeadingBlock
from ui.settings import get_heading_extra_spacing

# Taille de police par niveau de titre.
_FONT_SIZES = {1: 28, 2: 22, 3: 18}
# Espacement ajouté au-dessus du titre quand l'option est activée (PATCH 49).
_EXTRA_TOP_MARGIN_PX = 22


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

        if get_heading_extra_spacing():
            self.setStyleSheet(f"QLineEdit {{ border: none; margin-top: {_EXTRA_TOP_MARGIN_PX}px; }}")

        self.textChanged.connect(self._on_text_changed)

    @property
    def block(self) -> HeadingBlock:
        return self._block

    def _on_text_changed(self, text: str) -> None:
        """Synchronise le contenu du widget vers le bloc de données."""
        self._block.content = text
