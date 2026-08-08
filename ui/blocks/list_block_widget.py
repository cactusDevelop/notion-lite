"""
Widget graphique du bloc Liste (PATCH 23).

Une ligne par élément : puce ou numéro (recalculé automatiquement
selon la position) + champ de texte éditable + bouton de suppression.
Un sélecteur permet de basculer entre liste à puces et numérotée.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from blocks.list_block import LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock

_TYPE_LABELS = {LIST_TYPE_BULLET: "À puces", LIST_TYPE_NUMBERED: "Numérotée"}


class ListBlockWidget(QWidget):
    """Représentation graphique éditable d'un ListBlock."""

    def __init__(self, block: ListBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.addWidget(QLabel("Style :", self))
        self._type_combo = QComboBox(self)
        for list_type, label in _TYPE_LABELS.items():
            self._type_combo.addItem(label, list_type)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        header.addWidget(self._type_combo)
        header.addStretch(1)
        layout.addLayout(header)

        self._items_layout = QVBoxLayout()
        layout.addLayout(self._items_layout)

        add_button = QPushButton("+ Élément", self)
        add_button.clicked.connect(self._on_add_item)
        layout.addWidget(add_button)

        self._rebuild()

    @property
    def block(self) -> ListBlock:
        return self._block

    def _rebuild(self) -> None:
        self._syncing = True
        index = self._type_combo.findData(self._block.list_type)
        self._type_combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False

        while self._items_layout.count():
            taken = self._items_layout.takeAt(0)
            if taken.widget():
                taken.widget().deleteLater()

        for position, item in enumerate(self._block.items):
            self._items_layout.addWidget(self._build_row(item, position))

    def _build_row(self, item: dict, position: int) -> QWidget:
        row = QWidget(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        marker_text = "•" if self._block.list_type == LIST_TYPE_BULLET else f"{position + 1}."
        marker = QLabel(marker_text, row)
        marker.setFixedWidth(24)
        row_layout.addWidget(marker)

        line_edit = QLineEdit(item.get("text", ""), row)
        line_edit.textChanged.connect(lambda text, item_id=item["id"]: self._on_item_text_changed(item_id, text))
        row_layout.addWidget(line_edit, 1)

        remove_btn = QPushButton("×", row)
        remove_btn.setFixedWidth(24)
        remove_btn.clicked.connect(lambda _, item_id=item["id"]: self._on_remove_item(item_id))
        row_layout.addWidget(remove_btn)

        return row

    # -- Événements ------------------------------------------------------

    def _on_type_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_list_type(self._type_combo.currentData())
        self._rebuild()

    def _on_add_item(self) -> None:
        self._block.add_item("")
        self._rebuild()

    def _on_remove_item(self, item_id: str) -> None:
        self._block.remove_item(item_id)
        self._rebuild()

    def _on_item_text_changed(self, item_id: str, text: str) -> None:
        self._block.set_item_text(item_id, text)
