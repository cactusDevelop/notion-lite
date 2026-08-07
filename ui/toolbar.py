"""
Barre d'outils principale.

PATCH 5 : actions de base (nouveau bloc, mise en forme simple).
La mise en forme complète (barré, alignement, listes, citations,
code) sera ajoutée au PATCH 6.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSpinBox, QToolBar


class MainToolBar(QToolBar):
    """Barre d'outils exposant les actions de base de l'éditeur.

    Les callbacks sont fournis par MainWindow, qui reste responsable
    de savoir sur quel bloc appliquer chaque action.
    """

    def __init__(
        self,
        on_new_block: Callable[[], None],
        on_bold: Callable[[], None],
        on_italic: Callable[[], None],
        on_underline: Callable[[], None],
        on_color: Callable[[], None],
        on_size_changed: Callable[[int], None],
        parent=None,
    ) -> None:
        super().__init__("Barre d'outils", parent)
        self.setMovable(False)

        new_block_action = QAction("Nouveau bloc", self)
        new_block_action.triggered.connect(on_new_block)
        self.addAction(new_block_action)

        self.addSeparator()

        bold_action = QAction("Gras", self)
        bold_action.triggered.connect(on_bold)
        self.addAction(bold_action)

        italic_action = QAction("Italique", self)
        italic_action.triggered.connect(on_italic)
        self.addAction(italic_action)

        underline_action = QAction("Souligné", self)
        underline_action.triggered.connect(on_underline)
        self.addAction(underline_action)

        color_action = QAction("Couleur", self)
        color_action.triggered.connect(on_color)
        self.addAction(color_action)

        self.addSeparator()

        self._size_spin = QSpinBox(self)
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(14)
        self._size_spin.setSuffix(" pt")
        self._size_spin.valueChanged.connect(on_size_changed)
        self.addWidget(self._size_spin)
