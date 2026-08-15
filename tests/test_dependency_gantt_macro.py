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
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from blocks.dependency_gantt_block import FORMAT_MACRO, FORMAT_MICRO
from ui.blocks.dependency_gantt_block_widget import (
    _MACRO_HEADER_H,
    _MACRO_PERSON_ROW_H,
    _MACRO_WEEK_GAP,
    _DependencyGanttCanvas,
    _clip_task_to_week,
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
