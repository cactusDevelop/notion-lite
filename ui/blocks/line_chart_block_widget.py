"""
Widget graphique du bloc "Courbes" (PATCH 47).
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.line_chart_block import (
    SLOPE_MODE_CONSTANT,
    SLOPE_MODE_EFFICIENCY,
    LineChartBlock,
    compute_line_series,
)

_REFRESH_INTERVAL_MS = 500
_MARGIN = 30


class _LineChartCanvas(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._series: list[dict] = []
        self.setMinimumHeight(220)

    def set_series(self, series: list[dict]) -> None:
        self._series = series
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        plot_w, plot_h = w - 2 * _MARGIN, h - 2 * _MARGIN

        y_max = max((max(s["y0"], s["y1"]) for s in self._series), default=1.0)
        x_max = max((max(s["x0"], s["x1"]) for s in self._series), default=1.0)
        y_max = y_max or 1.0
        x_max = x_max or 1.0

        def to_px(x: float, y: float) -> tuple[int, int]:
            px = _MARGIN + int(x / x_max * plot_w)
            py = h - _MARGIN - int(y / y_max * plot_h)
            return px, py

        # Axes.
        painter.setPen(QPen(QColor("#888888"), 1))
        painter.drawLine(_MARGIN, h - _MARGIN, w - _MARGIN, h - _MARGIN)
        painter.drawLine(_MARGIN, h - _MARGIN, _MARGIN, _MARGIN)

        for s in self._series:
            pen = QPen(QColor(s["color"]), 2)
            painter.setPen(pen)
            x0, y0 = to_px(s["x0"], s["y0"])
            x1, y1 = to_px(s["x1"], s["y1"])
            painter.drawLine(x0, y0, x1, y1)
            painter.drawText(x1 - 60, y1 - 6, 60, 16, Qt.AlignRight, s["name"])

        painter.end()


class LineChartBlockWidget(QWidget):
    """Widget d'un LineChartBlock : titre, échelle, séries éditables, courbes."""

    def __init__(self, block: LineChartBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.addWidget(QLabel("Titre :", self))
        self._title_edit = QLineEdit(block.title, self)
        self._title_edit.textChanged.connect(self._on_title_changed)
        header.addWidget(self._title_edit, 1)
        header.addWidget(QLabel("X max :", self))
        self._x_max_spin = QDoubleSpinBox(self)
        self._x_max_spin.setRange(0.01, 100000)
        self._x_max_spin.setValue(block.x_max)
        self._x_max_spin.valueChanged.connect(self._on_x_max_changed)
        header.addWidget(self._x_max_spin)
        layout.addLayout(header)

        self._canvas = _LineChartCanvas(self)
        layout.addWidget(self._canvas)

        self._series_area = QGridLayout()
        layout.addLayout(self._series_area)

        add_button = QPushButton("+ Ajouter une droite", self)
        add_button.clicked.connect(self._on_add_series)
        layout.addWidget(add_button)

        self._rebuild_series_rows()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> LineChartBlock:
        return self._block

    def _gantt_blocks(self) -> list[DependencyGanttBlock]:
        return [b for b in self._document.blocks if isinstance(b, DependencyGanttBlock)]

    def _rebuild_series_rows(self) -> None:
        while self._series_area.count():
            item = self._series_area.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._syncing = True
        for row_index, s in enumerate(self._block.series):
            name_edit = QLineEdit(s["name"], self)
            name_edit.textChanged.connect(lambda text, sid=s["id"]: self._on_series_name_changed(sid, text))
            self._series_area.addWidget(name_edit, row_index, 0)

            mode_combo = QComboBox(self)
            mode_combo.addItem("Constante", SLOPE_MODE_CONSTANT)
            mode_combo.addItem("Vélocité réelle (planning)", SLOPE_MODE_EFFICIENCY)
            mode_combo.setCurrentIndex(0 if s["mode"] == SLOPE_MODE_CONSTANT else 1)
            self._series_area.addWidget(mode_combo, row_index, 1)

            slope_spin = QDoubleSpinBox(self)
            slope_spin.setRange(-1000, 1000)
            slope_spin.setSingleStep(0.1)
            slope_spin.setValue(s["slope"])
            slope_spin.setEnabled(s["mode"] == SLOPE_MODE_CONSTANT)
            slope_spin.valueChanged.connect(lambda v, sid=s["id"]: self._on_series_slope_changed(sid, v))
            self._series_area.addWidget(slope_spin, row_index, 2)

            source_combo = QComboBox(self)
            source_combo.addItem("(aucun planning)", None)
            for gantt in self._gantt_blocks():
                source_combo.addItem(f"Planning {gantt.id[:8]}", gantt.id)
            source_index = source_combo.findData(s.get("source_block_id"))
            source_combo.setCurrentIndex(source_index if source_index >= 0 else 0)
            source_combo.setEnabled(s["mode"] == SLOPE_MODE_EFFICIENCY)
            self._series_area.addWidget(source_combo, row_index, 3)

            mode_combo.currentIndexChanged.connect(
                lambda _, sid=s["id"], mc=mode_combo, sc=source_combo, ss=slope_spin: self._on_series_mode_changed(
                    sid, mc, sc, ss
                )
            )
            source_combo.currentIndexChanged.connect(
                lambda _, sid=s["id"], mc=mode_combo, sc=source_combo: self._on_series_source_changed(sid, mc, sc)
            )

            remove_button = QPushButton("×", self)
            remove_button.clicked.connect(lambda _, sid=s["id"]: self._on_remove_series(sid))
            self._series_area.addWidget(remove_button, row_index, 4)
        self._syncing = False

    # -- Callbacks --------------------------------------------------------

    def _on_title_changed(self, text: str) -> None:
        self._block.title = text
        self.refresh()

    def _on_x_max_changed(self, value: float) -> None:
        self._block.x_max = value
        self.refresh()

    def _on_add_series(self) -> None:
        self._block.add_series(name=f"Droite {len(self._block.series) + 1}")
        self._rebuild_series_rows()
        self.refresh()

    def _on_remove_series(self, series_id: str) -> None:
        self._block.remove_series(series_id)
        self._rebuild_series_rows()
        self.refresh()

    def _on_series_name_changed(self, series_id: str, text: str) -> None:
        if self._syncing:
            return
        self._block.set_series_name(series_id, text)
        self.refresh()

    def _on_series_slope_changed(self, series_id: str, value: float) -> None:
        if self._syncing:
            return
        self._block.set_series_slope(series_id, value)
        self.refresh()

    def _on_series_mode_changed(self, series_id: str, mode_combo, source_combo, slope_spin) -> None:
        if self._syncing:
            return
        mode = mode_combo.currentData()
        slope_spin.setEnabled(mode == SLOPE_MODE_CONSTANT)
        source_combo.setEnabled(mode == SLOPE_MODE_EFFICIENCY)
        self._block.set_series_mode(series_id, mode, source_combo.currentData() if mode == SLOPE_MODE_EFFICIENCY else None)
        self.refresh()

    def _on_series_source_changed(self, series_id: str, mode_combo, source_combo) -> None:
        if self._syncing:
            return
        if mode_combo.currentData() == SLOPE_MODE_EFFICIENCY:
            self._block.set_series_mode(series_id, SLOPE_MODE_EFFICIENCY, source_combo.currentData())
            self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        self._canvas.set_series(compute_line_series(self._document, self._block))
