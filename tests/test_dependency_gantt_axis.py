"""
PATCH 51 — Vérifie que le pas de graduation de l'axe temporel du
Gantt (dépendances) est toujours un nombre entier "rond" (jamais de
type 0.1), et qu'il grandit avec l'échelle affichée (dézoomer donne
des graduations plus espacées).
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.blocks.dependency_gantt_block_widget import _nice_axis_step  # noqa: E402


def test_step_is_never_fractional():
    for value in (0.4, 1, 3, 8, 12, 40, 90, 400, 1200):
        step = _nice_axis_step(value)
        assert step >= 1
        assert step == int(step)


def test_step_grows_as_scale_grows():
    steps = [_nice_axis_step(v) for v in (3, 40, 90, 400, 1200)]
    assert steps == sorted(steps)
    assert steps[0] < steps[-1]


def test_step_matches_expected_nice_numbers():
    assert _nice_axis_step(8) == 1
    assert _nice_axis_step(12) == 2
    assert _nice_axis_step(40) == 5
