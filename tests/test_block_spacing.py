"""
PATCH 51 — Vérifie que l'option d'espacement (activée par défaut)
ajoute une marge au-dessus des titres, tableaux et graphiques, mais
pas des autres types de blocs (texte, checklist, ...).
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.bar_chart_block import BarChartBlock  # noqa: E402
from blocks.heading_block import HeadingBlock  # noqa: E402
from blocks.table_block import TableBlock  # noqa: E402
from blocks.text_block import TextBlock  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.settings import get_block_spacing, set_block_spacing  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(qapp):
    return MainWindow()


@pytest.fixture(autouse=True)
def _restore_block_spacing_setting():
    original = get_block_spacing()
    yield
    set_block_spacing(original)


def test_block_spacing_enabled_by_default():
    assert get_block_spacing() is True


def test_wrap_applies_margin_to_heading_and_table_but_not_text(window):
    set_block_spacing(True)
    heading = HeadingBlock(level=1, content="Titre")
    table = TableBlock()
    chart = BarChartBlock()
    text = TextBlock(content="Bonjour")
    for block in (heading, table, chart, text):
        window._document.add_block(block)

    heading_container = window._wrap(window._create_content_widget_for_block(heading), heading.id)
    table_container = window._wrap(window._create_content_widget_for_block(table), table.id)
    chart_container = window._wrap(window._create_content_widget_for_block(chart), chart.id)
    text_container = window._wrap(window._create_content_widget_for_block(text), text.id)

    assert heading_container.layout().contentsMargins().top() > 0
    assert table_container.layout().contentsMargins().top() > 0
    assert chart_container.layout().contentsMargins().top() > 0
    assert text_container.layout().contentsMargins().top() == 0


def test_wrap_applies_no_margin_when_disabled(window):
    set_block_spacing(False)
    heading = HeadingBlock(level=1, content="Titre")
    window._document.add_block(heading)

    container = window._wrap(window._create_content_widget_for_block(heading), heading.id)

    assert container.layout().contentsMargins().top() == 0
