"""
Widget graphique du bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49, PATCH 54).

Barre pleine bleue = "Prévu". Marqueur en pointillés = "Réel" (rouge
en dépassement de budget, vert sinon), si renseigné.

PATCH 54 : un sélecteur "Source" permet de relier ce graphique à un
bloc "Planning par dépendances" existant, avec un regroupement
optionnel par colonne du tableau source (ex : "Phases"). Une fois
relié, les barres sont en lecture seule et recalculées en direct
(sondage périodique, même principe que le bloc Gantt) à partir des
durées et des écarts ("Ecarts") des sous-tâches — l'édition manuelle
des barres reste disponible tant qu'aucune source n'est choisie.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
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

from blocks.bar_chart_block import BarChartBlock, budget_marker_color, sync_bars_from_gantt
from blocks.dependency_gantt_block import (
    DependencyGanttBlock,
    available_label_columns,
    find_source_table,
)
from ui.no_scroll_combo_box import NoScrollComboBox

_MARGIN = 30
_REFRESH_INTERVAL_MS = 500


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
    """Widget d'un BarChartBlock : titre, source optionnelle, barres, graphique."""

    def __init__(self, block: BarChartBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

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

        # -- PATCH 54 : source (planning par dépendances) + regroupement --
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Source :", self))
        self._source_combo = NoScrollComboBox(self)
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_row.addWidget(self._source_combo, 1)
        source_row.addWidget(QLabel("Regrouper par :", self))
        self._group_combo = NoScrollComboBox(self)
        self._group_combo.currentIndexChanged.connect(self._on_group_changed)
        source_row.addWidget(self._group_combo, 1)
        layout.addLayout(source_row)

        self._canvas = _BarChartCanvas(self)
        layout.addWidget(self._canvas)

        self._bars_area = QGridLayout()
        self._bars_area.addWidget(QLabel("<b>Phase</b>", self), 0, 0)
        self._bars_area.addWidget(QLabel("<b>Prévu</b>", self), 0, 1)
        self._bars_area.addWidget(QLabel("<b>Réel</b>", self), 0, 2)
        layout.addLayout(self._bars_area)

        self._add_button = QPushButton("+ Ajouter une barre", self)
        self._add_button.clicked.connect(self._on_add_bar)
        layout.addWidget(self._add_button)

        self._populate_source_combo()
        self._rebuild_bar_rows()
        self._refresh_canvas()

        # PATCH 54 — tant qu'une source est reliée, les barres dépendent
        # de l'état (potentiellement modifié ailleurs) du tableau/Gantt
        # relié : sondage périodique, même principe que DependencyGanttBlockWidget.
        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer_refresh)
        self._timer.start()

    @property
    def block(self) -> BarChartBlock:
        return self._block

    # -- Source (PATCH 54) -------------------------------------------------

    def _gantt_blocks(self) -> list[DependencyGanttBlock]:
        return [b for b in self._document.blocks if isinstance(b, DependencyGanttBlock)]

    def _populate_source_combo(self) -> None:
        self._syncing = True
        self._source_combo.clear()
        self._source_combo.addItem("Aucune (manuel)", None)
        selected_index = 0
        for gantt in self._gantt_blocks():
            self._source_combo.addItem(f"Planning « {gantt.id[:8]} »", gantt.id)
            if gantt.id == self._block.source_gantt_id:
                selected_index = self._source_combo.count() - 1
        self._source_combo.setCurrentIndex(selected_index)
        self._populate_group_combo()
        self._syncing = False

    def _populate_group_combo(self) -> None:
        self._group_combo.clear()
        self._group_combo.addItem("Par sous-tâche", None)
        gantt = self._document.find_block(self._block.source_gantt_id) if self._block.source_gantt_id else None
        selected_index = 0
        if isinstance(gantt, DependencyGanttBlock):
            table = find_source_table(self._document, gantt)
            if table is not None:
                for column in available_label_columns(table):
                    self._group_combo.addItem(column["name"], column["id"])
                    if column["id"] == self._block.group_column_id:
                        selected_index = self._group_combo.count() - 1
        self._group_combo.setCurrentIndex(selected_index)
        self._group_combo.setEnabled(gantt is not None)

    def _is_linked(self) -> bool:
        return self._block.source_gantt_id is not None

    def _on_source_changed(self) -> None:
        if self._syncing:
            return
        gantt_id = self._source_combo.currentData()
        self._block.set_source(gantt_id, None)
        self._populate_group_combo()
        self._apply_linked_mode()
        self._refresh_canvas()

    def _on_group_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(self._block.source_gantt_id, self._group_combo.currentData())
        self._refresh_canvas()

    def _apply_linked_mode(self) -> None:
        """PATCH 54 — édition manuelle désactivée tant qu'une source est reliée."""
        linked = self._is_linked()
        self._add_button.setVisible(not linked)
        self._rebuild_bar_rows()

    def _on_timer_refresh(self) -> None:
        if self._is_linked():
            self._refresh_canvas()

    # -- Barres --------------------------------------------------------

    def _rebuild_bar_rows(self) -> None:
        # Conserve la ligne d'en-tête (ligne 0), vide seulement les lignes de données.
        for row_index in range(1, self._bars_area.rowCount()):
            for col in range(4):
                item = self._bars_area.itemAtPosition(row_index, col)
                if item is not None and item.widget() is not None:
                    item.widget().deleteLater()

        if self._is_linked():
            # PATCH 54 — barres recalculées, lecture seule : rien à
            # éditer ligne par ligne ici, tout passe par le graphique.
            return

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
        if self._is_linked():
            bars = sync_bars_from_gantt(self._document, self._block)
        else:
            bars = self._block.bars
        self._canvas.set_data(bars, self._block.y_axis_label)

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
