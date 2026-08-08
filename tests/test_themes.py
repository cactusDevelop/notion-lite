from __future__ import annotations

import os
import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.themes.theme import (  # noqa: E402
    THEME_DARK,
    THEME_HIGH_CONTRAST,
    THEME_LABELS,
    THEME_LIGHT,
    THEME_SEPIA,
    THEMES,
    apply_theme,
    build_palette,
    cycle_theme,
    current_theme,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_all_themes_have_a_label():
    for theme_name in THEMES:
        assert theme_name in THEME_LABELS
        assert THEME_LABELS[theme_name]


def test_at_least_four_themes_available():
    assert len(THEMES) >= 4
    assert {THEME_LIGHT, THEME_DARK, THEME_SEPIA, THEME_HIGH_CONTRAST} <= set(THEMES)


def test_each_theme_builds_a_distinct_palette():
    from PySide6.QtGui import QPalette

    palettes = {name: build_palette(name).color(QPalette.Window).name() for name in THEMES}
    assert len(set(palettes.values())) == len(THEMES)


def test_apply_each_theme(qapp):
    for theme_name in THEMES:
        apply_theme(qapp, theme_name)
        assert current_theme(qapp) == theme_name


def test_cycle_theme_visits_all_and_wraps(qapp):
    apply_theme(qapp, THEMES[0])
    seen = [current_theme(qapp)]
    for _ in range(len(THEMES) - 1):
        seen.append(cycle_theme(qapp))
    assert seen == THEMES

    # Un tour de plus revient au premier thème (boucle).
    assert cycle_theme(qapp) == THEMES[0]
