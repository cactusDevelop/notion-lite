"""
Widget graphique du bloc Texte.

Utilise QTextEdit qui fournit nativement : édition libre, retour
à la ligne, sélection, copier/coller (Ctrl+C / Ctrl+V / clic droit).

Expose aussi des méthodes de mise en forme de base pour la toolbar
(PATCH 5). La persistance de cette mise en forme dans les données
du bloc sera traitée au PATCH 6.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import QTextEdit

from blocks.text_block import TextBlock


class TextBlockWidget(QTextEdit):
    """Représentation graphique éditable d'un TextBlock."""

    # Émis quand ce widget prend le focus, avec lui-même en argument.
    focused = Signal(object)

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

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.focused.emit(self)

    def _on_text_changed(self) -> None:
        """Synchronise le contenu du widget vers le bloc de données."""
        self._block.content = self.toPlainText()

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        """Applique un format à la sélection, ou au prochain texte tapé."""
        self.mergeCurrentCharFormat(fmt)

    def toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Normal if self.fontWeight() == QFont.Bold else QFont.Bold)
        self._merge_format(fmt)

    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.fontItalic())
        self._merge_format(fmt)

    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.fontUnderline())
        self._merge_format(fmt)

    def set_text_color(self, color: QColor) -> None:
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self._merge_format(fmt)

    def set_font_size(self, size: int) -> None:
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)
