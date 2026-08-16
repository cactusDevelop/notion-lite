"""PATCH 96 — clic droit = une seule case à cocher "Jour ouvré" (un
jour n'est que ouvré OU non ouvré), plus "Réinitialiser" si une
exception ponctuelle existe déjà, sur les cases-date du calendrier
réaliste du mode macro. PATCH 97 — le clic gauche (ex-surlignage bleu,
purement visuel et sans effet, retiré) n'est plus testé ici.
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


def test_toggle_action_reflects_default_state_and_flips_it(qapp):
    """Samedi, sans exception : la case part décochée (non ouvré par
    défaut) ; la cocher force le jour comme ouvré."""
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"  # lundi
    widget = DependencyGanttBlockWidget(block, doc)
    saturday = date(2026, 8, 22)

    menu, toggle_action, reset_action, effective = widget._build_day_context_menu(saturday)
    assert effective is False
    assert toggle_action.isChecked() is False
    assert reset_action is None

    widget._apply_day_context_menu_choice(saturday.isoformat(), toggle_action, toggle_action, reset_action, effective)
    assert block.day_overrides == {"2026-08-22": True}
    assert widget._canvas._day_overrides == {"2026-08-22": True}


def test_toggle_action_on_working_day_forces_it_off(qapp):
    """Lundi, sans exception : la case part cochée (ouvré par défaut) ;
    la décocher force le jour comme non ouvré."""
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"  # lundi
    widget = DependencyGanttBlockWidget(block, doc)
    monday = date(2026, 8, 17)

    menu, toggle_action, reset_action, effective = widget._build_day_context_menu(monday)
    assert effective is True
    assert toggle_action.isChecked() is True

    widget._apply_day_context_menu_choice(monday.isoformat(), toggle_action, toggle_action, reset_action, effective)
    assert block.day_overrides == {"2026-08-17": False}


def test_reset_action_only_offered_with_existing_override(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    block.set_day_override("2026-08-22", True)
    widget = DependencyGanttBlockWidget(block, doc)
    saturday = date(2026, 8, 22)

    menu, toggle_action, reset_action, effective = widget._build_day_context_menu(saturday)
    assert reset_action is not None
    assert effective is True
    assert toggle_action.isChecked() is True

    widget._apply_day_context_menu_choice(
        saturday.isoformat(), reset_action, toggle_action, reset_action, effective
    )
    assert block.day_overrides == {}


def test_left_click_on_day_cell_has_no_visible_effect(qapp):
    """PATCH 97 — régression : un clic gauche sur une case-date ne doit
    plus rien surligner (l'ancien surlignage bleu, purement visuel et
    sans effet sur le planning, a été retiré)."""
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    assert not hasattr(widget, "_on_day_left_clicked")
    assert not hasattr(widget._canvas, "on_day_left_clicked")
    assert not hasattr(widget._canvas, "_highlighted_days")


def test_no_reset_action_without_existing_override(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)

    _, _, reset_action, _ = widget._build_day_context_menu(date(2026, 8, 17))
    assert reset_action is None
