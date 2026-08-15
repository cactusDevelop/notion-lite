"""
Widget graphique du bloc "Gantt (dépendances)" (PATCH 46, révisé PATCH 49, PATCH 57).

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

PATCH 57 :
    - Les bâtonnets sont désormais directement ajustables au clic-
      glissé, à l'instar du séparateur "À faire"/"Faites" du bloc
      "Checklists liées" (QSplitter) : cliquer-glisser un bâtonnet
      vers la droite/gauche rallonge/raccourcit son retard ou son
      avance en temps réel (voir `_DependencyGanttCanvas` et
      `on_bar_drag_moved`/`on_bar_drag_finished`). Un simple clic
      (sans glissement notable) ouvre toujours la pop-up de saisie
      précise (`_DeltaDialog`), pour une valeur exacte.

PATCH 71 (remplace PATCH 70, dont le zoom n'avait aucun effet tant que
le canvas était étiré pour remplir la zone visible) :
    - Le canvas a désormais une largeur FIXE, déterminée uniquement par
      le curseur "Échelle" (nombre de jours × pixels/jour à 100 % ×
      zoom). Il n'est plus jamais étiré par la zone de défilement, donc
      bouger le curseur a toujours un effet visible, immédiatement.
    - La zone de défilement (QScrollArea) ne défile qu'à l'horizontale ;
      verticalement le canvas garde toujours sa hauteur complète (une
      ligne par personne + axe), sans découpage ni barre verticale.
    - Un bouton "Auto" recalcule le zoom nécessaire pour que tout
      l'intervalle temporel tienne exactement dans la largeur visible
      (comportement historique), et resynchronise le curseur. Tant que
      ce mode est actif, il se réajuste automatiquement au
      redimensionnement du bloc ou au changement des données ; il se
      désactive dès que l'utilisateur bouge le curseur ou les boutons ±
      manuellement.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from PySide6.QtCore import QDate, QRect, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from blocks.dependency_gantt_block import (
    DAYS_PER_MONTH,
    FORMAT_MACRO,
    FORMAT_MICRO,
    DependencyGanttBlock,
    available_delta_columns,
    available_dependency_columns,
    available_duration_columns,
    available_label_columns,
    available_person_columns,
    available_phase_columns,
    available_risk_columns,
    compute_schedule,
    find_source_table,
)
from blocks.table_block import TableBlock
from ui.no_scroll_combo_box import NoScrollComboBox
from ui.i18n import tr

_REFRESH_INTERVAL_MS = 500
_ROW_HEIGHT = 30
_AXIS_HEIGHT = 24
_LABEL_WIDTH = 120
# PATCH 74 — bandeau réservé aux séparateurs/étiquettes de phase, ajouté
# entre l'axe temporel et les lignes UNIQUEMENT si une colonne "Phases"
# est configurée (sinon le graphique garde sa hauteur habituelle).
_PHASE_BAND_HEIGHT = 18
_PHASE_LINE_COLOR = QColor("#7e57c2")
_DELAY_COLOR = QColor("#1a1a1a")
_ADVANCE_COLOR = QColor("#2196f3")
# PATCH 57 — en-deçà de ce nombre de pixels de glissement, le geste est
# traité comme un simple clic (ouvre la pop-up de saisie précise) plutôt
# que comme un ajustement direct de l'écart.
_DRAG_THRESHOLD_PX = 4
_DELTA_RANGE_DAYS = 999.0

# PATCH 71 — nombre de pixels par jour à l'échelle 100 %, multiplié par
# le zoom courant pour obtenir la largeur totale du graphique (mode
# micro uniquement, voir _MACRO_BASE_CELL_PX pour le mode macro).
_BASE_PX_PER_DAY = 4
_ZOOM_MIN = 10
_ZOOM_MAX = 800
_ZOOM_STEP = 25
_ZOOM_DEFAULT = 100

# PATCH 90 — mode macro (calendrier) : largeur/hauteur des cases du
# calendrier (7 colonnes = jours de la semaine), une "semaine" par
# ligne, avec une bande par personne à l'intérieur de chaque semaine.
_MACRO_BASE_CELL_PX = 40
_MACRO_MIN_CELL_PX = 24
_MACRO_HEADER_H = 16
_MACRO_PERSON_ROW_H = 22
_MACRO_WEEK_GAP = 6
# PATCH 91 — mode macro calendaire (avec "Jour 0" configuré) : hauteur
# de l'en-tête des jours de la semaine, dessiné une seule fois en haut
# de la grille (voir _paint_macro_calendar).
_MACRO_WEEKDAY_HEADER_H = 20
_TODAY_BORDER_COLOR = QColor("#e53935")

_WEEKDAY_KEYS = [
    "dep_gantt.weekday.mon",
    "dep_gantt.weekday.tue",
    "dep_gantt.weekday.wed",
    "dep_gantt.weekday.thu",
    "dep_gantt.weekday.fri",
    "dep_gantt.weekday.sat",
    "dep_gantt.weekday.sun",
]
_MONTH_KEYS = [f"dep_gantt.month.{i}" for i in range(1, 13)]


def _format_month_year(day: date) -> str:
    return f"{tr(_MONTH_KEYS[day.month - 1])} {day.year}"


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _micro_axis_step(max_value_days: float) -> tuple[float, str]:
    """PATCH 90 — Choisit un pas d'axe adaptatif pour le mode micro, en
    doublant depuis 1 jour (1, 2, 4, 8, 16 J) puis en poursuivant le
    doublement en mois au-delà (1, 2, 4, 8... M), plutôt que la
    progression 1/2/5/10 utilisée avant l'introduction du mode macro.
    Retourne (pas en jours, suffixe "J" ou "M")."""
    raw_step = max(max_value_days / 8, 1.0)
    step = 1.0
    is_months = False
    while step < raw_step:
        if step < 16:
            step *= 2
        else:
            step = DAYS_PER_MONTH if not is_months else step * 2
            is_months = True
    return step, ("M" if is_months else "J")


def _compute_phase_groups(schedule: list[dict]) -> list[dict]:
    """PATCH 74 — Regroupe les sous-tâches consécutives (dans l'ordre du
    tableau source) partageant la même valeur non vide de colonne
    "Phases", avec l'étendue temporelle (jours) couverte par le groupe.
    Retourne une liste vide si aucune colonne "Phases" n'est configurée
    (chaque tâche a alors "phase" == "")."""
    groups: list[dict] = []
    for task in schedule:
        label = task.get("phase") or ""
        if not label:
            continue
        span_start = task["start"]
        span_end = max(task["end"], task["resolution"])
        if groups and groups[-1]["label"] == label:
            groups[-1]["start"] = min(groups[-1]["start"], span_start)
            groups[-1]["end"] = max(groups[-1]["end"], span_end)
        else:
            groups.append({"label": label, "start": span_start, "end": span_end})
    return groups


class _DependencyGanttCanvas(QWidget):
    """Zone de dessin : axe temporel + une ligne par personne, une barre
    par sous-tâche assignée.

    PATCH 57 — Cliquer-glisser un bâtonnet ajuste directement son écart
    (retard/avance) en temps réel, à l'instar du séparateur ajustable
    des "Checklists liées" : `on_bar_drag_moved(row_id, delta_days)` est
    appelé à chaque déplacement, `on_bar_drag_finished` une fois relâché.
    Un clic sans glissement notable appelle plutôt `on_bar_clicked`
    (pop-up de saisie précise, PATCH 49)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._people: list[str] = []
        self._tasks_by_person: dict[str, list[dict]] = {}
        self._bar_rects: list[tuple[QRect, dict]] = []
        # PATCH 74 — séparateurs de phase (voir set_schedule/_update_geometry).
        self._phase_groups: list[dict] = []
        self._content_top = _AXIS_HEIGHT
        self._format = FORMAT_MICRO
        self.on_bar_clicked = None
        self.on_bar_drag_moved = None
        self.on_bar_drag_finished = None
        # PATCH 57 — état du glisser en cours (None si aucun).
        self._drag_task: dict | None = None
        self._drag_start_x = 0
        self._drag_start_delta = 0.0
        self._drag_moved = False
        self._days_per_pixel = 0.0
        # PATCH 71 — zoom courant (%) et étendue en jours mémorisée à
        # chaque `set_schedule`, pour calculer la taille FIXE du canvas
        # (voir `_update_geometry`), indépendamment de la largeur de la
        # zone de défilement qui le contient.
        self._zoom_percent = _ZOOM_DEFAULT
        self._max_x_days = 1.0
        # PATCH 91 — "Jour 0" calendaire (None si non configuré, voir
        # set_start_date) : bascule le mode macro entre calendrier
        # relatif ("Semaine N", _paint_macro_relative) et calendrier
        # réaliste (vrais jours de semaine/dates, _paint_macro_calendar).
        self._start_date: date | None = None
        # PATCH 92 — "Travailler le weekend" (voir la case à cocher
        # correspondante) : si False (défaut), samedi/dimanche sont
        # grisés dans le calendrier réaliste (_paint_macro_calendar).
        self._work_weekends = False
        # PATCH 72 — notifié à chaque changement de taille du canvas,
        # pour que la QScrollArea parente puisse copier sa hauteur
        # (elle ne le fait pas toute seule quand `widgetResizable` est
        # à False, voir DependencyGanttBlockWidget._sync_scroll_height).
        self.on_geometry_changed = None
        self._update_geometry()
        self.setCursor(Qt.PointingHandCursor)

    @property
    def max_x_days(self) -> float:
        return self._max_x_days

    def set_zoom(self, zoom_percent: int) -> None:
        self._zoom_percent = zoom_percent
        self._update_geometry()
        self.update()

    def set_format(self, chart_format: str) -> None:
        self._format = chart_format
        self._update_geometry()
        self.update()

    def set_start_date(self, iso_value: str) -> None:
        """PATCH 91 — voir `_start_date`. `iso_value` vide ou invalide
        retombe sur le calendrier relatif (None)."""
        self._start_date = _parse_iso_date(iso_value)
        self._update_geometry()
        self.update()

    def set_work_weekends(self, work_weekends: bool) -> None:
        self._work_weekends = work_weekends
        self.update()

    def _macro_calendar_weeks(self) -> tuple[date, int]:
        """PATCH 91 — pour le mode macro calendaire : (lundi de la
        semaine du "Jour 0", nombre de semaines nécessaires pour
        couvrir tout le planning)."""
        anchor = self._start_date
        calendar_start = anchor - timedelta(days=anchor.weekday())
        total_business_days = max(int(math.ceil(max(self._max_x_days, 1.0))), 1)
        # PATCH 93 — le planning est stocké en jours ouvrés (compute_schedule
        # ignore les weekends) ; convertir en jours calendaires réels avant
        # de dimensionner la grille, sinon les dernières semaines (décalées
        # par les weekends sautés) sont coupées quand "Travailler le
        # weekend" est désactivé.
        total_days = max(int(math.ceil(self._business_to_calendar_offset(total_business_days))), 1)
        last_date = anchor + timedelta(days=total_days)
        days_span = (last_date - calendar_start).days + 1
        weeks_count = max(1, math.ceil(days_span / 7))
        return calendar_start, weeks_count

    def _business_to_calendar_offset(self, day: float) -> float:
        """PATCH 93 — convertit un décalage en jours ouvrés (tel que
        stocké par `compute_schedule`, qui ignore toujours les weekends)
        en décalage calendaire réel depuis le "Jour 0", en sautant les
        samedis/dimanches quand `work_weekends` est désactivé. Sans
        effet si `work_weekends` est actif (jour ouvré == jour
        calendaire) : le planning reprend alors son comportement
        historique, continu."""
        if self._work_weekends or self._start_date is None or day <= 0:
            return day
        anchor = self._start_date
        whole = int(math.floor(day))
        frac = day - whole
        offset = 0
        counted = 0
        while counted < whole:
            if (anchor + timedelta(days=offset)).weekday() < 5:
                counted += 1
            offset += 1
        if frac > 1e-9:
            while (anchor + timedelta(days=offset)).weekday() >= 5:
                offset += 1
        return offset + frac

    @property
    def base_content_width(self) -> float:
        """PATCH 90 — largeur "à 100 %" utilisée par le zoom auto
        (`DependencyGanttBlockWidget._sync_auto_zoom`), qui diffère
        entre les deux modes : proportionnelle au nombre de jours en
        micro, fixe (7 colonnes) en macro."""
        if self._format == FORMAT_MACRO:
            return 7 * _MACRO_BASE_CELL_PX
        return max(self._max_x_days, 1.0) * _BASE_PX_PER_DAY

    def _macro_cell_width(self) -> int:
        return max(int(_MACRO_BASE_CELL_PX * self._zoom_percent / 100), _MACRO_MIN_CELL_PX)

    def _weekend_color(self) -> QColor:
        """PATCH 92 — dérivée de la couleur de fond courante plutôt
        qu'une teinte fixe (#f0f0f0, invisible en mode sombre et à
        peine visible en mode clair) : légèrement plus sombre en mode
        clair, légèrement plus claire en mode sombre, pour rester un
        gris discret quel que soit le thème."""
        base = self.palette().color(QPalette.Base)
        return base.darker(107) if base.lightness() > 128 else base.lighter(130)

    def set_schedule(self, schedule: list[dict]) -> None:
        people: list[str] = []
        tasks_by_person: dict[str, list[dict]] = {}
        for task in schedule:
            for name in task["person_names"] or [tr("dep_gantt.unassigned")]:
                if name not in tasks_by_person:
                    tasks_by_person[name] = []
                    people.append(name)
                tasks_by_person[name].append(task)
        self._people = people
        self._tasks_by_person = tasks_by_person
        self._max_x_days = max(
            (max(t["resolution"], t["end"]) for tasks in tasks_by_person.values() for t in tasks),
            default=1.0,
        ) or 1.0
        # PATCH 74 — regroupe les sous-tâches consécutives partageant la
        # même valeur de colonne "Phases" (si configurée), pour tracer un
        # séparateur vertical étiqueté entre chaque phase (voir paintEvent).
        self._phase_groups = _compute_phase_groups(schedule)
        self._update_geometry()
        self.update()

    def _update_geometry(self) -> None:
        if self._format == FORMAT_MACRO:
            cell_w = self._macro_cell_width()
            week_h = _MACRO_HEADER_H + max(1, len(self._people)) * _MACRO_PERSON_ROW_H
            if self._start_date is not None:
                _, weeks = self._macro_calendar_weeks()
                top_offset = _MACRO_WEEKDAY_HEADER_H
            else:
                total_days = max(int(math.ceil(max(self._max_x_days, 1.0))), 1)
                weeks = max(1, math.ceil(total_days / 7))
                top_offset = 0
            self.setFixedWidth(_LABEL_WIDTH + 7 * cell_w + 10)
            self.setFixedHeight(top_offset + weeks * week_h + max(weeks - 1, 0) * _MACRO_WEEK_GAP + 10)
        else:
            chart_width = int(self._max_x_days * _BASE_PX_PER_DAY * self._zoom_percent / 100)
            self._content_top = _AXIS_HEIGHT + (_PHASE_BAND_HEIGHT if self._phase_groups else 0)
            self.setFixedWidth(_LABEL_WIDTH + max(chart_width, 20) + 10)
            self.setFixedHeight(max(_ROW_HEIGHT, _ROW_HEIGHT * len(self._people)) + self._content_top)
        if self.on_geometry_changed is not None:
            self.on_geometry_changed()

    def _bar_at(self, pos) -> dict | None:
        for rect, task in reversed(self._bar_rects):
            if rect.contains(pos):
                return task
        return None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            task = self._bar_at(event.pos())
            if task is not None:
                if self._format == FORMAT_MACRO:
                    # PATCH 90 — pas de clic-glissé en mode macro : les
                    # échelles ne sont pas uniformes (semaine par semaine),
                    # le clic ouvre donc toujours la pop-up de saisie
                    # précise plutôt qu'un ajustement direct au pixel.
                    if self.on_bar_clicked is not None:
                        self.on_bar_clicked(task)
                    return
                self._drag_task = task
                self._drag_start_x = event.pos().x()
                self._drag_start_delta = task["delta"]
                self._drag_moved = False
                self.setCursor(Qt.SizeHorCursor)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_task is None:
            super().mouseMoveEvent(event)
            return
        dx = event.pos().x() - self._drag_start_x
        if not self._drag_moved and abs(dx) < _DRAG_THRESHOLD_PX:
            return
        self._drag_moved = True
        delta_days = self._drag_start_delta + dx * self._days_per_pixel
        delta_days = max(-_DELTA_RANGE_DAYS, min(_DELTA_RANGE_DAYS, delta_days))
        if self.on_bar_drag_moved is not None:
            self.on_bar_drag_moved(self._drag_task["row_id"], delta_days)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._drag_task is None:
            super().mouseReleaseEvent(event)
            return
        task, moved = self._drag_task, self._drag_moved
        self._drag_task = None
        self._drag_moved = False
        self.setCursor(Qt.PointingHandCursor)
        if moved:
            if self.on_bar_drag_finished is not None:
                self.on_bar_drag_finished(task["row_id"])
        elif self.on_bar_clicked is not None:
            self.on_bar_clicked(task)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._bar_rects = []

        if not self._people:
            painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
            painter.drawText(self.rect(), Qt.AlignCenter, tr("gantt.no_data"))
            painter.end()
            return

        if self._format == FORMAT_MACRO:
            if self._start_date is not None:
                self._paint_macro_calendar(painter)
            else:
                self._paint_macro_relative(painter)
        else:
            self._paint_micro(painter)
        painter.end()

    def _paint_micro(self, painter: QPainter) -> None:
        max_x_days = max(
            (max(t["resolution"], t["end"]) for tasks in self._tasks_by_person.values() for t in tasks),
            default=1.0,
        ) or 1.0

        chart_width = max(self.width() - _LABEL_WIDTH - 10, 20)
        # PATCH 57 — mémorisé pour convertir un déplacement en pixels (lors
        # d'un clic-glissé) en jours ; figé au clic (`mousePressEvent`
        # capture cette valeur avant que l'échelle ne bouge pendant le
        # glissement, pour un geste stable plutôt qu'un ré-échelonnage en
        # direct qui rendrait le glisser imprévisible).
        self._days_per_pixel = max_x_days / chart_width if chart_width else 0.0

        def to_x(day: float) -> int:
            return _LABEL_WIDTH + int(day / max_x_days * chart_width)

        # -- Axe temporel (PATCH 49), gradué en jours puis en mois de
        # façon adaptative selon le zoom (PATCH 90, remplace l'ancien
        # sélecteur manuel "Jours"/"Mois") -------------------------------
        step_days, unit_suffix = _micro_axis_step(max_x_days)
        divisor = DAYS_PER_MONTH if unit_suffix == "M" else 1.0

        painter.setPen(QPen(QColor("#888888"), 1))
        painter.drawLine(_LABEL_WIDTH, _AXIS_HEIGHT, self.width(), _AXIS_HEIGHT)
        tick_days = 0.0
        while tick_days <= max_x_days + step_days / 2:
            x = to_x(tick_days)
            painter.drawLine(x, _AXIS_HEIGHT - 4, x, _AXIS_HEIGHT)
            tick_display = tick_days / divisor
            painter.drawText(x - 20, 0, 40, _AXIS_HEIGHT - 4, Qt.AlignCenter, f"{unit_suffix}{tick_display:g}")
            tick_days += step_days

        # -- Séparateurs de phase (PATCH 74) : un trait vertical pointillé
        # à chaque début de phase (sauf la toute première, en début d'axe),
        # avec son libellé (ex. "Phase 2") dans le bandeau dédié.
        if self._phase_groups:
            painter.setFont(QFont(painter.font().family(), -1, QFont.Bold))
            for i, group in enumerate(self._phase_groups):
                x_start = to_x(group["start"])
                if i > 0:
                    painter.setPen(QPen(_PHASE_LINE_COLOR, 1, Qt.DashLine))
                    painter.drawLine(x_start, _AXIS_HEIGHT, x_start, self.height())
                label_rect = QRect(
                    x_start + 4, _AXIS_HEIGHT, max(to_x(group["end"]) - x_start - 4, 10), _PHASE_BAND_HEIGHT
                )
                painter.setPen(QPen(_PHASE_LINE_COLOR, 1))
                painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, group["label"])
            painter.setFont(QFont(painter.font().family()))

        for i, name in enumerate(self._people):
            y = self._content_top + i * _ROW_HEIGHT
            painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
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

    def _paint_macro_relative(self, painter: QPainter) -> None:
        """PATCH 90 — mode macro sans "Jour 0" configuré : calendrier
        relatif (une ligne = une semaine de 7 cases/jours), avec une
        bande par personne à l'intérieur de chaque semaine, colorée
        aux jours où elle a une sous-tâche active (mêmes couleurs/
        retard/avance qu'en mode micro)."""
        cell_w = self._macro_cell_width()
        week_h = _MACRO_HEADER_H + max(1, len(self._people)) * _MACRO_PERSON_ROW_H
        total_days = max(int(math.ceil(max(self._max_x_days, 1.0))), 1)
        weeks = max(1, math.ceil(total_days / 7))

        def day_x(day_in_week: float) -> int:
            return _LABEL_WIDTH + int(day_in_week * cell_w)

        for week in range(weeks):
            week_y = week * (week_h + _MACRO_WEEK_GAP)
            week_start_day = week * 7

            painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
            painter.drawText(
                0, week_y, _LABEL_WIDTH, week_h, Qt.AlignVCenter | Qt.AlignLeft,
                f"{tr('dep_gantt.week')} {week + 1}",
            )

            for d in range(7):
                x = day_x(d)
                painter.setPen(QPen(QColor("#cccccc"), 1))
                painter.drawRect(QRect(x, week_y, cell_w, week_h))
                painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
                painter.drawText(
                    x + 3, week_y + 1, cell_w - 6, _MACRO_HEADER_H - 2,
                    Qt.AlignLeft | Qt.AlignVCenter, f"J{week_start_day + d + 1}",
                )

            for p_index, name in enumerate(self._people):
                row_y = week_y + _MACRO_HEADER_H + p_index * _MACRO_PERSON_ROW_H
                for task in self._tasks_by_person[name]:
                    for x0, x1, color in _clip_task_to_week(task, week_start_day, week_start_day + 7):
                        bar_rect = QRect(
                            day_x(x0), row_y + 3, max(day_x(x1) - day_x(x0), 2), _MACRO_PERSON_ROW_H - 6
                        )
                        painter.fillRect(bar_rect, color)
                        self._bar_rects.append((QRect(bar_rect), task))

    def _paint_macro_calendar(self, painter: QPainter) -> None:
        """PATCH 91 — mode macro avec "Jour 0" configuré : calendrier
        réaliste (vrais jours de la semaine affichés une seule fois en
        en-tête, vraies dates du mois par case, week-ends grisés, nom
        du mois affiché à gauche dès qu'il change), plutôt que le
        calendrier relatif "Semaine N / J1..J7" de
        `_paint_macro_relative`. Les semaines commencent toujours un
        lundi (même si le "Jour 0" du planning tombe un autre jour :
        les cases avant le "Jour 0" dans sa semaine sont affichées,
        sans bâtonnet)."""
        cell_w = self._macro_cell_width()
        calendar_start, weeks = self._macro_calendar_weeks()
        week_h = _MACRO_HEADER_H + max(1, len(self._people)) * _MACRO_PERSON_ROW_H
        top = _MACRO_WEEKDAY_HEADER_H
        today = date.today()

        def day_x(day_in_week: float) -> int:
            return _LABEL_WIDTH + int(day_in_week * cell_w)

        painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
        for d, key in enumerate(_WEEKDAY_KEYS):
            painter.drawText(day_x(d), 0, cell_w, _MACRO_WEEKDAY_HEADER_H, Qt.AlignCenter, tr(key))

        # PATCH 93 — conversion jours ouvrés -> jours calendaires (voir
        # _business_to_calendar_offset), calculée une seule fois pour
        # toutes les semaines : sans elle, une barre continue en jours
        # ouvrés empiète visuellement sur les cases grisées du weekend
        # au lieu de les enjamber.
        tasks_by_person = {
            name: [
                {
                    **task,
                    "start": self._business_to_calendar_offset(task["start"]),
                    "end": self._business_to_calendar_offset(task["end"]),
                    "resolution": self._business_to_calendar_offset(task["resolution"]),
                }
                for task in tasks
            ]
            for name, tasks in self._tasks_by_person.items()
        }

        last_month: tuple[int, int] | None = None
        for week in range(weeks):
            week_y = top + week * (week_h + _MACRO_WEEK_GAP)
            week_start_date = calendar_start + timedelta(weeks=week)
            week_start_day = (week_start_date - self._start_date).days

            month_key = (week_start_date.year, week_start_date.month)
            if month_key != last_month:
                painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
                painter.drawText(
                    0, week_y, _LABEL_WIDTH, week_h, Qt.AlignVCenter | Qt.AlignLeft,
                    _format_month_year(week_start_date),
                )
                last_month = month_key

            for d in range(7):
                cell_date = week_start_date + timedelta(days=d)
                x = day_x(d)
                cell_rect = QRect(x, week_y, cell_w, week_h)
                if cell_date.weekday() >= 5 and not self._work_weekends:
                    painter.fillRect(cell_rect, self._weekend_color())
                painter.setPen(QPen(QColor("#cccccc"), 1))
                painter.drawRect(cell_rect)
                painter.setPen(QPen(self.palette().color(QPalette.WindowText)))
                painter.drawText(
                    x + 3, week_y + 1, cell_w - 6, _MACRO_HEADER_H - 2,
                    Qt.AlignLeft | Qt.AlignVCenter, str(cell_date.day),
                )
                if cell_date == today:
                    painter.setPen(QPen(_TODAY_BORDER_COLOR, 2))
                    painter.drawRect(cell_rect.adjusted(1, 1, -1, -1))

            for p_index, name in enumerate(self._people):
                row_y = week_y + _MACRO_HEADER_H + p_index * _MACRO_PERSON_ROW_H
                for task in tasks_by_person[name]:
                    for x0, x1, color in _clip_task_to_week_business(
                        task, week_start_day, week_start_day + 7, self._start_date, self._work_weekends
                    ):
                        bar_rect = QRect(
                            day_x(x0), row_y + 3, max(day_x(x1) - day_x(x0), 2), _MACRO_PERSON_ROW_H - 6
                        )
                        painter.fillRect(bar_rect, color)
                        self._bar_rects.append((QRect(bar_rect), task))


