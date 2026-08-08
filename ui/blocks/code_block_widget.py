"""
Widget graphique du bloc Code (PATCH 22).

QTextEdit en texte brut, police monospace (Consolas/Courier New selon
la plateforme) et fond légèrement grisé pour se distinguer du texte
normal. La coloration syntaxique n'est pas incluse (amélioration
future prévue par le plan du projet).
"""
from __future__ import annotations

from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QTextEdit

from blocks.code_block import CodeBlock

_MONOSPACE_FAMILY = "Consolas"


class CodeBlockWidget(QTextEdit):
    """Représentation graphique éditable d'un CodeBlock."""

    def __init__(self, block: CodeBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        self.setAcceptRichText(False)
        self.setPlainText(block.content)
        self.setPlaceholderText("// Code...")
        self.setFrameStyle(0)

        font = QFont(_MONOSPACE_FAMILY)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        # Fond/bordure dérivés de la palette courante (claire ou sombre,
        # PATCH 32) plutôt que des couleurs fixes.
        alt_bg = self.palette().color(QPalette.AlternateBase).name()
        border_color = self.palette().color(QPalette.Mid).name()
        self.setStyleSheet(
            f"QTextEdit {{ background-color: {alt_bg}; border: 1px solid {border_color}; padding: 8px; }}"
        )

        self.textChanged.connect(self._on_text_changed)

    @property
    def block(self) -> CodeBlock:
        return self._block

    def _on_text_changed(self) -> None:
        self._block.content = self.toPlainText()
