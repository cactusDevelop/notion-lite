"""
Widget graphique du bloc Texte.

Utilise QTextEdit qui fournit nativement : édition libre, retour
à la ligne, sélection, copier/coller (Ctrl+C / Ctrl+V / clic droit).

Le contenu est conservé au format HTML dans le bloc de données afin
de préserver toute la mise en forme (PATCH 6) : gras, italique,
souligné, barré, couleurs, alignement, listes, citations, code.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QTextCharFormat,
    QTextListFormat,
)
from PySide6.QtWidgets import QTextEdit

from blocks.text_block import TextBlock

_CODE_FONT_FAMILY = "Consolas"
_QUOTE_INDENT = 24


class TextBlockWidget(QTextEdit):
    """Représentation graphique éditable d'un TextBlock."""

    focused = Signal(object)

    def __init__(self, block: TextBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        self.setAcceptRichText(False)
        if block.html:
            self.setHtml(block.html)
        else:
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
        """Synchronise le texte brut et le HTML vers le bloc de données."""
        self._block.content = self.toPlainText()
        self._block.html = self.toHtml()

    # -- Mise en forme caractère ----------------------------------------

    def _merge_char_format(self, fmt: QTextCharFormat) -> None:
        """Applique un format à la sélection, ou au prochain texte tapé."""
        self.mergeCurrentCharFormat(fmt)

    def toggle_bold(self) -> None:
        is_bold = self.currentCharFormat().fontWeight() == QFont.Bold
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Normal if is_bold else QFont.Bold)
        self._merge_char_format(fmt)

    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.currentCharFormat().fontItalic())
        self._merge_char_format(fmt)

    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.currentCharFormat().fontUnderline())
        self._merge_char_format(fmt)

    def toggle_strikethrough(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self.currentCharFormat().fontStrikeOut())
        self._merge_char_format(fmt)

    def toggle_code(self) -> None:
        is_code = self.currentCharFormat().fontFamily() == _CODE_FONT_FAMILY
        fmt = QTextCharFormat()
        fmt.setFontFamily("" if is_code else _CODE_FONT_FAMILY)
        self._merge_char_format(fmt)

    def set_text_color(self, color: QColor) -> None:
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self._merge_char_format(fmt)

    def set_font_size(self, size: int) -> None:
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_char_format(fmt)

    # -- Mise en forme paragraphe -----------------------------------------

    def set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        self.setAlignment(alignment)

    def toggle_quote(self) -> None:
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        is_quote = block_fmt.leftMargin() > 0
        block_fmt.setLeftMargin(0 if is_quote else _QUOTE_INDENT)
        cursor.mergeBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        char_fmt.setFontItalic(not is_quote)
        char_fmt.setForeground(QColor("black") if is_quote else QColor("#555555"))
        self._merge_char_format(char_fmt)

    def _toggle_list(self, style: QTextListFormat.Style) -> None:
        cursor = self.textCursor()
        current_list = cursor.currentList()
        if current_list is not None and current_list.format().style() == style:
            current_list.remove(cursor.block())
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.mergeBlockFormat(block_fmt)
        else:
            list_fmt = QTextListFormat()
            list_fmt.setStyle(style)
            cursor.createList(list_fmt)

    def toggle_bullet_list(self) -> None:
        self._toggle_list(QTextListFormat.ListDisc)

    def toggle_numbered_list(self) -> None:
        self._toggle_list(QTextListFormat.ListDecimal)
