"""
Widget graphique du bloc Séparateur (PATCH 20).

Simple ligne horizontale, sans état ni interaction : reflète fidèlement
le fait que SeparatorBlock ne porte aucune donnée éditable.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from blocks.separator_block import SeparatorBlock


class SeparatorBlockWidget(QWidget):
    """Représentation graphique d'un SeparatorBlock : une ligne horizontale."""

    def __init__(self, block: SeparatorBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    @property
    def block(self) -> SeparatorBlock:
        return self._block
