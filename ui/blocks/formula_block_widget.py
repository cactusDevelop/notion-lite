"""
Widget graphique du bloc "Résultat calculé" (PATCH 45).

Même principe que GanttBlockWidget : aucune donnée propre conservée
côté widget, relecture périodique du TableBlock référencé.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from blocks.formula_block import (
    FormulaBlock,
    available_boolean_columns,
    available_number_columns,
    compute_formula_result,
    find_source_table,
    format_formula_text,
)
from blocks.table_block import TableBlock
from ui.no_scroll_combo_box import NoScrollComboBox
from ui.i18n import tr

_REFRESH_INTERVAL_MS = 500


class FormulaBlockWidget(QWidget):
    """Widget d'un FormulaBlock : sélecteurs de source + résultat affiché."""

    def __init__(self, block: FormulaBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        selectors = QHBoxLayout()
        selectors.addWidget(QLabel(tr("formula.label"), self))
        self._label_edit = QLineEdit(block.label, self)
        self._label_edit.textChanged.connect(self._on_label_changed)
        selectors.addWidget(self._label_edit, 1)

        selectors.addWidget(QLabel(tr("formula.table"), self))
        self._table_combo = NoScrollComboBox(self)
        self._table_combo.currentIndexChanged.connect(self._on_table_changed)
        selectors.addWidget(self._table_combo, 1)

        selectors.addWidget(QLabel(tr("formula.points"), self))
        self._number_combo = NoScrollComboBox(self)
        self._number_combo.currentIndexChanged.connect(self._on_number_column_changed)
        selectors.addWidget(self._number_combo, 1)

        selectors.addWidget(QLabel(tr("formula.state"), self))
        self._boolean_combo = NoScrollComboBox(self)
        self._boolean_combo.currentIndexChanged.connect(self._on_boolean_column_changed)
        selectors.addWidget(self._boolean_combo, 1)
        layout.addLayout(selectors)

        self._result_label = QLabel(self)
        font = self._result_label.font()
        font.setBold(True)
        self._result_label.setFont(font)
        layout.addWidget(self._result_label)

        self._populate_table_combo()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> FormulaBlock:
        return self._block

    # -- Sélection de la source -----------------------------------------

    def _table_blocks(self) -> list[TableBlock]:
        return [b for b in self._document.blocks if isinstance(b, TableBlock)]

    def _populate_table_combo(self) -> None:
        self._syncing = True
        self._table_combo.clear()
        self._table_combo.addItem(tr("formula.none"), None)
        for table in self._table_blocks():
            title = f"{tr('formula.table_prefix')} ({table.columns[0]['name']}...)" if table.columns else tr("formula.table_prefix")
            self._table_combo.addItem(title, table.id)
        index = self._table_combo.findData(self._block.table_block_id)
        self._table_combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False
        self._populate_column_combos()

    def _populate_column_combos(self) -> None:
        self._syncing = True
        self._number_combo.clear()
        self._boolean_combo.clear()

        table = find_source_table(self._document, self._block)
        if table is not None:
            for column in available_number_columns(table):
                self._number_combo.addItem(column["name"] or tr("formula.unnamed"), column["id"])
            for column in available_boolean_columns(table):
                self._boolean_combo.addItem(column["name"] or tr("formula.unnamed"), column["id"])

        number_index = self._number_combo.findData(self._block.number_column_id)
        self._number_combo.setCurrentIndex(number_index if number_index >= 0 else 0)
        boolean_index = self._boolean_combo.findData(self._block.boolean_column_id)
        self._boolean_combo.setCurrentIndex(boolean_index if boolean_index >= 0 else 0)
        self._syncing = False

    def _on_table_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(self._table_combo.currentData(), None, None)
        self._populate_column_combos()
        self.refresh()

    def _on_number_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._number_combo.currentData(), self._block.boolean_column_id
        )
        self.refresh()

    def _on_boolean_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._block.number_column_id, self._boolean_combo.currentData()
        )
        self.refresh()

    def _on_label_changed(self, text: str) -> None:
        self._block.label = text
        self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        result = compute_formula_result(self._document, self._block)
        self._result_label.setText(format_formula_text(self._block, result))