def _split_business_segments(day_start: float, day_end: float, anchor: date, work_weekends: bool):
    """PATCH 94 — subdivise [day_start, day_end) (décalages calendaires
    absolus depuis `anchor`) en sous-segments qui excluent les colonnes
    de weekend, quand `work_weekends` est désactivé : sans ça, le
    rectangle d'une barre reste continu et recouvre visuellement les
    cases grisées du weekend même si ses bornes ont été calculées pour
    les enjamber (voir _business_to_calendar_offset). Jours ouvrés
    consécutifs fusionnés en un seul segment ; ne produit rien pour
    work_weekends actif (segment unique inchangé, géré par l'appelant)."""
    if work_weekends or day_end <= day_start:
        yield (day_start, day_end)
        return
    day_idx = int(math.floor(day_start))
    seg_start: float | None = None
    seg_end = day_start
    cur = day_start
    while cur < day_end - 1e-9:
        day_bound_end = min(day_idx + 1, day_end)
        if (anchor + timedelta(days=day_idx)).weekday() < 5:
            if seg_start is None:
                seg_start = max(cur, float(day_idx))
            seg_end = day_bound_end
        elif seg_start is not None:
            yield (seg_start, seg_end)
            seg_start = None
        cur = day_bound_end
        day_idx += 1
    if seg_start is not None:
        yield (seg_start, seg_end)


