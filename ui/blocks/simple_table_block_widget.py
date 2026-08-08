"""
Widget graphique du bloc Tableau simple (PATCH 24).

QTableWidget minimal : cellules de texte brut uniquement, sans
colonnes typées ni options (voir SimpleTableBlock). Volontairement
plus léger que TableBlockWidget (PATCH 14/15).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from blocks.simple_table_block import SimpleTableBlock


class SimpleTableBlockWidget(QWidget):
    """Représentation graphique éditable d'un SimpleTableBlock."""

    def __init__(self, block: SimpleTableBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(self)
        self._table.horizontalHeader().setVisible(False)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

        buttons = QHBoxLayout()
        for label, handler in (
            ("+ Ligne", self._on_add_row),
            ("+ Colonne", self._on_add_column),
            ("- Ligne", self._on_delete_row),
            ("- Colonne", self._on_delete_column),
        ):
            btn = QPushButton(label, self)
            btn.clicked.connect(handler)
            buttons.addWidget(btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self._rebuild()

    @property
    def block(self) -> SimpleTableBlock:
        return self._block

    def _rebuild(self) -> None:
        self._syncing = True
        self._table.setRowCount(self._block.row_count)
        self._table.setColumnCount(self._block.column_count)
        for row_index, row in enumerate(self._block.rows):
            for col_index, text in enumerate(row):
                self._table.setItem(row_index, col_index, QTableWidgetItem(text))
        self._syncing = False

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._syncing:
            return
        self._block.set_cell(item.row(), item.column(), item.text())

    def _on_add_row(self) -> None:
        self._block.add_row()
        self._rebuild()

    def _on_add_column(self) -> None:
        self._block.add_column()
        self._rebuild()

    def _on_delete_row(self) -> None:
        current = self._table.currentRow()
        if current >= 0:
            self._block.remove_row(current)
            self._rebuild()

    def _on_delete_column(self) -> None:
        current = self._table.currentColumn()
        if current >= 0:
            self._block.remove_column(current)
            self._rebuild()
