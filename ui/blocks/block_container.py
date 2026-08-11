"""
Conteneur générique de bloc (PATCH 13, menu contextuel PATCH 26, icône
de type PATCH 34).

Ajoute une poignée de glisser-déposer (« ⠿ ») et une icône
représentative du type de bloc à gauche de n'importe quel widget de
bloc, pour permettre de réordonner et d'identifier au premier coup
d'œil tous les types de blocs (texte, titres, checklists, images,
tableaux...) de la même façon dans le document. Le clic droit ouvre
un menu contextuel complet (dupliquer, supprimer, déplacer, convertir),
délégué à la fenêtre principale via un callback.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QContextMenuEvent, QDrag, QMouseEvent
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
    """Enveloppe un widget de bloc avec sa poignée de déplacement et
    son clic droit (PATCH 26).

    ``content`` reste accessible via l'attribut du même nom, pour que
    la fenêtre principale puisse continuer à interagir directement
    avec le widget métier du bloc (focus, texte, etc.).
    """

    def __init__(
        self,
        content: QWidget,
        block_id: str,
        on_context_menu_requested: Optional[Callable[[str, QPoint], None]] = None,
        icon: str = "",
        extra_top_margin: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.content = content
        self.block_id = block_id
        self._on_context_menu_requested = on_context_menu_requested

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, extra_top_margin, 0, 0)
        layout.addWidget(_DragHandle(block_id, self))
        if icon:
            icon_label = QLabel(icon, self)
            icon_label.setFixedWidth(22)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
        layout.addWidget(content, stretch=1)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """PATCH 26 — Clic droit complet : délégué à la fenêtre principale."""
        if self._on_context_menu_requested is None:
            return
        self._on_context_menu_requested(self.block_id, event.globalPos())
        event.accept()
