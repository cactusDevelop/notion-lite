"""
Fenêtre principale de Notion Lite.
"""
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from blocks.heading_block import HeadingBlock
from blocks.text_block import TextBlock
from core.document import Document
from ui.blocks.heading_block_widget import HeadingBlockWidget
from ui.blocks.text_block_widget import TextBlockWidget


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application.

    Affiche pour l'instant le document sous forme d'une simple
    colonne de blocs (PATCH 3 : texte, PATCH 4 : titres). Les
    patches suivants ajouteront la toolbar, le menu "/", etc.
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

        # Blocs de démonstration pour valider les PATCH 3 et 4.
        h1 = HeadingBlock(level=1, content="Titre principal")
        h2 = HeadingBlock(level=2, content="Sous-titre")
        h3 = HeadingBlock(level=3, content="Petit titre")
        text = TextBlock(content="Ceci est un bloc de texte modifiable.")

        for block in (h1, h2, h3, text):
            self._document.add_block(block)

        layout.addWidget(HeadingBlockWidget(h1))
        layout.addWidget(HeadingBlockWidget(h2))
        layout.addWidget(HeadingBlockWidget(h3))
        layout.addWidget(TextBlockWidget(text))

        self.setCentralWidget(central)
