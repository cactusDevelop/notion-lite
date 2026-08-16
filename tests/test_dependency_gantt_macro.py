"""
PATCH 90 — Vérifie le mode "macro" (calendrier) du Gantt (dépendances) :
découpage des bâtonnets par semaine (`_clip_task_to_week`), et
géométrie du canvas (une ligne de 7 cases par semaine, hauteur
dépendant du nombre de personnes).
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from datetime import date

from blocks.dependency_gantt_block import FORMAT_MACRO, FORMAT_MICRO
from ui.blocks.dependency_gantt_block_widget import (
    _MACRO_HEADER_H,
    _MACRO_PERSON_ROW_H,
    _MACRO_WEEK_GAP,
    _MACRO_WEEKDAY_HEADER_H,
    _DependencyGanttCanvas,
    _clip_task_to_week,
    _clip_task_to_week_business,
    _format_month_year,
    _split_business_segments,
)


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


def _task(start, end, delta=0.0, resolution=None):
    return {
        "start": start,
        "end": end,
        "resolution": resolution if resolution is not None else end + delta,
        "delta": delta,
        "color": "#4db6ac",
    }


def test_clip_task_to_week_splits_across_week_boundary():
    task = _task(5, 10)
    week0 = list(_clip_task_to_week(task, 0, 7))
    week1 = list(_clip_task_to_week(task, 7, 14))
    assert week0 == [(5, 7, QColor("#4db6ac"))]
    assert week1 == [(0, 3, QColor("#4db6ac"))]


def test_clip_task_to_week_ignores_untouched_weeks():
    task = _task(1, 3)
    assert list(_clip_task_to_week(task, 7, 14)) == []


def test_clip_task_to_week_includes_delay_segment():
    task = _task(1, 3, delta=2.0, resolution=5.0)
    segments = list(_clip_task_to_week(task, 0, 7))
    assert (1, 3, QColor("#4db6ac")) in segments
    delay_segment = [s for s in segments if s[0] == 3.0][0]
    assert delay_segment[1] == 5.0


def test_clip_task_to_week_includes_advance_segment():
    task = _task(1, 5, delta=-2.0, resolution=3.0)
    segments = list(_clip_task_to_week(task, 0, 7))
    advance_segment = [s for s in segments if s[0] == 3.0][0]
    assert advance_segment[1] == 5.0


def test_macro_geometry_has_seven_columns_and_scales_with_people(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_format(FORMAT_MACRO)
    canvas.set_schedule(
        [
            {
                "row_id": "r1",
                "label": "Tâche 1",
                "person_names": ["Alice"],
                "start": 0.0,
                "end": 3.0,
                "resolution": 3.0,
                "delta": 0.0,
                "color": "#4db6ac",
                "phase": "",
            },
            {
                "row_id": "r2",
                "label": "Tâche 2",
                "person_names": ["Bob"],
                "start": 8.0,
                "end": 12.0,
                "resolution": 12.0,
                "delta": 0.0,
                "color": "#4db6ac",
                "phase": "",
            },
        ]
    )
    cell_w = canvas._macro_cell_width()
    expected_width = 120 + 7 * cell_w + 10  # _LABEL_WIDTH == 120
    assert canvas.width() == expected_width

    # 12 jours -> 2 semaines ; 2 personnes -> 2 lignes par semaine.
    week_h = _MACRO_HEADER_H + 2 * _MACRO_PERSON_ROW_H
    expected_height = 2 * week_h + _MACRO_WEEK_GAP + 10
    assert canvas.height() == expected_height


def test_switching_back_to_micro_restores_linear_geometry(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_schedule(
        [
            {
                "row_id": "r1",
                "label": "Tâche 1",
                "person_names": ["Alice"],
                "start": 0.0,
                "end": 3.0,
                "resolution": 3.0,
                "delta": 0.0,
                "color": "#4db6ac",
                "phase": "",
            }
        ]
    )
    canvas.set_format(FORMAT_MACRO)
    canvas.set_format(FORMAT_MICRO)
    # En micro, la largeur dépend de max_x_days * pixels/jour, pas des
    # 7 colonnes fixes du calendrier : elle doit redevenir raisonnable
    # pour une étendue de 3 jours (bien plus étroite que le calendrier).
    assert canvas.width() < 200


# -- PATCH 91 : calendrier réaliste avec "Jour 0" -------------------------


def test_calendar_weeks_start_on_monday_even_if_day_zero_does_not(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_schedule(
        [
            {
                "row_id": "r1",
                "label": "Tâche",
                "person_names": ["Alice"],
                "start": 0.0,
                "end": 2.0,
                "resolution": 2.0,
                "delta": 0.0,
                "color": "#4db6ac",
                "phase": "",
            }
        ]
    )
    canvas.set_format(FORMAT_MACRO)
    # 2026-08-19 est un mercredi ; le "Jour 0" n'a pas à tomber un lundi.
    canvas.set_start_date("2026-08-19")
    calendar_start, weeks = canvas._macro_calendar_weeks()
    assert calendar_start == date(2026, 8, 17)  # lundi de cette semaine-là
    assert calendar_start.weekday() == 0
    assert weeks >= 1


def test_geometry_reserves_weekday_header_only_in_calendar_mode(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_schedule(
        [
            {
                "row_id": "r1",
                "label": "Tâche",
                "person_names": ["Alice"],
                "start": 0.0,
                "end": 2.0,
                "resolution": 2.0,
                "delta": 0.0,
                "color": "#4db6ac",
                "phase": "",
            }
        ]
    )
    canvas.set_format(FORMAT_MACRO)
    height_without_date = canvas.height()
    canvas.set_start_date("2026-08-19")
    height_with_date = canvas.height()
    assert height_with_date == height_without_date + _MACRO_WEEKDAY_HEADER_H


def test_set_start_date_falls_back_to_relative_calendar_on_empty_or_invalid(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_format(FORMAT_MACRO)
    canvas.set_start_date("2026-08-19")
    assert canvas._start_date is not None
    canvas.set_start_date("")
    assert canvas._start_date is None
    canvas.set_start_date("pas une date")
    assert canvas._start_date is None


def test_format_month_year_uses_localized_month_name():
    assert _format_month_year(date(2026, 8, 19)) == "Août 2026"
    assert _format_month_year(date(2026, 1, 1)) == "Janvier 2026"


def test_weekend_color_defaults_to_off_and_is_toggleable(qapp):
    canvas = _DependencyGanttCanvas()
    assert canvas._work_weekends is False
    canvas.set_work_weekends(True)
    assert canvas._work_weekends is True
    canvas.set_work_weekends(False)
    assert canvas._work_weekends is False


def test_weekend_color_is_derived_from_palette_not_a_fixed_hex(qapp):
    """PATCH 92 — la teinte des week-ends doit rester visible aussi bien
    en thème clair qu'en thème sombre : elle doit donc être calculée à
    partir de la couleur de fond courante plutôt que fixée en dur."""
    canvas = _DependencyGanttCanvas()
    weekend_color = canvas._weekend_color()
    base_color = canvas.palette().color(QPalette.Base)
    assert weekend_color != base_color
    if base_color.lightness() > 128:
        assert weekend_color.lightness() < base_color.lightness()
    else:
        assert weekend_color.lightness() > base_color.lightness()


# PATCH 93 — _business_to_calendar_offset : la barre ne doit pas empiéter
# sur les cases grisées du weekend quand "Travailler le weekend" est
# désactivé (les jours stockés par compute_schedule sont toujours des
# jours ouvrés continus, sans notion de weekend).


def test_business_to_calendar_offset_is_identity_when_work_weekends(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas.set_work_weekends(True)
    assert canvas._business_to_calendar_offset(6) == 6


def test_business_to_calendar_offset_skips_weekend_when_disabled(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas.set_work_weekends(False)
    # 5 jours ouvrés (lun-ven) -> frontière samedi, aucun weekend traversé.
    assert canvas._business_to_calendar_offset(5) == 5
    # 6e jour ouvré -> samedi + dimanche sautés avant de compter le lundi
    # suivant : 5 (semaine 1) + 2 (weekend) + 1 (lundi) = 8.
    assert canvas._business_to_calendar_offset(6) == 8


def test_business_to_calendar_offset_handles_fractional_day(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas.set_work_weekends(False)
    # 5.5 jours ouvrés : les 5 premiers jours ouvrés se terminent au
    # samedi (offset 5) ; la demi-journée restante tombe sur le lundi
    # suivant (offset entier 7, weekend sauté) -> 7.5.
    assert canvas._business_to_calendar_offset(5.5) == 7.5


def test_macro_calendar_weeks_accounts_for_skipped_weekends(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas._max_x_days = 6.0
    canvas.set_work_weekends(True)
    _, weeks_work = canvas._macro_calendar_weeks()
    canvas.set_work_weekends(False)
    _, weeks_off = canvas._macro_calendar_weeks()
    assert weeks_off >= weeks_work


# PATCH 94 — _split_business_segments / _clip_task_to_week_business : le
# rectangle peint ne doit plus traverser visuellement un weekend, même
# quand les bornes converties l'enjambent déjà numériquement.


def test_split_business_segments_breaks_at_weekend():
    anchor = date(2026, 8, 17)  # lundi
    # Segment jeudi(3)->mardi suivant(8), calendaire (après conversion) :
    # doit se scinder en jeu-ven (3-5) et lundi-mardi (7-8), sans le
    # week-end (5-7).
    is_working_day = lambda d: d.weekday() < 5
    segments = list(_split_business_segments(3.0, 8.0, anchor, is_working_day))
    assert segments == [(3.0, 5.0), (7.0, 8.0)]


def test_split_business_segments_noop_when_work_weekends(qapp):
    anchor = date(2026, 8, 17)
    segments = list(_split_business_segments(3.0, 8.0, anchor, lambda d: True))
    assert segments == [(3.0, 8.0)]


def test_clip_task_to_week_business_skips_weekend_columns():
    anchor = date(2026, 8, 17)  # lundi, semaine = jours 0..7
    task = _task(3, 8)  # jeu -> mardi suivant, comme ci-dessus
    is_working_day = lambda d: d.weekday() < 5
    pieces = list(_clip_task_to_week_business(task, 0, 7, anchor, is_working_day))
    # dans la semaine courante (0-7), seul jeu-ven (3-5) est produit :
    # le lundi suivant tombe dans la semaine d'après.
    assert pieces == [(3.0, 5.0, QColor(task["color"]))]


def test_split_business_segments_respects_day_override():
    """PATCH 95 — une exception ponctuelle (jour normalement ouvré
    marqué comme non ouvré) doit couper le bâtonnet, même en semaine."""
    anchor = date(2026, 8, 17)  # lundi

    def is_working_day(d):
        return d != date(2026, 8, 19)  # mercredi forcé non ouvré

    segments = list(_split_business_segments(0.0, 4.0, anchor, is_working_day))
    assert segments == [(0.0, 2.0), (3.0, 4.0)]


# PATCH 95 — exceptions ponctuelles (clic droit) et surlignage bleu
# (clic gauche) sur les cases-date du calendrier réaliste.


def test_is_working_day_default_follows_work_weekends(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas.set_work_weekends(False)
    assert canvas._is_working_day(date(2026, 8, 21)) is True  # vendredi
    assert canvas._is_working_day(date(2026, 8, 22)) is False  # samedi
    canvas.set_work_weekends(True)
    assert canvas._is_working_day(date(2026, 8, 22)) is True


def test_is_working_day_override_wins_over_weekday(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")  # lundi
    canvas.set_work_weekends(False)
    # Samedi normalement non ouvré, forcé ouvré par override.
    canvas.set_day_overrides({"2026-08-22": True})
    assert canvas._is_working_day(date(2026, 8, 22)) is True
    # Un lundi normalement ouvré, forcé non ouvré.
    canvas.set_day_overrides({"2026-08-17": False})
    assert canvas._is_working_day(date(2026, 8, 17)) is False


def test_day_at_returns_matching_cell_date(qapp):
    canvas = _DependencyGanttCanvas()
    canvas._day_cell_rects = [(QRect(0, 0, 10, 10), date(2026, 8, 17))]
    assert canvas._day_at(QPoint(5, 5)) == date(2026, 8, 17)
    assert canvas._day_at(QPoint(50, 50)) is None


def test_paint_macro_calendar_populates_day_cell_rects(qapp):
    canvas = _DependencyGanttCanvas()
    canvas.set_start_date("2026-08-17")
    canvas.set_format(FORMAT_MACRO)
    canvas.set_schedule(
        [
            {
                "row_id": "r1",
                "label": "Tâche 1",
                "person_names": ["Alice"],
                "start": 0.0,
                "end": 3.0,
                "resolution": 3.0,
                "delta": 0.0,
                "color": "#4db6ac",
            }
        ]
    )
    canvas.grab()  # force un paintEvent
    assert len(canvas._day_cell_rects) > 0
    assert all(isinstance(day, date) for _, day in canvas._day_cell_rects)
