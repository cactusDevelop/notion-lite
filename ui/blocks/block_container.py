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

from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt
from PySide6.QtGui import QContextMenuEvent, QDrag, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

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
        on_activated: Optional[Callable[[str], None]] = None,
        icon: str = "",
        extra_top_margin: int = 0,
        # PATCH 68 — Titres/sous-titres : petite flèche de repli/dépli
        # (façon plan Word), qui réduit/développe tous les blocs suivants
        # jusqu'au prochain titre. `on_toggle_collapse` est appelé avec
        # `block_id` au clic ; `collapsed` donne l'état initial de la flèche.
        on_toggle_collapse: Optional[Callable[[str], None]] = None,
        collapsed: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.content = content
        self.block_id = block_id
        self._on_context_menu_requested = on_context_menu_requested
        self._on_activated = on_activated
        self._toggle_button: Optional[QToolButton] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, extra_top_margin, 0, 0)
        layout.addWidget(_DragHandle(block_id, self))
        if icon:
            icon_label = QLabel(icon, self)
            icon_label.setFixedWidth(22)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
        if on_toggle_collapse is not None:
            self._toggle_button = QToolButton(self)
            self._toggle_button.setAutoRaise(True)
            self._toggle_button.setFixedWidth(18)
            self._toggle_button.setCursor(Qt.PointingHandCursor)
            self._toggle_button.setToolTip(
                "Réduire/développer jusqu'au prochain titre ou sous-titre"
            )
            self._toggle_button.clicked.connect(
                lambda: on_toggle_collapse(block_id)
            )
            self.set_collapsed(collapsed)
            layout.addWidget(self._toggle_button)
        layout.addWidget(content, stretch=1)

        # PATCH 67 — Repère le bloc "actif" (dernier cliqué), quel que
        # soit son type (texte, Gantt, tableau, image...), afin qu'un
        # nouveau bloc créé depuis la toolbar ou le menu contextuel
        # s'insère juste après lui plutôt qu'en fin de document. On
        # observe les clics sur le conteneur et tous ses descendants
        # sans intercepter l'événement (juste une notification).
        if self._on_activated is not None:
            self.installEventFilter(self)
            for child in self.findChildren(QWidget):
                child.installEventFilter(self)

    def set_collapsed(self, collapsed: bool) -> None:
        """PATCH 68 — Met à jour l'apparence de la flèche (▾ développé,
        ▸ réduit), sans reconstruire le widget."""
        if self._toggle_button is not None:
            self._toggle_button.setText("▸" if collapsed else "▾")

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (nom imposé par Qt)
        if event.type() == QEvent.MouseButtonPress and self._on_activated is not None:
            self._on_activated(self.block_id)
        return super().eventFilter(obj, event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """PATCH 26 — Clic droit complet : délégué à la fenêtre principale."""
        if self._on_context_menu_requested is None:
            return
        self._on_context_menu_requested(self.block_id, event.globalPos())
        event.accept()
