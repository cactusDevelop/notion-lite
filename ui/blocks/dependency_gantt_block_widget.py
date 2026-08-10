"""
Widget graphique du bloc "Gantt (dépendances)" (PATCH 46, révisé PATCH 49).

Une ligne par personne assignée à au moins une sous-tâche ; chaque
sous-tâche est dessinée comme une barre (couleur = risque) sur la
ligne de chaque personne qui lui est assignée, sous un axe temporel
gradué. Le retard (noir) ou l'avance (bleu) déclaré sur une
sous-tâche est visible directement sur sa barre.

PATCH 49 :
    - Axe temporel gradué en haut du graphique.
    - L'écart (retard/avance) se règle via une pop-up qui s'ouvre au
      clic sur le bâtonnet concerné, et s'écrit dans la colonne
      "Ecarts" du tableau source (sélectionnée comme les autres
      colonnes) plutôt que stockée dans le bloc.
    - Sélecteur d'unité "Jours" / "Mois" : change l'échelle de l'axe
      et l'affichage des valeurs chiffrées (l'écart saisi et les
      graduations), sans jamais changer le stockage interne, qui
      reste toujours en jours (voir DAYS_PER_MONTH côté bloc).
"""
from __future__ import annotations

from PySide6.QtCore import QRect, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from blocks.dependency_gantt_block import (
    DAYS_PER_MONTH,
    UNIT_DAYS,
    UNIT_MONTHS,
    DependencyGanttBlock,
    available_delta_columns,
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
_AXIS_HEIGHT = 24
_LABEL_WIDTH = 120
_DELAY_COLOR = QColor("#1a1a1a")
_ADVANCE_COLOR = QColor("#2196f3")

_UNIT_LABELS = {UNIT_DAYS: "Jours", UNIT_MONTHS: "Mois"}


def _nice_axis_step(max_value: float) -> float:
    """Choisit un pas d'axe "rond" (1, 2, 5, 10, 20, 50, ...) donnant
    environ 5 à 10 graduations sur [0, max_value] (max_value déjà
    exprimé dans l'unité d'affichage choisie)."""
    if max_value <= 0:
        return 1.0
    raw_step = max_value / 8
    if raw_step < 1:
        return 0.1 if raw_step >= 0.1 else 0.01
    magnitude = 10 ** (len(str(int(raw_step))) - 1)
    for factor in (1, 2, 5, 10):
        step = factor * magnitude
        if step >= raw_step:
            return step
    return magnitude * 10


class _DependencyGanttCanvas(QWidget):
    """Zone de dessin : axe temporel + une ligne par personne, une barre
    par sous-tâche assignée. Cliquer sur une barre ouvre la pop-up
    d'écart (retard/avance) via le callback `on_bar_clicked`."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._people: list[str] = []
        self._tasks_by_person: dict[str, list[dict]] = {}
        self._bar_rects: list[tuple[QRect, dict]] = []
        self._time_unit = UNIT_DAYS
        self.on_bar_clicked = None
        self.setMinimumHeight(_ROW_HEIGHT + _AXIS_HEIGHT)

    def set_time_unit(self, unit: str) -> None:
        self._time_unit = unit
        self.update()

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
        self.setMinimumHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(people)) + _AXIS_HEIGHT)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self.on_bar_clicked is not None:
            for rect, task in reversed(self._bar_rects):
                if rect.contains(event.pos()):
                    self.on_bar_clicked(task)
                    return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._bar_rects = []

        if not self._people:
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune donnée à afficher.")
            painter.end()
            return

        max_x_days = max(
            (max(t["resolution"], t["end"]) for tasks in self._tasks_by_person.values() for t in tasks),
            default=1.0,
        ) or 1.0

        chart_width = max(self.width() - _LABEL_WIDTH - 10, 20)

        def to_x(day: float) -> int:
            return _LABEL_WIDTH + int(day / max_x_days * chart_width)

        # -- Axe temporel (PATCH 49), gradué dans l'unité choisie -------
        divisor = DAYS_PER_MONTH if self._time_unit == UNIT_MONTHS else 1.0
        max_x_display = max_x_days / divisor
        step_display = _nice_axis_step(max_x_display)
        unit_suffix = "M" if self._time_unit == UNIT_MONTHS else "J"

        painter.setPen(QPen(QColor("#888888"), 1))
        painter.drawLine(_LABEL_WIDTH, _AXIS_HEIGHT, self.width(), _AXIS_HEIGHT)
        tick_display = 0.0
        while tick_display <= max_x_display + step_display / 2:
            x = to_x(tick_display * divisor)
            painter.drawLine(x, _AXIS_HEIGHT - 4, x, _AXIS_HEIGHT)
            painter.drawText(x - 20, 0, 40, _AXIS_HEIGHT - 4, Qt.AlignCenter, f"{unit_suffix}{tick_display:g}")
            tick_display += step_display

        for i, name in enumerate(self._people):
            y = _AXIS_HEIGHT + i * _ROW_HEIGHT
            painter.setPen(QPen(QColor("#000000")))
            painter.drawText(0, y, _LABEL_WIDTH, _ROW_HEIGHT, Qt.AlignVCenter, name)
            for task in self._tasks_by_person[name]:
                start, end, resolution = task["start"], task["end"], task["resolution"]
                color = QColor(task["color"])
                x_start, x_end = to_x(start), to_x(end)
                bar_rect = QRect(x_start, y + 5, max(x_end - x_start, 2), _ROW_HEIGHT - 10)
                painter.fillRect(bar_rect, color)
                hit_rect = QRect(bar_rect)

                if task["delta"] > 0:
                    # Retard : prolongement noir jusqu'au point de résolution.
                    x_resolution = to_x(resolution)
                    extra = QRect(x_end, y + 5, max(x_resolution - x_end, 2), _ROW_HEIGHT - 10)
                    painter.fillRect(extra, _DELAY_COLOR)
                    hit_rect = hit_rect.united(extra)
                elif task["delta"] < 0:
                    # Avance : le temps gagné (fin de la barre normale) en bleu.
                    x_resolution = to_x(resolution)
                    extra = QRect(x_resolution, y + 5, max(x_end - x_resolution, 2), _ROW_HEIGHT - 10)
                    painter.fillRect(extra, _ADVANCE_COLOR)

                self._bar_rects.append((hit_rect, task))

        painter.end()


class _DeltaDialog(QDialog):
    """Pop-up d'édition de l'écart (retard/avance) d'une sous-tâche.

    La valeur est saisie et affichée dans l'unité choisie pour le
    Gantt (jours ou mois), mais toujours convertie en jours avant
    d'être renvoyée via value_in_days().
    """

    def __init__(self, task_label: str, current_delta_days: float, unit: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Écart — {task_label}")
        self._unit = unit
        divisor = DAYS_PER_MONTH if unit == UNIT_MONTHS else 1.0

        layout = QVBoxLayout(self)
        unit_label = _UNIT_LABELS.get(unit, "Jours").lower()
        layout.addWidget(
            QLabel(f"Retard (positif) ou avance (négatif), en {unit_label} :", self)
        )
        self._spin = QDoubleSpinBox(self)
        self._spin.setRange(-999, 999)
        self._spin.setDecimals(2)
        self._spin.setValue(current_delta_days / divisor)
        layout.addWidget(self._spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value_in_days(self) -> float:
        divisor = DAYS_PER_MONTH if self._unit == UNIT_MONTHS else 1.0
        return self._spin.value() * divisor


class DependencyGanttBlockWidget(QWidget):
    """Widget d'un DependencyGanttBlock : sélecteurs de source + graphique."""

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
            ("delta", "Ecarts"),
        ):
            selectors.addWidget(QLabel(f"{label} :", self))
            combo = QComboBox(self)
            combo.currentIndexChanged.connect(self._on_source_changed)
            selectors.addWidget(combo, 1)
            self._combos[key] = combo
        layout.addLayout(selectors)

        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Unité :", self))
        self._unit_combo = QComboBox(self)
        self._unit_combo.addItem("Jours", UNIT_DAYS)
        self._unit_combo.addItem("Mois", UNIT_MONTHS)
        index = self._unit_combo.findData(self._block.time_unit)
        self._unit_combo.setCurrentIndex(index if index >= 0 else 0)
        self._unit_combo.currentIndexChanged.connect(self._on_unit_changed)
        unit_row.addWidget(self._unit_combo)
        unit_row.addStretch(1)
        layout.addLayout(unit_row)

        self._canvas = _DependencyGanttCanvas(self)
        self._canvas.on_bar_clicked = self._on_bar_clicked
        self._canvas.set_time_unit(self._block.time_unit)
        layout.addWidget(self._canvas)

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
            ("delta", available_delta_columns, self._block.delta_column_id),
        )
        for key, getter, current_id in specs:
            combo = self._combos[key]
            combo.clear()
            combo.addItem("(aucune)", None)
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
                self._combos["delta"].currentData(),
            )
        self.refresh()

    def _on_unit_changed(self) -> None:
        if self._syncing:
            return
        self._block.time_unit = self._unit_combo.currentData()
        self._canvas.set_time_unit(self._block.time_unit)
        self.refresh()

    # -- Édition de l'écart via pop-up (PATCH 49) ------------------------

    def _on_bar_clicked(self, task: dict) -> None:
        dialog = _DeltaDialog(task["label"], task["delta"], self._block.time_unit, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        value_days = dialog.value_in_days()

        table = find_source_table(self._document, self._block)
        delta_column_id = self._block.delta_column_id
        if table is not None and delta_column_id is not None:
            table.set_cell(task["row_id"], delta_column_id, str(value_days))
        else:
            # Aucune colonne "Ecarts" configurée : repli sur l'ancien
            # stockage propre au bloc (voir DependencyGanttBlock.set_delta).
            self._block.set_delta(task["row_id"], value_days)
        self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        self._canvas.set_schedule(compute_schedule(self._document, self._block))
