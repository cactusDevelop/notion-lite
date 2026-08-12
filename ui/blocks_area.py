"""
Zone de dépôt des blocs (PATCH 13), clic droit sur zone vide (PATCH 26).

Widget central qui accepte le glisser-déposer initié par une
``_DragHandle`` (voir ``block_container.py``) et calcule la position
d'insertion à partir de la coordonnée Y du curseur au relâchement.
Le clic droit sur une zone vide (sous le dernier bloc) délègue à la
fenêtre principale, qui propose d'y ajouter un nouveau bloc.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QPoint
from PySide6.QtGui import QContextMenuEvent, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget

from ui.blocks.block_container import BLOCK_MIME_TYPE
from ui.themes.theme import THEME_DARK, current_theme


class BlocksArea(QWidget):
    """Conteneur vertical des blocs du document, cible du drag & drop."""

    def __init__(
        self,
        on_block_dropped: Callable[[str, int], None],
        on_empty_context_menu: Optional[Callable[[QPoint], None]] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.blocks_layout = QVBoxLayout(self)
        self._on_block_dropped = on_block_dropped
        self._on_empty_context_menu = on_empty_context_menu

        # PATCH 62 — indicateur d'insertion : une fine ligne (blanche en
        # thème sombre, noire sinon) affichée pendant le survol du
        # glisser-déposer, à la position où le bloc sera inséré si
        # l'utilisateur relâche le clic. Widget flottant (hors layout)
        # pour ne pas perturber la disposition des blocs pendant le survol.
        self._drop_indicator = QFrame(self)
        self._drop_indicator.setFixedHeight(3)
        self._drop_indicator.hide()

    def _drop_indicator_color(self) -> str:
        """Blanc en thème sombre, noir sinon (PATCH 62)."""
        return "#ffffff" if current_theme(QApplication.instance()) == THEME_DARK else "#000000"

    def _show_drop_indicator(self, target_index: int) -> None:
        self._drop_indicator.setStyleSheet(f"background-color: {self._drop_indicator_color()};")
        margin = 4
        self._drop_indicator.setGeometry(
            margin, self._y_for_index(target_index) - 1, max(self.width() - 2 * margin, 0), 3
        )
        self._drop_indicator.show()
        self._drop_indicator.raise_()

    def _hide_drop_indicator(self) -> None:
        self._drop_indicator.hide()

    def _y_for_index(self, index: int) -> int:
        """Coordonnée Y (haut du bloc visé, ou bas du dernier bloc en
        fin de document) où positionner l'indicateur d'insertion."""
        count = self.blocks_layout.count()
        if count == 0:
            return 0
        if 0 <= index < count:
            widget = self.blocks_layout.itemAt(index).widget()
            if widget is not None:
                return widget.geometry().y()
        last_widget = self.blocks_layout.itemAt(count - 1).widget()
        if last_widget is not None:
            return last_widget.geometry().y() + last_widget.geometry().height()
        return 0

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()
            self._show_drop_indicator(self._index_for_y(event.position().y()))

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._hide_drop_indicator()

    def dropEvent(self, event: QDropEvent) -> None:
        self._hide_drop_indicator()
        mime = event.mimeData()
        if not mime.hasFormat(BLOCK_MIME_TYPE):
            return
        block_id = bytes(mime.data(BLOCK_MIME_TYPE)).decode("utf-8")
        target_index = self._index_for_y(event.position().y())
        event.acceptProposedAction()
        self._on_block_dropped(block_id, target_index)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """PATCH 26 — Clic droit sur une zone vide : propose d'ajouter un bloc.

        N'est déclenché que si le clic n'est tombé sur aucun bloc
        (chaque BlockContainer intercepte déjà son propre clic droit).
        """
        if self._on_empty_context_menu is not None:
            self._on_empty_context_menu(event.globalPos())
            event.accept()

    def _index_for_y(self, y: float) -> int:
        """Index d'insertion : juste avant le premier bloc dont le
        milieu se trouve sous la position Y du dépôt."""
        for i in range(self.blocks_layout.count()):
            item = self.blocks_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget is None:
                continue
            mid_y = widget.geometry().y() + widget.geometry().height() / 2
            if y < mid_y:
                return i
        return self.blocks_layout.count()
