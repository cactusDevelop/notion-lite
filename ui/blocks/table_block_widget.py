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
    QAbstractScrollArea,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
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
from core.duration import format_duration
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
        # PATCH 49 — évite que le tableau soit comprimé dans une hauteur
        # par défaut trop petite (avec sa propre scrollbar interne) :
        # sa hauteur s'ajuste au nombre de lignes (voir _adjust_table_height).
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
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
                f"{column.get('name') or f'Colonne {i + 1}'} "
                f"({COLUMN_TYPE_LABELS[column['type']]}"
                f"{' — début/fin' if column.get('range') else ''})"
                for i, column in enumerate(columns)
            ]
        )

        for row_index, row in enumerate(rows):
            for col_index, column in enumerate(columns):
                self._set_cell_display(row_index, col_index, row, column)

        self._apply_merged_cells(columns, rows)
        self._adjust_table_height()
        self._syncing = False

    def _apply_merged_cells(self, columns: list[dict], rows: list[dict]) -> None:
        """PATCH 49 — fusionne visuellement les cellules consécutives d'une
        même colonne "Texte" qui ont la valeur identique (ex : plusieurs
        lignes "Phase 1" à la suite), pour éviter la répétition inutile.
        Ne modifie jamais les données du bloc, uniquement l'affichage
        (setSpan) ; refait à chaque _rebuild.
        """
        self._table.clearSpans()
        for col_index, column in enumerate(columns):
            if column["type"] != COLUMN_TYPE_TEXT:
                continue
            run_start = 0
            while run_start < len(rows):
                value = rows[run_start]["cells"].get(column["id"])
                run_end = run_start + 1
                while run_end < len(rows) and rows[run_end]["cells"].get(column["id"]) == value and value:
                    run_end += 1
                run_length = run_end - run_start
                if run_length > 1:
                    self._table.setSpan(run_start, col_index, run_length, 1)
                run_start = run_end

    def _adjust_table_height(self) -> None:
        """PATCH 49 — dimensionne le tableau à son contenu réel (au lieu de
        la hauteur par défaut de QTableWidget, qui le fait paraître
        comprimé avec une scrollbar interne)."""
        self._table.resizeRowsToContents()
        header_height = self._table.horizontalHeader().height()
        rows_height = sum(self._table.rowHeight(i) for i in range(self._table.rowCount()))
        frame = 2 * self._table.frameWidth()
        total_height = header_height + rows_height + frame + 4
        self._table.setMinimumHeight(max(total_height, header_height + 40))
        self._table.setMaximumHeight(max(total_height, header_height + 40))

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
        if column.get("range"):
            return self._build_date_range_cell(row, column, value)

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

    def _build_date_range_cell(self, row: dict, column: dict, value) -> QWidget:
        """PATCH 18 — Cellule "Date" en mode plage : deux sélecteurs (début / fin)."""
        value = value or {"start": "", "end": ""}
        container = QWidget(self._table)
        cell_layout = QHBoxLayout(container)
        cell_layout.setContentsMargins(0, 0, 0, 0)

        def _make_edit(field: str) -> QDateEdit:
            edit = QDateEdit(container)
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")
            edit.setMinimumDate(QDate(1900, 1, 1))
            qdate = QDate.fromString(value.get(field, ""), "yyyy-MM-dd")
            edit.setDate(qdate if qdate.isValid() else edit.minimumDate())
            return edit

        start_edit = _make_edit("start")
        end_edit = _make_edit("end")
        cell_layout.addWidget(QLabel("Du", container))
        cell_layout.addWidget(start_edit)
        cell_layout.addWidget(QLabel("au", container))
        cell_layout.addWidget(end_edit)

        def _push() -> None:
            self._block.set_cell(
                row["id"],
                column["id"],
                {
                    "start": start_edit.date().toString("yyyy-MM-dd"),
                    "end": end_edit.date().toString("yyyy-MM-dd"),
                },
            )

        start_edit.dateChanged.connect(_push)
        end_edit.dateChanged.connect(_push)
        return container

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

        preview_label = QLabel(format_duration(value), container)
        preview_label.setStyleSheet("color: gray;")
        cell_layout.addWidget(preview_label, 1)

        def _push() -> None:
            new_value = {"amount": amount_spin.value(), "unit": unit_combo.currentText()}
            self._block.set_cell(row["id"], column["id"], new_value)
            preview_label.setText(format_duration(new_value))

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
        name, col_type, options, date_range = result
        self._block.add_column(name=name, col_type=col_type, options=options, date_range=date_range)
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
            self,
            name=column.get("name", ""),
            col_type=column["type"],
            options=column.get("options", []),
            date_range=column.get("range", False),
        )
        if result is None:
            return
        name, col_type, options, date_range = result
        self._block.rename_column(column["id"], name)
        if col_type == column["type"]:
            self._block.set_column_options(column["id"], options)
            if col_type == "date":
                self._block.set_column_date_range(column["id"], date_range)
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
