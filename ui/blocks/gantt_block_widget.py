"""
Widget graphique du bloc Gantt (PATCH 19).

Le widget ne conserve aucune copie des données du tableau : à chaque
rafraîchissement (changement de sélection, ou minuterie périodique),
il appelle `compute_gantt_rows` qui relit directement le TableBlock
référencé dans le document. Toute modification du tableau (cellule,
ajout/suppression de ligne...) apparaît donc automatiquement, sans
action de synchronisation explicite.
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from blocks.gantt_block import (
    GanttBlock,
    available_date_columns,
    compute_gantt_rows,
    find_source_table,
)
from blocks.table_block import TableBlock
from ui.no_scroll_combo_box import NoScrollComboBox

_REFRESH_INTERVAL_MS = 500
_ROW_HEIGHT = 28
_BAR_COLOR = QColor("#4db6ac")


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class _GanttCanvas(QWidget):
    """Zone de dessin : une ligne par tâche, une barre proportionnelle aux dates."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self.setMinimumHeight(_ROW_HEIGHT)

    def set_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        self.setMinimumHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(rows)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._rows:
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune donnée à afficher.")
            painter.end()
            return

        dated = [
            (r, _parse_iso(r["start"]), _parse_iso(r["end"]))
            for r in self._rows
        ]
        valid_dates = [d for _, s, e in dated for d in (s, e) if d is not None]
        min_date = min(valid_dates) if valid_dates else None
        max_date = max(valid_dates) if valid_dates else None
        span_days = max((max_date - min_date).days, 1) if min_date and max_date else 1

        label_width = 140
        chart_width = max(self.width() - label_width - 10, 20)

        for i, (row, start, end) in enumerate(dated):
            y = i * _ROW_HEIGHT
            painter.drawText(0, y, label_width, _ROW_HEIGHT, Qt.AlignVCenter, row["label"] or "(sans titre)")

            if start is None:
                continue
            end = end or start
            x_start = label_width + int((start - min_date).days / span_days * chart_width)
            x_end = label_width + int(max((end - min_date).days, 0) / span_days * chart_width) + 6
            painter.fillRect(x_start, y + 4, max(x_end - x_start, 6), _ROW_HEIGHT - 8, _BAR_COLOR)

        painter.end()


class GanttBlockWidget(QWidget):
    """Widget d'un GanttBlock : sélecteurs de source + zone de dessin."""

    def __init__(self, block: GanttBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("Tableau :", self))
        self._table_combo = NoScrollComboBox(self)
        self._table_combo.currentIndexChanged.connect(self._on_table_changed)
        selectors.addWidget(self._table_combo, 1)

        selectors.addWidget(QLabel("Libellé :", self))
        self._label_combo = NoScrollComboBox(self)
        self._label_combo.currentIndexChanged.connect(self._on_label_column_changed)
        selectors.addWidget(self._label_combo, 1)

        selectors.addWidget(QLabel("Dates :", self))
        self._date_combo = NoScrollComboBox(self)
        self._date_combo.currentIndexChanged.connect(self._on_date_column_changed)
        selectors.addWidget(self._date_combo, 1)
        layout.addLayout(selectors)

        self._canvas = _GanttCanvas(self)
        layout.addWidget(self._canvas)

        self._populate_table_combo()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> GanttBlock:
        return self._block

    # -- Sélection de la source -----------------------------------------

    def _table_blocks(self) -> list[TableBlock]:
        return [b for b in self._document.blocks if isinstance(b, TableBlock)]

    def _populate_table_combo(self) -> None:
        self._syncing = True
        self._table_combo.clear()
        self._table_combo.addItem("(aucun)", None)
        for table in self._table_blocks():
            title = f"Tableau ({table.columns[0]['name']}...)" if table.columns else "Tableau"
            self._table_combo.addItem(title, table.id)
        index = self._table_combo.findData(self._block.table_block_id)
        self._table_combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False
        self._populate_column_combos()

    def _populate_column_combos(self) -> None:
        self._syncing = True
        self._label_combo.clear()
        self._date_combo.clear()

        table = find_source_table(self._document, self._block)
        if table is not None:
            for column in table.columns:
                self._label_combo.addItem(column["name"] or "(sans nom)", column["id"])
            for column in available_date_columns(table):
                self._date_combo.addItem(column["name"] or "(sans nom)", column["id"])

        label_index = self._label_combo.findData(self._block.label_column_id)
        self._label_combo.setCurrentIndex(label_index if label_index >= 0 else 0)
        date_index = self._date_combo.findData(self._block.date_column_id)
        self._date_combo.setCurrentIndex(date_index if date_index >= 0 else 0)
        self._syncing = False

    def _on_table_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(self._table_combo.currentData(), None, None)
        self._populate_column_combos()
        self.refresh()

    def _on_label_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._label_combo.currentData(), self._block.date_column_id
        )
        self.refresh()

    def _on_date_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.table_block_id, self._block.label_column_id, self._date_combo.currentData()
        )
        self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        """Relit le tableau source et redessine (PATCH 19 : aucune donnée
        propre au Gantt, tout est recalculé à partir du document)."""
        rows = compute_gantt_rows(self._document, self._block)
        self._canvas.set_rows(rows)
