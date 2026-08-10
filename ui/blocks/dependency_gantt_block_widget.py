"""
Widget graphique du bloc "Gantt (dépendances)" (PATCH 46).

Une ligne par personne assignée à au moins une sous-tâche ; chaque
sous-tâche est dessinée comme une barre (couleur = risque) sur la
ligne de chaque personne qui lui est assignée. Le retard (noir) ou
l'avance (bleu) déclaré sur une sous-tâche est visible directement
sur sa barre. Une liste sous le graphique permet de saisir ce
retard/avance (en jours) pour chaque sous-tâche.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from blocks.dependency_gantt_block import (
    DependencyGanttBlock,
    available_dependency_columns,
    available_duration_columns,
    available_label_columns,
    available_person_columns,
    available_risk_columns,
    compute_schedule,
    find_source_table,
)
from blocks.table_block import TableBlock

_REFRESH_INTERVAL_MS = 500
_ROW_HEIGHT = 30
_DELAY_COLOR = QColor("#1a1a1a")
_ADVANCE_COLOR = QColor("#2196f3")


class _DependencyGanttCanvas(QWidget):
    """Zone de dessin : une ligne par personne, une barre par sous-tâche assignée."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._people: list[str] = []
        self._tasks_by_person: dict[str, list[dict]] = {}
        self.setMinimumHeight(_ROW_HEIGHT)

    def set_schedule(self, schedule: list[dict]) -> None:
        people: list[str] = []
        tasks_by_person: dict[str, list[dict]] = {}
        for task in schedule:
            for name in task["person_names"] or ["(non assigné)"]:
                if name not in tasks_by_person:
                    tasks_by_person[name] = []
                    people.append(name)
                tasks_by_person[name].append(task)
        self._people = people
        self._tasks_by_person = tasks_by_person
        self.setMinimumHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(people)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._people:
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune donnée à afficher.")
            painter.end()
            return

        max_x = max(
            (max(t["resolution"], t["end"]) for tasks in self._tasks_by_person.values() for t in tasks),
            default=1.0,
        ) or 1.0

        label_width = 120
        chart_width = max(self.width() - label_width - 10, 20)

        def to_x(day: float) -> int:
            return label_width + int(day / max_x * chart_width)

        for i, name in enumerate(self._people):
            y = i * _ROW_HEIGHT
            painter.drawText(0, y, label_width, _ROW_HEIGHT, Qt.AlignVCenter, name)
            for task in self._tasks_by_person[name]:
                start, end, resolution = task["start"], task["end"], task["resolution"]
                color = QColor(task["color"])
                x_start, x_end = to_x(start), to_x(end)
                painter.fillRect(x_start, y + 5, max(x_end - x_start, 2), _ROW_HEIGHT - 10, color)

                if task["delta"] > 0:
                    # Retard : prolongement noir jusqu'au point de résolution.
                    x_resolution = to_x(resolution)
                    painter.fillRect(x_end, y + 5, max(x_resolution - x_end, 2), _ROW_HEIGHT - 10, _DELAY_COLOR)
                elif task["delta"] < 0:
                    # Avance : le temps gagné (fin de la barre normale) en bleu.
                    x_resolution = to_x(resolution)
                    painter.fillRect(x_resolution, y + 5, max(x_end - x_resolution, 2), _ROW_HEIGHT - 10, _ADVANCE_COLOR)

        painter.end()


class DependencyGanttBlockWidget(QWidget):
    """Widget d'un DependencyGanttBlock : sélecteurs + graphique + saisie des écarts."""

    def __init__(self, block: DependencyGanttBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        selectors = QHBoxLayout()
        self._combos: dict[str, QComboBox] = {}
        for key, label in (
            ("table", "Tableau"),
            ("label", "Sous-tâches"),
            ("person", "Personnes"),
            ("duration", "Durée"),
            ("risk", "Risques"),
            ("dependency", "Dépendances"),
        ):
            selectors.addWidget(QLabel(f"{label} :", self))
            combo = QComboBox(self)
            combo.currentIndexChanged.connect(self._on_source_changed)
            selectors.addWidget(combo, 1)
            self._combos[key] = combo
        layout.addLayout(selectors)

        self._canvas = _DependencyGanttCanvas(self)
        layout.addWidget(self._canvas)

        self._deltas_area = QGridLayout()
        layout.addLayout(self._deltas_area)

        self._populate_table_combo()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    @property
    def block(self) -> DependencyGanttBlock:
        return self._block

    # -- Sélection de la source -----------------------------------------

    def _table_blocks(self) -> list[TableBlock]:
        return [b for b in self._document.blocks if isinstance(b, TableBlock)]

    def _populate_table_combo(self) -> None:
        self._syncing = True
        combo = self._combos["table"]
        combo.clear()
        combo.addItem("(aucun)", None)
        for table in self._table_blocks():
            title = f"Tableau ({table.columns[0]['name']}...)" if table.columns else "Tableau"
            combo.addItem(title, table.id)
        index = combo.findData(self._block.table_block_id)
        combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False
        self._populate_column_combos()

    def _populate_column_combos(self) -> None:
        self._syncing = True
        table = find_source_table(self._document, self._block)
        specs = (
            ("label", available_label_columns, self._block.label_column_id),
            ("person", available_person_columns, self._block.person_column_id),
            ("duration", available_duration_columns, self._block.duration_column_id),
            ("risk", available_risk_columns, self._block.risk_column_id),
            ("dependency", available_dependency_columns, self._block.dependency_column_id),
        )
        for key, getter, current_id in specs:
            combo = self._combos[key]
            combo.clear()
            if table is not None:
                for column in getter(table):
                    combo.addItem(column["name"] or "(sans nom)", column["id"])
            index = combo.findData(current_id)
            combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing = False

    def _on_source_changed(self) -> None:
        if self._syncing:
            return
        if self.sender() is self._combos["table"]:
            self._block.set_source(self._combos["table"].currentData())
            self._populate_column_combos()
        else:
            self._block.set_source(
                self._block.table_block_id,
                self._combos["label"].currentData(),
                self._combos["person"].currentData(),
                self._combos["duration"].currentData(),
                self._combos["risk"].currentData(),
                self._combos["dependency"].currentData(),
            )
        self.refresh()

    # -- Saisie des écarts (retard/avance) -------------------------------

    def _rebuild_delta_inputs(self, schedule: list[dict]) -> None:
        row_ids = [task["row_id"] for task in schedule]
        if row_ids == getattr(self, "_delta_row_ids", None):
            # Structure inchangée (mêmes lignes) : on ne reconstruit pas les
            # champs à chaque rafraîchissement périodique, ce qui casserait
            # la saisie en cours (focus perdu à chaque frappe).
            return
        self._delta_row_ids = row_ids

        while self._deltas_area.count():
            item = self._deltas_area.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for row_index, task in enumerate(schedule):
            self._deltas_area.addWidget(QLabel(f"Écart « {task['label']} » (jours) :", self), row_index, 0)
            spin = QDoubleSpinBox(self)
            spin.setRange(-999, 999)
            spin.setValue(task["delta"])
            spin.valueChanged.connect(lambda value, row_id=task["row_id"]: self._on_delta_changed(row_id, value))
            self._deltas_area.addWidget(spin, row_index, 1)

    def _on_delta_changed(self, row_id: str, value: float) -> None:
        self._block.set_delta(row_id, value)
        self._canvas.set_schedule(compute_schedule(self._document, self._block))

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        schedule = compute_schedule(self._document, self._block)
        self._canvas.set_schedule(schedule)
        self._rebuild_delta_inputs(schedule)
