"""PATCH 95 — clic gauche = surlignage bleu (visuel), clic droit = force
le jour comme ouvré/non ouvré (exception ponctuelle), sur les cases-date
du calendrier réaliste du mode macro.
"""
from __future__ import annotations

import os
import sys
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.table_block import COLUMN_TYPE_NUMBER, COLUMN_TYPE_TEXT, TableBlock
from core.document import Document
from ui.blocks.dependency_gantt_block_widget import DependencyGanttBlockWidget


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


def _build_document_and_block():
    doc = Document()
    table = TableBlock()
    label_col = table.add_column("Sous-tâches", col_type=COLUMN_TYPE_TEXT)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_NUMBER)
    doc.add_block(table)
    block = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        duration_column_id=duration_col["id"],
    )
    doc.add_block(block)
    return doc, block


def test_on_day_left_clicked_toggles_highlight(qapp):
    doc, block = _build_document_and_block()
    widget = DependencyGanttBlockWidget(block, doc)
    widget._on_day_left_clicked(date(2026, 8, 17))
    assert block.highlighted_days == ["2026-08-17"]
    assert widget._canvas._highlighted_days == {"2026-08-17"}
    widget._on_day_left_clicked(date(2026, 8, 17))
    assert block.highlighted_days == []
    assert widget._canvas._highlighted_days == set()


def test_on_day_right_clicked_marks_working_day(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)

    menu, mark_working, mark_off, reset_action = widget._build_day_context_menu("2026-08-22")
    assert reset_action is None
    widget._apply_day_context_menu_choice("2026-08-22", mark_working, mark_working, mark_off, reset_action)
    assert block.day_overrides == {"2026-08-22": True}
    assert widget._canvas._day_overrides == {"2026-08-22": True}


def test_on_day_right_clicked_marks_non_working_day(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)

    menu, mark_working, mark_off, reset_action = widget._build_day_context_menu("2026-08-17")
    widget._apply_day_context_menu_choice("2026-08-17", mark_off, mark_working, mark_off, reset_action)
    assert block.day_overrides == {"2026-08-17": False}


def test_on_day_right_clicked_reset_only_offered_with_existing_override(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    block.set_day_override("2026-08-22", True)
    widget = DependencyGanttBlockWidget(block, doc)

    menu, mark_working, mark_off, reset_action = widget._build_day_context_menu("2026-08-22")
    assert reset_action is not None
    widget._apply_day_context_menu_choice("2026-08-22", reset_action, mark_working, mark_off, reset_action)
    assert block.day_overrides == {}


def test_on_day_right_clicked_no_reset_action_without_existing_override(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)

    _, _, _, reset_action = widget._build_day_context_menu("2026-08-17")
    assert reset_action is None
