"""
Widget graphique du bloc Tableau (PATCH 14).

Affiche les colonnes/lignes du TableBlock dans un QTableWidget.
Toute édition de cellule ou d'en-tête est immédiatement répercutée
dans le bloc via les id (colonne/ligne), jamais via la position, pour
rester valide après un ajout/suppression/déplacement.
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

from blocks.table_block import TableBlock


class TableBlockWidget(QWidget):
    """Représentation graphique éditable d'un TableBlock."""

    def __init__(self, block: TableBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(self)
        self._table.itemChanged.connect(self._on_item_changed)
        self._table.horizontalHeader().sectionDoubleClicked.connect(
            self._on_header_double_clicked
        )
        layout.addWidget(self._table)

        buttons = QHBoxLayout()
        add_row_btn = QPushButton("+ Ligne", self)
        add_row_btn.clicked.connect(self._on_add_row)
        buttons.addWidget(add_row_btn)

        add_col_btn = QPushButton("+ Colonne", self)
        add_col_btn.clicked.connect(self._on_add_column)
        buttons.addWidget(add_col_btn)

        del_row_btn = QPushButton("- Ligne", self)
        del_row_btn.clicked.connect(self._on_delete_row)
        buttons.addWidget(del_row_btn)

        del_col_btn = QPushButton("- Colonne", self)
        del_col_btn.clicked.connect(self._on_delete_column)
        buttons.addWidget(del_col_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self._rebuild()

    @property
    def block(self) -> TableBlock:
        return self._block

    # -- Rendu -------------------------------------------------------

    def _rebuild(self) -> None:
        """Reconstruit entièrement la grille à partir du bloc."""
        self._syncing = True
        columns = self._block.columns
        rows = self._block.rows

        self._table.setColumnCount(len(columns))
        self._table.setRowCount(len(rows))
        self._table.setHorizontalHeaderLabels(
            [column.get("name") or f"Colonne {i + 1}" for i, column in enumerate(columns)]
        )

        for row_index, row in enumerate(rows):
            for col_index, column in enumerate(columns):
                value = row["cells"].get(column["id"], "")
                item = QTableWidgetItem(str(value))
                self._table.setItem(row_index, col_index, item)

        self._syncing = False

    # -- Colonnes ------------------------------------------------------

    def _on_add_column(self) -> None:
        self._block.add_column(name=f"Colonne {len(self._block.columns) + 1}")
        self._rebuild()

    def _on_delete_column(self) -> None:
        current_col = self._table.currentColumn()
        if current_col < 0 or current_col >= len(self._block.columns):
            return
        column_id = self._block.columns[current_col]["id"]
        self._block.remove_column(column_id)
        self._rebuild()

    def _on_header_double_clicked(self, section: int) -> None:
        if section < 0 or section >= len(self._block.columns):
            return
        from PySide6.QtWidgets import QInputDialog

        column = self._block.columns[section]
        name, ok = QInputDialog.getText(
            self, "Renommer la colonne", "Nom :", text=column.get("name", "")
        )
        if ok:
            self._block.rename_column(column["id"], name)
            self._rebuild()

    # -- Lignes --------------------------------------------------------

    def _on_add_row(self) -> None:
        self._block.add_row()
        self._rebuild()

    def _on_delete_row(self) -> None:
        current_row = self._table.currentRow()
        if current_row < 0 or current_row >= len(self._block.rows):
            return
        row_id = self._block.rows[current_row]["id"]
        self._block.remove_row(row_id)
        self._rebuild()

    # -- Édition de cellule ----------------------------------------------

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._syncing:
            return
        row_index, col_index = item.row(), item.column()
        if row_index >= len(self._block.rows) or col_index >= len(self._block.columns):
            return
        row_id = self._block.rows[row_index]["id"]
        column_id = self._block.columns[col_index]["id"]
        self._block.set_cell(row_id, column_id, item.text())
