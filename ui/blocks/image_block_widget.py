"""
Widget graphique du bloc Image.

Affiche l'image décodée depuis le base64 du bloc, permet de la
redimensionner (largeur ; hauteur recalculée au ratio d'origine),
de la déplacer dans le document (haut/bas) et de la supprimer.
"""
from __future__ import annotations

import base64
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from blocks.image_block import ImageBlock
from ui.i18n import tr

_MIN_WIDTH = 50
_MAX_WIDTH = 2000


class ImageBlockWidget(QWidget):
    """Représentation graphique éditable d'un ImageBlock."""

    def __init__(
        self,
        block: ImageBlock,
        on_move_up: Optional[Callable[[], None]] = None,
        on_move_down: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._block = block
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_delete = on_delete
        self._source_pixmap = self._decode_pixmap(block)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._image_label = QLabel(self)
        self._image_label.setAlignment(Qt.AlignLeft)
        outer.addWidget(self._image_label)

        controls = QHBoxLayout()

        controls.addWidget(QLabel(tr("image.width"), self))
        self._width_spin = QSpinBox(self)
        self._width_spin.setRange(_MIN_WIDTH, _MAX_WIDTH)
        self._width_spin.setSingleStep(10)
        self._width_spin.setValue(self._initial_width())
        self._width_spin.valueChanged.connect(self._on_width_changed)
        controls.addWidget(self._width_spin)

        controls.addStretch(1)

        up_button = QToolButton(self)
        up_button.setText("↑")
        up_button.setToolTip(tr("context.move_up"))
        up_button.clicked.connect(lambda: self._on_move_up() if self._on_move_up else None)
        controls.addWidget(up_button)

        down_button = QToolButton(self)
        down_button.setText("↓")
        down_button.setToolTip(tr("context.move_down"))
        down_button.clicked.connect(lambda: self._on_move_down() if self._on_move_down else None)
        controls.addWidget(down_button)

        delete_button = QPushButton(tr("context.delete"), self)
        delete_button.clicked.connect(lambda: self._on_delete() if self._on_delete else None)
        controls.addWidget(delete_button)

        outer.addLayout(controls)

        # Applique la largeur initiale (native ou déjà enregistrée) à l'affichage.
        self._apply_width(self._width_spin.value())

    @property
    def block(self) -> ImageBlock:
        return self._block

    @staticmethod
    def _decode_pixmap(block: ImageBlock) -> QPixmap:
        pixmap = QPixmap()
        if block.image_base64:
            try:
                raw_bytes = base64.b64decode(block.image_base64)
            except (ValueError, TypeError):
                return pixmap
            pixmap.loadFromData(raw_bytes)
        return pixmap

    def _initial_width(self) -> int:
        if self._block.width:
            return max(_MIN_WIDTH, min(_MAX_WIDTH, self._block.width))
        if not self._source_pixmap.isNull():
            return max(_MIN_WIDTH, min(_MAX_WIDTH, self._source_pixmap.width()))
        return _MIN_WIDTH

    def _on_width_changed(self, value: int) -> None:
        self._block.width = value
        self._apply_width(value)

    def _apply_width(self, width: int) -> None:
        if self._source_pixmap.isNull():
            self._image_label.setText("(image illisible)")
            return
        scaled = self._source_pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self._image_label.setPixmap(scaled)
