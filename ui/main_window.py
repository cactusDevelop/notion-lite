"""
Fenêtre principale de Notion Lite.
"""
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from blocks.text_block import TextBlock
from core.document import Document
from ui.blocks.text_block_widget import TextBlockWidget


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application.

    Affiche pour l'instant le document sous forme d'une simple
    colonne de blocs (PATCH 3 : bloc texte). Les patches suivants
    ajouteront la toolbar, le menu "/", le drag & drop, etc.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Notion Lite")
        self.resize(1000, 700)

        self._document = Document()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Prépare les composants de l'interface et affiche le document."""
        central = QWidget()
        layout = QVBoxLayout(central)

        # Bloc de démonstration pour valider le PATCH 3.
        block = TextBlock(content="Ceci est un bloc de texte modifiable.")
        self._document.add_block(block)
        layout.addWidget(TextBlockWidget(block))

        self.setCentralWidget(central)
