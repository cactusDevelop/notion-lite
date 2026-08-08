from __future__ import annotations

import os
import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.themes.theme import (  # noqa: E402
    THEME_DARK,
    THEME_LIGHT,
    apply_theme,
    build_palette,
    current_theme,
    toggle_theme,
)
from PySide6.QtGui import QPalette  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_build_palette_differs_between_themes():
    light = build_palette(THEME_LIGHT)
    dark = build_palette(THEME_DARK)
    assert light.color(QPalette.Window) != dark.color(QPalette.Window)


def test_apply_theme_sets_current_theme(qapp):
    apply_theme(qapp, THEME_DARK)
    assert current_theme(qapp) == THEME_DARK

    apply_theme(qapp, THEME_LIGHT)
    assert current_theme(qapp) == THEME_LIGHT


def test_apply_theme_invalid_falls_back_to_light(qapp):
    apply_theme(qapp, "inconnu")
    assert current_theme(qapp) == THEME_LIGHT


def test_toggle_theme_switches_and_returns_new_value(qapp):
    apply_theme(qapp, THEME_LIGHT)
    assert toggle_theme(qapp) == THEME_DARK
    assert current_theme(qapp) == THEME_DARK
    assert toggle_theme(qapp) == THEME_LIGHT
    assert current_theme(qapp) == THEME_LIGHT
