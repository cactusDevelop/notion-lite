"""
Zone de dépôt des blocs (PATCH 13).

Widget central qui accepte le glisser-déposer initié par une
``_DragHandle`` (voir ``block_container.py``) et calcule la position
d'insertion à partir de la coordonnée Y du curseur au relâchement.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.blocks.block_container import BLOCK_MIME_TYPE


class BlocksArea(QWidget):
    """Conteneur vertical des blocs du document, cible du drag & drop."""

    def __init__(
        self,
        on_block_dropped: Callable[[str, int], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.blocks_layout = QVBoxLayout(self)
        self._on_block_dropped = on_block_dropped

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(BLOCK_MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if not mime.hasFormat(BLOCK_MIME_TYPE):
            return
        block_id = bytes(mime.data(BLOCK_MIME_TYPE)).decode("utf-8")
        target_index = self._index_for_y(event.position().y())
        event.acceptProposedAction()
        self._on_block_dropped(block_id, target_index)

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