def _clip_task_to_week_business(
    task: dict, week_start_day: float, week_end_day: float, anchor: date, work_weekends: bool
):
    """PATCH 94 — variante de `_clip_task_to_week` pour le calendrier
    réaliste (mode macro avec "Jour 0") : découpe en plus chaque
    segment clippé à la semaine par jour ouvré (voir
    `_split_business_segments`) quand `work_weekends` est désactivé,
    pour qu'aucun bâtonnet ne traverse visuellement un samedi/dimanche."""
    segments = [(task["start"], task["end"], QColor(task["color"]))]
    if task["delta"] > 0:
        segments.append((task["end"], task["resolution"], _DELAY_COLOR))
    elif task["delta"] < 0:
        segments.append((task["resolution"], task["end"], _ADVANCE_COLOR))
    for start, end, color in segments:
        clipped_start = max(start, week_start_day)
        clipped_end = min(end, week_end_day)
        if clipped_end <= clipped_start:
            continue
        for seg_start, seg_end in _split_business_segments(clipped_start, clipped_end, anchor, work_weekends):
            yield seg_start - week_start_day, seg_end - week_start_day, color


def _clip_task_to_week(task: dict, week_start_day: float, week_end_day: float):
    """PATCH 90 — Découpe les segments (barre normale + retard/avance)
    d'une sous-tâche sur l'étendue [week_start_day, week_end_day),
    en coordonnées "jour dans la semaine" (0-7). Ne produit rien pour
    les semaines que la sous-tâche ne traverse pas."""
    segments = [(task["start"], task["end"], QColor(task["color"]))]
    if task["delta"] > 0:
        segments.append((task["end"], task["resolution"], _DELAY_COLOR))
    elif task["delta"] < 0:
        segments.append((task["resolution"], task["end"], _ADVANCE_COLOR))
    for start, end, color in segments:
        clipped_start = max(start, week_start_day)
        clipped_end = min(end, week_end_day)
        if clipped_end > clipped_start:
            yield clipped_start - week_start_day, clipped_end - week_start_day, color


