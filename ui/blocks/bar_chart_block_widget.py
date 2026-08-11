"""
Widget graphique du bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49).

Barre pleine bleue = "Prévu". Marqueur en pointillés = "Réel" (rouge
en dépassement de budget, vert sinon), si renseigné.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from blocks.bar_chart_block import BarChartBlock, budget_marker_color

_MARGIN = 30


class _BarChartCanvas(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._bars: list[dict] = []
        self._y_axis_label = ""
        self.setMinimumHeight(220)

    def set_data(self, bars: list[dict], y_axis_label: str) -> None:
        self._bars = bars
        self._y_axis_label = y_axis_label
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        plot_w, plot_h = w - 2 * _MARGIN, h - 2 * _MARGIN

        if self._y_axis_label:
            painter.save()
            painter.translate(12, h / 2)
            painter.rotate(-90)
            painter.drawText(-plot_h / 2, 0, plot_h, 16, Qt.AlignCenter, self._y_axis_label)
            painter.restore()

        painter.drawLine(_MARGIN, h - _MARGIN, w - _MARGIN, h - _MARGIN)

        if not self._bars:
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune barre à afficher.")
            painter.end()
            return

        max_value = max(
            (max(abs(b["value"]), abs(b["actual"] or 0)) for b in self._bars), default=1.0
        ) or 1.0
        slot_w = plot_w / len(self._bars)
        bar_w = slot_w * 0.6

        for i, bar in enumerate(self._bars):
            bar_h = abs(bar["value"]) / max_value * plot_h
            x = _MARGIN + i * slot_w + (slot_w - bar_w) / 2
            y = h - _MARGIN - bar_h
            # Barre "Prévu" pleine, toujours bleue.
            painter.fillRect(int(x), int(y), int(bar_w), int(bar_h), QColor(bar["color"]))
            painter.drawText(int(x - 10), h - _MARGIN + 2, int(bar_w + 20), 16, Qt.AlignCenter, bar["label"])
            painter.drawText(int(x - 10), int(y) - 16, int(bar_w + 20), 16, Qt.AlignCenter, str(bar["value"]))

            # Marqueur "Réel" en pointillés (rouge si dépassement, vert sinon).
            marker_color = budget_marker_color(bar)
            if marker_color is not None:
                actual_h = abs(bar["actual"]) / max_value * plot_h
                actual_y = h - _MARGIN - actual_h
                pen = QPen(QColor(marker_color), 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(int(x), int(actual_y), int(x + bar_w), int(actual_y))
                painter.drawText(
                    int(x - 10), int(actual_y) - 16, int(bar_w + 20), 16, Qt.AlignCenter, str(bar["actual"])
                )
                painter.setPen(QPen(QColor("#000000")))

        painter.end()


class BarChartBlockWidget(QWidget):
    """Widget d'un BarChartBlock : titre, barres éditables (Prévu + Réel), graphique."""

    def __init__(self, block: BarChartBlock, parent=None) -> None:
        super().__init__(parent)
        self._block = block

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self._title_edit = QLineEdit(block.title, self)
        self._title_edit.setPlaceholderText("Titre")
        self._title_edit.setFrame(False)
        self._title_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent; font-weight: bold; font-size: 15pt; }"
        )
        self._title_edit.textChanged.connect(self._on_title_changed)
        header.addWidget(self._title_edit, 1)
        self._y_label_edit = QLineEdit(block.y_axis_label, self)
        self._y_label_edit.setPlaceholderText("Axe Y")
        self._y_label_edit.setFrame(False)
        self._y_label_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent; color: #666666; }"
        )
        self._y_label_edit.textChanged.connect(self._on_y_label_changed)
        header.addWidget(self._y_label_edit, 1)
        layout.addLayout(header)

        self._canvas = _BarChartCanvas(self)
        layout.addWidget(self._canvas)

        self._bars_area = QGridLayout()
        self._bars_area.addWidget(QLabel("<b>Phase</b>", self), 0, 0)
        self._bars_area.addWidget(QLabel("<b>Prévu</b>", self), 0, 1)
        self._bars_area.addWidget(QLabel("<b>Réel</b>", self), 0, 2)
        layout.addLayout(self._bars_area)

        add_button = QPushButton("+ Ajouter une barre", self)
        add_button.clicked.connect(self._on_add_bar)
        layout.addWidget(add_button)

        self._rebuild_bar_rows()
        self._refresh_canvas()

    @property
    def block(self) -> BarChartBlock:
        return self._block

    def _rebuild_bar_rows(self) -> None:
        # Conserve la ligne d'en-tête (ligne 0), vide seulement les lignes de données.
        for row_index in range(1, self._bars_area.rowCount()):
            for col in range(4):
                item = self._bars_area.itemAtPosition(row_index, col)
                if item is not None and item.widget() is not None:
                    item.widget().deleteLater()

        for row_index, bar in enumerate(self._block.bars, start=1):
            label_edit = QLineEdit(bar["label"], self)
            label_edit.textChanged.connect(lambda text, bid=bar["id"]: self._on_bar_label_changed(bid, text))
            self._bars_area.addWidget(label_edit, row_index, 0)

            value_spin = QDoubleSpinBox(self)
            value_spin.setRange(-1000000, 1000000)
            value_spin.setValue(bar["value"])
            value_spin.valueChanged.connect(lambda v, bid=bar["id"]: self._on_bar_value_changed(bid, v))
            self._bars_area.addWidget(value_spin, row_index, 1)

            actual_spin = QDoubleSpinBox(self)
            actual_spin.setRange(-1000000, 1000000)
            actual_spin.setValue(bar["actual"] if bar["actual"] is not None else 0.0)
            actual_spin.valueChanged.connect(lambda v, bid=bar["id"]: self._on_bar_actual_changed(bid, v))
            self._bars_area.addWidget(actual_spin, row_index, 2)

            remove_button = QPushButton("×", self)
            remove_button.clicked.connect(lambda _, bid=bar["id"]: self._on_remove_bar(bid))
            self._bars_area.addWidget(remove_button, row_index, 3)

    def _refresh_canvas(self) -> None:
        self._canvas.set_data(self._block.bars, self._block.y_axis_label)

    # -- Callbacks --------------------------------------------------------

    def _on_title_changed(self, text: str) -> None:
        self._block.title = text

    def _on_y_label_changed(self, text: str) -> None:
        self._block.y_axis_label = text
        self._refresh_canvas()

    def _on_add_bar(self) -> None:
        self._block.add_bar(label=f"Phase {len(self._block.bars) + 1}", value=0)
        self._rebuild_bar_rows()
        self._refresh_canvas()

    def _on_remove_bar(self, bar_id: str) -> None:
        self._block.remove_bar(bar_id)
        self._rebuild_bar_rows()
        self._refresh_canvas()

    def _on_bar_label_changed(self, bar_id: str, text: str) -> None:
        self._block.set_bar_label(bar_id, text)
        self._refresh_canvas()

    def _on_bar_value_changed(self, bar_id: str, value: float) -> None:
        self._block.set_bar_value(bar_id, value)
        self._refresh_canvas()

    def _on_bar_actual_changed(self, bar_id: str, value: float) -> None:
        self._block.set_bar_actual(bar_id, value)
        self._refresh_canvas()
