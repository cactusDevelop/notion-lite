"""
Conteneur générique de bloc (PATCH 13).

Ajoute une poignée de glisser-déposer (« ⠿ ») à gauche de n'importe
quel widget de bloc, pour permettre de réordonner tous les types de
blocs (texte, titres, checklists, images, tableaux à venir...) de la
même façon dans le document.
"""
from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

# Type MIME privé transportant l'ID du bloc glissé.
BLOCK_MIME_TYPE = "application/x-notion-lite-block-id"


class _DragHandle(QLabel):
    """Poignée : point de départ du glisser-déposer d'un bloc."""

    def __init__(self, block_id: str, parent: QWidget | None = None) -> None:
        super().__init__("⠿", parent)
        self._block_id = block_id
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedWidth(18)
        self.setAlignment(Qt.AlignCenter)
        self._drag_start: QPoint | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is None or not (event.buttons() & Qt.LeftButton):
            return
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 10:
            return  # en dessous du seuil : pas encore un vrai glisser

        mime_data = QMimeData()
        mime_data.setData(BLOCK_MIME_TYPE, self._block_id.encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)
        self._drag_start = None


class BlockContainer(QWidget):
    """Enveloppe un widget de bloc avec sa poignée de déplacement.

    ``content`` reste accessible via l'attribut du même nom, pour que
    la fenêtre principale puisse continuer à interagir directement
    avec le widget métier du bloc (focus, texte, etc.).
    """

    def __init__(self, content: QWidget, block_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.content = content
        self.block_id = block_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_DragHandle(block_id, self))
        layout.addWidget(content, stretch=1)
