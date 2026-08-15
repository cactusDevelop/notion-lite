"""
PATCH 51, révisé PATCH 90 — Vérifie que le pas de graduation de l'axe
temporel du Gantt (dépendances), en mode micro, est toujours "rond"
(jamais fractionnaire), grandit avec l'échelle affichée, et suit la
progression adaptative 1J, 2J, 4J, 8J, 16J, 1M, 2M... (bascule vers
les mois une fois 16 jours dépassé).
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.blocks.dependency_gantt_block_widget import _micro_axis_step  # noqa: E402


def test_step_is_never_fractional():
    for value in (0.4, 1, 3, 8, 12, 40, 90, 400, 1200):
        step, _ = _micro_axis_step(value)
        assert step >= 1
        assert step == int(step)


def test_step_grows_as_scale_grows():
    steps = [_micro_axis_step(v)[0] for v in (3, 40, 90, 400, 1200)]
    assert steps == sorted(steps)
    assert steps[0] < steps[-1]


def test_step_follows_micro_progression_in_days():
    """1J, 2J, 4J, 8J, 16J : progression par doublement tant que le pas
    reste sous le seuil "mois" (30 jours)."""
    assert _micro_axis_step(8) == (1.0, "J")
    assert _micro_axis_step(9) == (2.0, "J")
    assert _micro_axis_step(16) == (2.0, "J")
    assert _micro_axis_step(17) == (4.0, "J")
    assert _micro_axis_step(64) == (8.0, "J")
    assert _micro_axis_step(128) == (16.0, "J")


def test_step_switches_to_months_beyond_sixteen_days():
    """1M, 2M... : une fois 16J dépassé, le pas continue de doubler
    mais exprimé en mois (30 jours) plutôt qu'en jours."""
    assert _micro_axis_step(129) == (30.0, "M")
    assert _micro_axis_step(240) == (30.0, "M")
    assert _micro_axis_step(241) == (60.0, "M")
