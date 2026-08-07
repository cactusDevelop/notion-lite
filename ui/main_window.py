"""
Fenêtre principale de Notion Lite.
"""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QMainWindow, QVBoxLayout, QWidget

from blocks.heading_block import HeadingBlock
from blocks.text_block import TextBlock
from core.document import Document
from ui.blocks.heading_block_widget import HeadingBlockWidget
from ui.blocks.text_block_widget import TextBlockWidget
from ui.toolbar import MainToolBar


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application.

    Affiche le document sous forme d'une colonne de blocs et
    expose une toolbar (PATCH 5) pour la mise en forme de base.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Notion Lite")
        self.resize(1000, 700)

        self._document = Document()
        self._active_text_widget: TextBlockWidget | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Prépare la toolbar, la zone de contenu et affiche le document."""
        toolbar = MainToolBar(
            on_new_block=self._add_text_block,
            on_bold=self._apply_bold,
            on_italic=self._apply_italic,
            on_underline=self._apply_underline,
            on_color=self._apply_color,
            on_size_changed=self._apply_size,
        )
        self.addToolBar(toolbar)

        central = QWidget()
        self._blocks_layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        # Blocs de démonstration pour valider les PATCH 3 et 4.
        h1 = HeadingBlock(level=1, content="Titre principal")
        h2 = HeadingBlock(level=2, content="Sous-titre")
        h3 = HeadingBlock(level=3, content="Petit titre")

        for block in (h1, h2, h3):
            self._document.add_block(block)
            self._blocks_layout.addWidget(HeadingBlockWidget(block))

        self._add_text_block(content="Ceci est un bloc de texte modifiable.")

    def _add_text_block(self, content: str = "") -> None:
        """Ajoute un nouveau bloc texte au document et à l'affichage."""
        block = TextBlock(content=content)
        self._document.add_block(block)

        widget = TextBlockWidget(block)
        widget.focused.connect(self._on_text_widget_focused)
        self._blocks_layout.addWidget(widget)

        widget.setFocus()

    def _on_text_widget_focused(self, widget: TextBlockWidget) -> None:
        self._active_text_widget = widget

    def _apply_bold(self) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.toggle_bold()

    def _apply_italic(self) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.toggle_italic()

    def _apply_underline(self) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.toggle_underline()

    def _apply_color(self) -> None:
        if self._active_text_widget is None:
            return
        color = QColorDialog.getColor(QColor("black"), self, "Choisir une couleur")
        if color.isValid():
            self._active_text_widget.set_text_color(color)

    def _apply_size(self, size: int) -> None:
        if self._active_text_widget is not None:
            self._active_text_widget.set_font_size(size)
