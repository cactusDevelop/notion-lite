"""
Widget graphique du bloc Gantt (PATCH 19, PATCH 70 : zoom + défilement).

Le widget ne conserve aucune copie des données du tableau : à chaque
rafraîchissement (changement de sélection, ou minuterie périodique),
il appelle `compute_gantt_rows` qui relit directement le TableBlock
référencé dans le document. Toute modification du tableau (cellule,
ajout/suppression de ligne...) apparaît donc automatiquement, sans
action de synchronisation explicite.

PATCH 70 :
    - Le graphique est désormais placé dans une zone de défilement
      horizontale (QScrollArea) : à l'échelle 100 %, il continue de
      s'ajuster à la largeur disponible comme avant, mais dès qu'on
      zoome au-delà, une barre de défilement apparaît pour se déplacer
      sur la période sans écraser les barres.
    - Un curseur "Échelle" (50 % à 400 %) permet d'agrandir/réduire le
      nombre de pixels par jour affiché.
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

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
# PATCH 70 — nombre de pixels par jour à l'échelle 100 %, multiplié par
# le zoom courant pour obtenir la largeur totale du graphique.
_BASE_PX_PER_DAY = 4
_ZOOM_MIN = 50
_ZOOM_MAX = 400
_ZOOM_STEP = 25
_ZOOM_DEFAULT = 100


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class _GanttCanvas(QWidget):
    """Zone de dessin : une ligne par tâche, une barre proportionnelle aux dates.

    PATCH 70 — Sa largeur "idéale" (`_update_width`) dépend désormais du
    nombre de jours à représenter et du zoom courant, pas seulement de
    la largeur disponible : au-delà de la largeur de la zone de
    défilement qui la contient, une barre horizontale apparaît.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._span_days = 1
        self._zoom_percent = _ZOOM_DEFAULT
        self.setMinimumHeight(_ROW_HEIGHT)

    def set_zoom(self, zoom_percent: int) -> None:
        self._zoom_percent = zoom_percent
        self._update_width()
        self.update()

    def set_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        dated = [(r, _parse_iso(r["start"]), _parse_iso(r["end"])) for r in rows]
        valid_dates = [d for _, s, e in dated for d in (s, e) if d is not None]
        min_date = min(valid_dates) if valid_dates else None
        max_date = max(valid_dates) if valid_dates else None
        self._span_days = max((max_date - min_date).days, 1) if min_date and max_date else 1
        self.setMinimumHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(rows)))
        self._update_width()
        self.update()

    def _update_width(self) -> None:
        chart_width = int(self._span_days * _BASE_PX_PER_DAY * self._zoom_percent / 100)
        self.setMinimumWidth(140 + max(chart_width, 20) + 10)

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

        # PATCH 70 — curseur d'échelle (zoom) : agrandit/réduit le
        # nombre de pixels par jour, indépendamment de la largeur du bloc.
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Échelle :", self))
        zoom_out_button = QToolButton(self)
        zoom_out_button.setText("－")
        zoom_out_button.setAutoRaise(True)
        zoom_out_button.clicked.connect(lambda: self._nudge_zoom(-_ZOOM_STEP))
        zoom_row.addWidget(zoom_out_button)
        self._zoom_slider = QSlider(Qt.Horizontal, self)
        self._zoom_slider.setRange(_ZOOM_MIN, _ZOOM_MAX)
        self._zoom_slider.setSingleStep(_ZOOM_STEP)
        self._zoom_slider.setPageStep(_ZOOM_STEP)
        self._zoom_slider.setValue(_ZOOM_DEFAULT)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_row.addWidget(self._zoom_slider)
        zoom_in_button = QToolButton(self)
        zoom_in_button.setText("＋")
        zoom_in_button.setAutoRaise(True)
        zoom_in_button.clicked.connect(lambda: self._nudge_zoom(_ZOOM_STEP))
        zoom_row.addWidget(zoom_in_button)
        self._zoom_label = QLabel(f"{_ZOOM_DEFAULT} %", self)
        self._zoom_label.setFixedWidth(42)
        zoom_row.addWidget(self._zoom_label)
        zoom_row.addStretch(1)
        layout.addLayout(zoom_row)

        self._canvas = _GanttCanvas(self)
        # PATCH 70 — zone de défilement horizontale : à zoom ≤ 100 % le
        # graphique continue de s'ajuster à la largeur du bloc (comme
        # avant), au-delà une barre de défilement apparaît.
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QScrollArea.NoFrame)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self._scroll_area.setWidget(self._canvas)
        layout.addWidget(self._scroll_area)

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

    # -- Zoom (PATCH 70) --------------------------------------------------

    def _nudge_zoom(self, delta: int) -> None:
        self._zoom_slider.setValue(self._zoom_slider.value() + delta)

    def _on_zoom_changed(self, value: int) -> None:
        self._zoom_label.setText(f"{value} %")
        self._canvas.set_zoom(value)

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        """Relit le tableau source et redessine (PATCH 19 : aucune donnée
        propre au Gantt, tout est recalculé à partir du document)."""
        rows = compute_gantt_rows(self._document, self._block)
        self._canvas.set_rows(rows)
