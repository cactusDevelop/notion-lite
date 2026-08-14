"""
Widget graphique du bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49, PATCH 54, PATCH 59).

Barre pleine bleue = "Prévu". Marqueur en pointillés = "Réel" (rouge
en dépassement de budget, vert sinon), si renseigné.

PATCH 54 : un sélecteur "Source" permet de relier ce graphique à un
bloc "Planning par dépendances" existant, avec un regroupement
optionnel par colonne du tableau source (ex : "Phases"). Une fois
relié, les barres sont recalculées en direct (sondage périodique,
même principe que le bloc Gantt) à partir du tableau source.

PATCH 59 : l'édition manuelle des barres (ligne "Phase / Prévu / Réel"
+ bouton "Ajouter une barre") a été retirée — elle ne servait plus à
rien, le graphique étant toujours piloté par sa source. À la place,
deux sélecteurs "Prévu" / "Réel" choisissent les colonnes "Nombre" du
tableau source à sommer par groupe (ex : "Prix estimé" / "Prix réel").
Sans source reliée, le graphique n'affiche aucune barre.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from blocks.bar_chart_block import BarChartBlock, budget_marker_color, sync_bars_from_gantt
from blocks.dependency_gantt_block import (
    DependencyGanttBlock,
    available_duration_columns,
    available_label_columns,
    find_source_table,
)
from ui.no_scroll_combo_box import NoScrollComboBox
from ui.i18n import tr

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
        # PATCH 58 — couleur de texte par défaut alignée sur le thème
        # (blanc en mode sombre, noir en mode clair) plutôt qu'un noir
        # figé : évite qu'un texte reste illisible une fois qu'un
        # marqueur "Réel" a été dessiné (voir plus bas).
        default_pen = QPen(self.palette().color(QPalette.WindowText))
        painter.setPen(default_pen)

        if self._y_axis_label:
            painter.save()
            painter.translate(12, h / 2)
            painter.rotate(-90)
            painter.drawText(-plot_h / 2, 0, plot_h, 16, Qt.AlignCenter, self._y_axis_label)
            painter.restore()

        painter.drawLine(_MARGIN, h - _MARGIN, w - _MARGIN, h - _MARGIN)

        if not self._bars:
            painter.drawText(self.rect(), Qt.AlignCenter, tr("bar_chart.no_data"))
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
            painter.setPen(default_pen)
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
                # PATCH 58 — on restaure la couleur de texte du thème, pas
                # un noir figé (voir `default_pen` ci-dessus).
                painter.setPen(default_pen)

        painter.end()


class BarChartBlockWidget(QWidget):
    """Widget d'un BarChartBlock : titre, source, colonnes Prévu/Réel, graphique.

    PATCH 59 — plus d'édition manuelle des barres : le graphique est
    toujours entièrement piloté par sa source (planning par
    dépendances) et les colonnes "Prévu"/"Réel" choisies ci-dessous."""

    def __init__(self, block: BarChartBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self._title_edit = QLineEdit(block.title, self)
        self._title_edit.setPlaceholderText(tr("bar_chart.title_placeholder"))
        self._title_edit.setFrame(False)
        self._title_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent; font-weight: bold; font-size: 15pt; }"
        )
        self._title_edit.textChanged.connect(self._on_title_changed)
        header.addWidget(self._title_edit, 1)
        self._y_label_edit = QLineEdit(block.y_axis_label, self)
        self._y_label_edit.setPlaceholderText(tr("bar_chart.y_axis_placeholder"))
        self._y_label_edit.setFrame(False)
        self._y_label_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent; color: #666666; }"
        )
        self._y_label_edit.textChanged.connect(self._on_y_label_changed)
        header.addWidget(self._y_label_edit, 1)
        layout.addLayout(header)

        # -- PATCH 54 : source (planning par dépendances) + regroupement --
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel(tr("bar_chart.source"), self))
        self._source_combo = NoScrollComboBox(self)
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_row.addWidget(self._source_combo, 1)
        source_row.addWidget(QLabel(tr("bar_chart.group_by"), self))
        self._group_combo = NoScrollComboBox(self)
        self._group_combo.currentIndexChanged.connect(self._on_group_changed)
        source_row.addWidget(self._group_combo, 1)
        layout.addLayout(source_row)

        # -- PATCH 59 : colonnes "Prévu" / "Réel" (ex : "Prix estimé" /
        # "Prix réel") remplaçant l'ancienne ligne d'édition manuelle --
        columns_row = QHBoxLayout()
        columns_row.addWidget(QLabel(tr("bar_chart.planned"), self))
        self._value_column_combo = NoScrollComboBox(self)
        self._value_column_combo.currentIndexChanged.connect(self._on_value_column_changed)
        columns_row.addWidget(self._value_column_combo, 1)
        columns_row.addWidget(QLabel(tr("bar_chart.actual"), self))
        self._actual_column_combo = NoScrollComboBox(self)
        self._actual_column_combo.currentIndexChanged.connect(self._on_actual_column_changed)
        columns_row.addWidget(self._actual_column_combo, 1)
        layout.addLayout(columns_row)

        self._canvas = _BarChartCanvas(self)
        layout.addWidget(self._canvas)

        self._populate_source_combo()
        self._refresh_canvas()

        # PATCH 54 — les barres dépendent de l'état (potentiellement
        # modifié ailleurs) du tableau/Gantt relié : sondage périodique,
        # même principe que DependencyGanttBlockWidget.
        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self._refresh_canvas)
        self._timer.start()

    @property
    def block(self) -> BarChartBlock:
        return self._block

    # -- Source (PATCH 54) -------------------------------------------------

    def _gantt_blocks(self) -> list[DependencyGanttBlock]:
        return [b for b in self._document.blocks if isinstance(b, DependencyGanttBlock)]

    def _source_table(self):
        gantt = self._document.find_block(self._block.source_gantt_id) if self._block.source_gantt_id else None
        if not isinstance(gantt, DependencyGanttBlock):
            return None
        return find_source_table(self._document, gantt)

    def _populate_source_combo(self) -> None:
        self._syncing = True
        self._source_combo.clear()
        self._source_combo.addItem(tr("dep_gantt.none_fem"), None)
        selected_index = 0
        for gantt in self._gantt_blocks():
            self._source_combo.addItem(f"{tr('bar_chart.schedule')} « {gantt.id[:8]} »", gantt.id)
            if gantt.id == self._block.source_gantt_id:
                selected_index = self._source_combo.count() - 1
        self._source_combo.setCurrentIndex(selected_index)
        self._populate_group_combo()
        self._populate_column_combos()
        self._syncing = False

    def _populate_group_combo(self) -> None:
        self._group_combo.clear()
        self._group_combo.addItem(tr("bar_chart.by_subtask"), None)
        table = self._source_table()
        selected_index = 0
        if table is not None:
            for column in available_label_columns(table):
                self._group_combo.addItem(column["name"], column["id"])
                if column["id"] == self._block.group_column_id:
                    selected_index = self._group_combo.count() - 1
        self._group_combo.setCurrentIndex(selected_index)
        self._group_combo.setEnabled(table is not None)

    def _populate_column_combos(self) -> None:
        """PATCH 59 — remplit les sélecteurs "Prévu"/"Réel" avec les
        colonnes "Nombre" du tableau source (ex : "Prix estimé",
        "Prix réel", ou l'ancienne "Temps estimé (jours)")."""
        table = self._source_table()
        columns = available_duration_columns(table) if table is not None else []
        for combo, selected_id in (
            (self._value_column_combo, self._block.value_column_id),
            (self._actual_column_combo, self._block.actual_column_id),
        ):
            combo.clear()
            combo.addItem(tr("bar_chart.duration_plus_delta"), None)
            selected_index = 0
            for column in columns:
                combo.addItem(column["name"], column["id"])
                if column["id"] == selected_id:
                    selected_index = combo.count() - 1
            combo.setCurrentIndex(selected_index)
            combo.setEnabled(table is not None)

    def _on_source_changed(self) -> None:
        if self._syncing:
            return
        gantt_id = self._source_combo.currentData()
        self._block.set_source(gantt_id, None, None, None)
        self._populate_group_combo()
        self._populate_column_combos()
        self._refresh_canvas()

    def _on_group_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.source_gantt_id,
            self._group_combo.currentData(),
            self._block.value_column_id,
            self._block.actual_column_id,
        )
        self._refresh_canvas()

    def _on_value_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.source_gantt_id,
            self._block.group_column_id,
            self._value_column_combo.currentData(),
            self._block.actual_column_id,
        )
        self._refresh_canvas()

    def _on_actual_column_changed(self) -> None:
        if self._syncing:
            return
        self._block.set_source(
            self._block.source_gantt_id,
            self._block.group_column_id,
            self._block.value_column_id,
            self._actual_column_combo.currentData(),
        )
        self._refresh_canvas()

    def _refresh_canvas(self) -> None:
        bars = sync_bars_from_gantt(self._document, self._block)
        self._canvas.set_data(bars, self._block.y_axis_label)

    # -- Callbacks --------------------------------------------------------

    def _on_title_changed(self, text: str) -> None:
        self._block.title = text

    def _on_y_label_changed(self, text: str) -> None:
        self._block.y_axis_label = text
        self._refresh_canvas()
