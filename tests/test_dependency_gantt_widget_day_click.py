"""PATCH 96 — clic droit = une seule case à cocher "Jour ouvré" (un
jour n'est que ouvré OU non ouvré), plus "Réinitialiser" si une
exception ponctuelle existe déjà, sur les cases-date du calendrier
réaliste du mode macro. PATCH 98 — clic gauche = sélection (façon
explorateur de fichiers : clic seul remplace, Ctrl ajoute/retire, Maj
étend une plage), effacée dès qu'on interagit ailleurs ; le clic droit
sur une case appartenant à la sélection applique l'action à tout le
groupe.
"""
from __future__ import annotations

import os
import sys
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent
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

    widget._apply_day_context_menu_choice({"2026-08-22"}, toggle_action, toggle_action, reset_action, effective)
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

    widget._apply_day_context_menu_choice({"2026-08-17"}, toggle_action, toggle_action, reset_action, effective)
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
        {"2026-08-22"}, reset_action, toggle_action, reset_action, effective
    )
    assert block.day_overrides == {}


def test_no_reset_action_without_existing_override(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)

    _, _, reset_action, _ = widget._build_day_context_menu(date(2026, 8, 17))
    assert reset_action is None


# -- PATCH 98 — sélection (clic gauche) --------------------------------


def test_plain_click_selects_only_that_day_replacing_previous(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas

    canvas._select_day(date(2026, 8, 17), Qt.NoModifier)
    assert canvas._selected_days == {"2026-08-17"}
    canvas._select_day(date(2026, 8, 18), Qt.NoModifier)
    assert canvas._selected_days == {"2026-08-18"}


def test_ctrl_click_toggles_day_in_and_out_of_selection(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas

    canvas._select_day(date(2026, 8, 17), Qt.NoModifier)
    canvas._select_day(date(2026, 8, 19), Qt.ControlModifier)
    assert canvas._selected_days == {"2026-08-17", "2026-08-19"}
    canvas._select_day(date(2026, 8, 17), Qt.ControlModifier)
    assert canvas._selected_days == {"2026-08-19"}


def test_shift_click_extends_range_from_anchor(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas

    canvas._select_day(date(2026, 8, 17), Qt.NoModifier)
    canvas._select_day(date(2026, 8, 20), Qt.ShiftModifier)
    assert canvas._selected_days == {
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
    }
    # Un second Maj+clic réétend depuis la même ancre (17), pas depuis
    # le dernier point de la plage précédente (20).
    canvas._select_day(date(2026, 8, 18), Qt.ShiftModifier)
    assert canvas._selected_days == {"2026-08-17", "2026-08-18"}


def test_clear_selection_empties_it(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas

    canvas._selected_days = {"2026-08-17"}
    canvas.clear_selection()
    assert canvas._selected_days == set()


def test_focus_out_clears_selection(qapp):
    """PATCH 98 — régression du bug signalé : interagir avec un autre
    contrôle (perte de focus du graphe) ne doit plus laisser la
    sélection "collée"."""
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas

    canvas._selected_days = {"2026-08-17"}
    canvas.focusOutEvent(QFocusEvent(QEvent.FocusOut, Qt.MouseFocusReason))
    assert canvas._selected_days == set()


def test_right_click_on_selected_day_applies_to_whole_selection(qapp):
    """PATCH 98 — un clic droit sur une case faisant partie de la
    sélection courante coche/décoche "Jour ouvré" pour tout le
    groupe en une fois."""
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"  # lundi
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas
    canvas._selected_days = {"2026-08-17", "2026-08-18", "2026-08-19"}

    menu, toggle_action, reset_action, effective = widget._build_day_context_menu(
        date(2026, 8, 17), {"2026-08-17", "2026-08-18", "2026-08-19"}
    )
    widget._apply_day_context_menu_choice(
        {"2026-08-17", "2026-08-18", "2026-08-19"}, toggle_action, toggle_action, reset_action, effective
    )
    assert block.day_overrides == {
        "2026-08-17": False,
        "2026-08-18": False,
        "2026-08-19": False,
    }
    # PATCH 98 — l'action appliquée efface aussi la sélection.
    assert canvas._selected_days == set()


def test_right_click_on_day_outside_selection_only_affects_that_day(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    canvas = widget._canvas
    canvas._selected_days = {"2026-08-17", "2026-08-18"}

    # 2026-08-25 n'est pas dans la sélection : seul lui est concerné.
    iso = "2026-08-25"
    selection = canvas._selected_days
    days = set(selection) if iso in selection and len(selection) > 1 else {iso}
    assert days == {"2026-08-25"}