class _DeltaDialog(QDialog):
    """Pop-up d'édition de l'écart (retard/avance) d'une sous-tâche.

    PATCH 90 — la saisie précise se fait toujours en jours (l'ancien
    sélecteur "Jours"/"Mois" est remplacé par le menu "Format"
    micro/macro, qui ne concerne que l'affichage du graphique, plus la
    saisie).
    """

    def __init__(self, task_label: str, current_delta_days: float, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{tr('dep_gantt.delta')} — {task_label}")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{tr('dep_gantt.delta_hint')} {tr('dep_gantt.days').lower()} :", self))
        self._spin = QDoubleSpinBox(self)
        self._spin.setRange(-999, 999)
        self._spin.setDecimals(2)
        self._spin.setValue(current_delta_days)
        layout.addWidget(self._spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value_in_days(self) -> float:
        return self._spin.value()


class DependencyGanttBlockWidget(QWidget):
    """Widget d'un DependencyGanttBlock : sélecteurs de source + graphique."""

    def __init__(self, block: DependencyGanttBlock, document, parent=None) -> None:
        super().__init__(parent)
        self._block = block
        self._document = document
        self._syncing = False
        # PATCH 71 — tant que True, le zoom suit automatiquement la
        # largeur visible (comportement historique "tout voir") ; se
        # désactive dès que l'utilisateur touche au curseur/boutons ±,
        # se réactive via le bouton "Auto".
        self._zoom_auto = True
        self._syncing_zoom = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        selectors = QHBoxLayout()
        self._combos: dict[str] = {}
        for key, label in (
            ("table", tr("formula.table_prefix")),
            ("label", tr("dep_gantt.subtasks")),
            ("person", tr("dep_gantt.people")),
            ("duration", tr("dep_gantt.duration")),
            ("risk", tr("dep_gantt.risks")),
            ("dependency", tr("dep_gantt.dependencies")),
            ("delta", tr("dep_gantt.deltas")),
            ("phase", tr("dep_gantt.phases")),
        ):
            selectors.addWidget(QLabel(f"{label} :", self))
            combo = NoScrollComboBox(self)
            combo.currentIndexChanged.connect(self._on_source_changed)
            selectors.addWidget(combo, 1)
            self._combos[key] = combo
        layout.addLayout(selectors)

        # PATCH 90 — remplace l'ancien sélecteur "Unité" (Jours/Mois) par
        # "Format" (Micro/Macro) : micro garde l'axe continu (désormais
        # gradué en jours puis mois de façon adaptative selon le zoom),
        # macro affiche un calendrier hebdomadaire.
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel(tr("dep_gantt.format"), self))
        self._format_combo = NoScrollComboBox(self)
        self._format_combo.addItem(tr("dep_gantt.micro"), FORMAT_MICRO)
        self._format_combo.addItem(tr("dep_gantt.macro"), FORMAT_MACRO)
        index = self._format_combo.findData(self._block.chart_format)
        self._format_combo.setCurrentIndex(index if index >= 0 else 0)
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_row.addWidget(self._format_combo)
        format_row.addStretch(1)
        layout.addLayout(format_row)

        # PATCH 91 — "Jour 0" optionnel : ancre le planning (toujours
        # calculé en jours relatifs) à une vraie date calendaire,
        # utilisée par le mode macro pour un calendrier réaliste (vrais
        # jours de semaine/dates, voir _paint_macro_calendar). Une case
        # à cocher rend la date explicitement optionnelle (QDateEdit
        # n'a pas d'état "vide" natif).
        start_date_row = QHBoxLayout()
        self._start_date_checkbox = QCheckBox(tr("dep_gantt.start_date"), self)
        self._start_date_edit = QDateEdit(self)
        self._start_date_edit.setCalendarPopup(True)
        self._start_date_edit.setDisplayFormat("dd/MM/yyyy")
        stored_start_date = self._block.start_date
        parsed = QDate.fromString(stored_start_date, "yyyy-MM-dd") if stored_start_date else QDate()
        self._start_date_checkbox.setChecked(parsed.isValid())
        self._start_date_edit.setDate(parsed if parsed.isValid() else QDate.currentDate())
        self._start_date_edit.setEnabled(parsed.isValid())
        self._start_date_checkbox.toggled.connect(self._on_start_date_toggled)
        self._start_date_edit.dateChanged.connect(self._on_start_date_changed)
        start_date_row.addWidget(self._start_date_checkbox)
        start_date_row.addWidget(self._start_date_edit)
        self._work_weekends_checkbox = QCheckBox(tr("dep_gantt.work_weekends"), self)
        self._work_weekends_checkbox.setChecked(self._block.work_weekends)
        # PATCH 93 — sans "Jour 0" configuré, le mode macro affiche un
        # calendrier relatif (_paint_macro_relative) qui n'a pas de
        # notion de weekend : "Travailler le weekend" n'a alors aucun
        # effet visible. Le griser évite de laisser croire que la case
        # fait quelque chose tant que "Jour 0" n'est pas actif.
        self._work_weekends_checkbox.setEnabled(parsed.isValid())
        self._work_weekends_checkbox.toggled.connect(self._on_work_weekends_toggled)
        start_date_row.addWidget(self._work_weekends_checkbox)
        start_date_row.addStretch(1)
        layout.addLayout(start_date_row)

        # PATCH 70 — curseur d'échelle (zoom) : agrandit/réduit le
        # nombre de pixels par jour, indépendamment de la largeur du bloc.
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel(tr("gantt.scale"), self))
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
        self._auto_button = QPushButton(tr("gantt.auto"), self)
        self._auto_button.setToolTip(tr("gantt.auto_tooltip"))
        self._auto_button.setFixedWidth(56)
        self._auto_button.clicked.connect(self._enable_auto_zoom)
        zoom_row.addWidget(self._auto_button)
        zoom_row.addStretch(1)
        layout.addLayout(zoom_row)

        self._canvas = _DependencyGanttCanvas(self)
        self._canvas.on_bar_clicked = self._on_bar_clicked
        self._canvas.on_bar_drag_moved = self._on_bar_drag_moved
        self._canvas.on_bar_drag_finished = self._on_bar_drag_finished
        self._canvas.set_format(self._block.chart_format)
        self._canvas.set_start_date(self._block.start_date)
        self._canvas.set_work_weekends(self._block.work_weekends)
        # PATCH 71 — zone de défilement STRICTEMENT horizontale : le
        # canvas garde toujours sa hauteur complète (jamais tronquée
        # verticalement), `widgetResizable=False` pour que sa largeur
        # ne soit jamais étirée par la zone de défilement (sinon le
        # zoom n'a plus d'effet visible).
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setFrameShape(QScrollArea.NoFrame)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setWidget(self._canvas)
        layout.addWidget(self._scroll_area)
        # PATCH 72 — `widgetResizable=False` ne fait pas suivre à la
        # QScrollArea la hauteur de son contenu toute seule : sans ce
        # câblage elle gardait sa hauteur par défaut (~192 px), ce qui
        # tronquait le graphique et affichait un ascenseur vertical dès
        # qu'il y avait beaucoup de personnes. On force sa hauteur à
        # toujours correspondre exactement à celle du canvas.
        self._canvas.on_geometry_changed = self._sync_scroll_height
        self._sync_scroll_height()

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
        combo.addItem(tr("formula.none"), None)
        for table in self._table_blocks():
            title = f"{tr('formula.table_prefix')} ({table.columns[0]['name']}...)" if table.columns else tr("formula.table_prefix")
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
            ("phase", available_phase_columns, self._block.phase_column_id),
        )
        for key, getter, current_id in specs:
            combo = self._combos[key]
            combo.clear()
            combo.addItem(tr("dep_gantt.none_fem"), None)
            if table is not None:
                for column in getter(table):
                    combo.addItem(column["name"] or tr("formula.unnamed"), column["id"])
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
                self._combos["phase"].currentData(),
            )
        self.refresh()

    def _on_format_changed(self) -> None:
        if self._syncing:
            return
        self._block.chart_format = self._format_combo.currentData()
        self._canvas.set_format(self._block.chart_format)
        self._zoom_auto = True
        self._sync_auto_zoom()
        self.refresh()

    def _on_start_date_toggled(self, checked: bool) -> None:
        """PATCH 91 — active/désactive le "Jour 0" (voir le commentaire
        à la construction de la case à cocher)."""
        self._start_date_edit.setEnabled(checked)
        self._work_weekends_checkbox.setEnabled(checked)
        self._block.start_date = self._start_date_edit.date().toString("yyyy-MM-dd") if checked else ""
        self._canvas.set_start_date(self._block.start_date)
        self.refresh()

    def _on_start_date_changed(self, qdate: QDate) -> None:
        if not self._start_date_checkbox.isChecked():
            return
        self._block.start_date = qdate.toString("yyyy-MM-dd")
        self._canvas.set_start_date(self._block.start_date)
        self.refresh()

    def _on_work_weekends_toggled(self, checked: bool) -> None:
        self._block.work_weekends = checked
        self._canvas.set_work_weekends(checked)
        self.refresh()

    # -- Zoom (PATCH 71) --------------------------------------------------

    def _nudge_zoom(self, delta: int) -> None:
        self._zoom_slider.setValue(self._zoom_slider.value() + delta)

    def _on_zoom_changed(self, value: int) -> None:
        self._zoom_label.setText(f"{value} %")
        self._canvas.set_zoom(value)
        if not self._syncing_zoom:
            # Ajustement manuel (curseur ou boutons ±) : on quitte le
            # mode "Auto" jusqu'à ce que l'utilisateur y revienne.
            self._zoom_auto = False

    def _enable_auto_zoom(self) -> None:
        self._zoom_auto = True
        self._sync_auto_zoom()

    def _sync_auto_zoom(self) -> None:
        """Calcule le zoom nécessaire pour que tout l'axe temporel
        tienne dans la largeur visible, et resynchronise le curseur
        (sans repasser en mode manuel, voir `_syncing_zoom`)."""
        if not self._zoom_auto:
            return
        viewport_width = self._scroll_area.viewport().width()
        available = max(viewport_width - _LABEL_WIDTH - 10, 20)
        ideal = available / self._canvas.base_content_width * 100
        target = max(_ZOOM_MIN, min(_ZOOM_MAX, math.floor(ideal)))
        self._syncing_zoom = True
        self._zoom_slider.setValue(target)
        self._syncing_zoom = False
        # setValue() n'émet pas valueChanged si la valeur ne change pas
        # (ex. redimensionnement négligeable) : on force quand même la
        # mise à jour du canvas pour rester exact.
        self._zoom_label.setText(f"{target} %")
        self._canvas.set_zoom(target)

    def _sync_scroll_height(self) -> None:
        """PATCH 73 — Aligne la hauteur de la zone de défilement sur
        celle du canvas (voir le commentaire au niveau de sa création),
        pour qu'elle prenne toujours toute la place verticale
        nécessaire, sans jamais tronquer ni faire défiler le contenu.
        La réserve pour la barre horizontale est lue via une métrique
        de style (PM_ScrollBarExtent, toujours disponible et non
        nulle) plutôt que `QScrollBar.sizeHint()`, qui peut renvoyer 0
        sur certains styles tant que la barre n'a encore jamais été
        affichée — ce qui, PATCH 72, ne lui laissait alors plus aucune
        place et la faisait purement disparaître, même quand le canvas
        dépassait bien la largeur visible."""
        reserve = self.style().pixelMetric(QStyle.PM_ScrollBarExtent) + 2
        self._scroll_area.setFixedHeight(self._canvas.height() + reserve)

    def resizeEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        super().resizeEvent(event)
        # PATCH 71 — différé au prochain passage de la boucle
        # d'événements : voir la note équivalente dans gantt_block_widget.py.
        QTimer.singleShot(0, self._sync_auto_zoom)

    def showEvent(self, event) -> None:  # noqa: N802 (nom imposé par Qt)
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_auto_zoom)

    # -- Édition de l'écart : clic-glissé direct (PATCH 57) ou pop-up
    # de saisie précise pour un simple clic (PATCH 49) -------------------

    def _apply_delta(self, row_id: str, value_days: float) -> None:
        """Écrit l'écart dans la colonne "Ecarts" si configurée, sinon
        dans le stockage historique propre au bloc (voir
        DependencyGanttBlock.set_delta)."""
        table = find_source_table(self._document, self._block)
        delta_column_id = self._block.delta_column_id
        if table is not None and delta_column_id is not None:
            table.set_cell(row_id, delta_column_id, str(value_days))
        else:
            self._block.set_delta(row_id, value_days)

    def _on_bar_clicked(self, task: dict) -> None:
        dialog = _DeltaDialog(task["label"], task["delta"], parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        self._apply_delta(task["row_id"], dialog.value_in_days())
        self.refresh()

    def _on_bar_drag_moved(self, row_id: str, delta_days: float) -> None:
        """PATCH 57 — appelé en continu pendant le clic-glissé d'un
        bâtonnet : écrit la nouvelle valeur et redessine immédiatement,
        pour un ajustement visuel en temps réel (même principe que le
        séparateur ajustable des "Checklists liées")."""
        self._apply_delta(row_id, delta_days)
        self.refresh()

    def _on_bar_drag_finished(self, row_id: str) -> None:
        # La valeur est déjà à jour (écrite à chaque _on_bar_drag_moved) ;
        # rien de plus à faire ici, hormis un dernier rafraîchissement.
        self.refresh()

    # -- Rafraîchissement -------------------------------------------------

    def refresh(self) -> None:
        self._canvas.set_schedule(compute_schedule(self._document, self._block))
        QTimer.singleShot(0, self._sync_auto_zoom)
