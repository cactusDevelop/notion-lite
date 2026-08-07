"""
Widget graphique du bloc Tableau (PATCH 14) + colonnes typées (PATCH 15).

Affiche les colonnes/lignes du TableBlock dans un QTableWidget. Le
widget de cellule dépend du type de la colonne (texte libre, case à
cocher, sélecteur de date, choix, ...). Toute édition est répercutée
dans le bloc via les id (colonne/ligne), jamais via la position.
"""
from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from blocks.table_block import (
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_CHECKLIST,
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_DURATION,
    COLUMN_TYPE_LABELS,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_TEXT,
    DURATION_UNITS,
    TableBlock,
)
from ui.blocks.table_cell_dialogs import (
    ask_column_definition,
    edit_checklist_cell,
    edit_multi_select,
    edit_person_list,
)


class TableBlockWidget(QWidget):
    """Représentation graphique éditable d'un TableBlock."""

    def __init__(self, block: TableBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
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
            [
                f"{column.get('name') or f'Colonne {i + 1}'} ({COLUMN_TYPE_LABELS[column['type']]})"
                for i, column in enumerate(columns)
            ]
        )

        for row_index, row in enumerate(rows):
            for col_index, column in enumerate(columns):
                self._set_cell_display(row_index, col_index, row, column)

        self._syncing = False

    def _set_cell_display(self, row_index: int, col_index: int, row: dict, column: dict) -> None:
        """Place le widget/item adapté au type de `column` dans la grille."""
        col_type = column["type"]
        value = row["cells"].get(column["id"])

        if col_type == COLUMN_TYPE_TEXT:
            self._table.setCellWidget(row_index, col_index, None)
            self._table.setItem(row_index, col_index, QTableWidgetItem(str(value or "")))
            return

        if col_type == COLUMN_TYPE_NUMBER:
            self._table.setCellWidget(row_index, col_index, None)
            self._table.setItem(row_index, col_index, QTableWidgetItem(str(value or "")))
            return

        self._table.setItem(row_index, col_index, QTableWidgetItem(""))

        if col_type == COLUMN_TYPE_BOOLEAN:
            self._table.setCellWidget(row_index, col_index, self._build_boolean_cell(row, column, value))
        elif col_type == COLUMN_TYPE_DATE:
            self._table.setCellWidget(row_index, col_index, self._build_date_cell(row, column, value))
        elif col_type == COLUMN_TYPE_DURATION:
            self._table.setCellWidget(row_index, col_index, self._build_duration_cell(row, column, value))
        elif col_type == COLUMN_TYPE_SELECT:
            self._table.setCellWidget(row_index, col_index, self._build_select_cell(row, column, value))
        elif col_type == COLUMN_TYPE_PERSON:
            self._table.setCellWidget(row_index, col_index, self._build_person_cell(row, column, value))
        elif col_type == COLUMN_TYPE_MULTI_SELECT:
            self._table.setCellWidget(row_index, col_index, self._build_multi_select_cell(row, column, value))
        elif col_type == COLUMN_TYPE_CHECKLIST:
            self._table.setCellWidget(row_index, col_index, self._build_checklist_cell(row, column, value))

    def _refresh_cell(self, row_id: str, column_id: str) -> None:
        """Redessine une seule cellule après une modification (sans tout reconstruire)."""
        row_index = next((i for i, r in enumerate(self._block.rows) if r["id"] == row_id), None)
        col_index = next((i for i, c in enumerate(self._block.columns) if c["id"] == column_id), None)
        if row_index is None or col_index is None:
            return
        row = self._block.rows[row_index]
        column = self._block.columns[col_index]
        self._syncing = True
        self._set_cell_display(row_index, col_index, row, column)
        self._syncing = False

    # -- Widgets de cellule par type -----------------------------------

    def _build_boolean_cell(self, row: dict, column: dict, value) -> QWidget:
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox(container)
        checkbox.setChecked(bool(value))
        checkbox.toggled.connect(lambda checked: self._block.set_cell(row["id"], column["id"], checked))
        cell_layout.addWidget(checkbox)
        return container

    def _build_date_cell(self, row: dict, column: dict, value) -> QWidget:
        date_edit = QDateEdit(self._table)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setSpecialValueText(" ")
        qdate = QDate.fromString(value, "yyyy-MM-dd") if value else QDate()
        date_edit.setMinimumDate(QDate(1900, 1, 1))
        date_edit.setDate(qdate if qdate.isValid() else date_edit.minimumDate())

        def _on_changed(new_date: QDate) -> None:
            self._block.set_cell(row["id"], column["id"], new_date.toString("yyyy-MM-dd"))

        date_edit.dateChanged.connect(_on_changed)
        return date_edit

    def _build_duration_cell(self, row: dict, column: dict, value) -> QWidget:
        value = value or {"amount": 0, "unit": DURATION_UNITS[1]}
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)

        amount_spin = QSpinBox(container)
        amount_spin.setRange(0, 9999)
        amount_spin.setValue(int(value.get("amount", 0)))
        cell_layout.addWidget(amount_spin)

        unit_combo = QComboBox(container)
        unit_combo.addItems(DURATION_UNITS)
        unit_combo.setCurrentText(value.get("unit", DURATION_UNITS[1]))
        cell_layout.addWidget(unit_combo)

        def _push() -> None:
            self._block.set_cell(
                row["id"], column["id"], {"amount": amount_spin.value(), "unit": unit_combo.currentText()}
            )

        amount_spin.valueChanged.connect(_push)
        unit_combo.currentTextChanged.connect(_push)
        return container

    def _build_select_cell(self, row: dict, column: dict, value) -> QWidget:
        combo = QComboBox(self._table)
        combo.addItem("")
        combo.addItems(column.get("options", []))
        combo.setCurrentText(value or "")
        combo.currentTextChanged.connect(lambda text: self._block.set_cell(row["id"], column["id"], text))
        return combo

    def _build_person_cell(self, row: dict, column: dict, value) -> QWidget:
        person_ids = value or []
        names = [
            (self._document.find_person(pid) or {}).get("name", "?") for pid in person_ids
        ]
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(", ".join(names), container)
        cell_layout.addWidget(label, 1)
        edit_btn = QPushButton("...", container)
        edit_btn.setFixedWidth(28)

        def _on_click() -> None:
            current = list(self._block.get_cell(row["id"], column["id"]) or [])
            result = edit_person_list(self, self._document, current)
            if result is not None:
                self._block.set_cell(row["id"], column["id"], result)
                self._refresh_cell(row["id"], column["id"])

        edit_btn.clicked.connect(_on_click)
        cell_layout.addWidget(edit_btn)
        return container

    def _build_multi_select_cell(self, row: dict, column: dict, value) -> QWidget:
        selected = value or []
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(", ".join(selected), container)
        cell_layout.addWidget(label, 1)
        edit_btn = QPushButton("...", container)
        edit_btn.setFixedWidth(28)

        def _on_click() -> None:
            current = (self._block.get_cell(row["id"], column["id"]) or [])
            result = edit_multi_select(self, column.get("options", []), list(current))
            if result is not None:
                self._block.set_cell(row["id"], column["id"], result)
                self._refresh_cell(row["id"], column["id"])

        edit_btn.clicked.connect(_on_click)
        cell_layout.addWidget(edit_btn)
        return container

    def _build_checklist_cell(self, row: dict, column: dict, value) -> QWidget:
        items = value or []
        done = sum(1 for item in items if item.get("checked"))
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(f"{done}/{len(items)}", container)
        cell_layout.addWidget(label, 1)
        edit_btn = QPushButton("...", container)
        edit_btn.setFixedWidth(28)

        def _on_click() -> None:
            current = (self._block.get_cell(row["id"], column["id"]) or [])
            result = edit_checklist_cell(self, list(current))
            if result is not None:
                self._block.set_cell(row["id"], column["id"], result)
                self._refresh_cell(row["id"], column["id"])

        edit_btn.clicked.connect(_on_click)
        cell_layout.addWidget(edit_btn)
        return container

    # -- Colonnes ------------------------------------------------------

    def _on_add_column(self) -> None:
        result = ask_column_definition(self, name=f"Colonne {len(self._block.columns) + 1}")
        if result is None:
            return
        name, col_type, options = result
        self._block.add_column(name=name, col_type=col_type, options=options)
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
        column = self._block.columns[section]
        result = ask_column_definition(
            self, name=column.get("name", ""), col_type=column["type"], options=column.get("options", [])
        )
        if result is None:
            return
        name, col_type, options = result
        self._block.rename_column(column["id"], name)
        if col_type == column["type"]:
            self._block.set_column_options(column["id"], options)
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

    # -- Édition de cellule texte/nombre ----------------------------------

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._syncing:
            return
        row_index, col_index = item.row(), item.column()
        if row_index >= len(self._block.rows) or col_index >= len(self._block.columns):
            return
        row_id = self._block.rows[row_index]["id"]
        column_id = self._block.columns[col_index]["id"]
        self._block.set_cell(row_id, column_id, item.text())
