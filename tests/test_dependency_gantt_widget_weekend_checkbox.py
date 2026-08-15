"""PATCH 93 — sans "Jour 0" configuré et valide, la case "Travailler le
weekend" n'a aucun effet visible (le mode macro relatif, sans date
calendaire, n'a pas de notion de weekend) : elle doit rester grisée et
non modifiable par l'utilisateur tant que "Jour 0" n'est pas actif.
"""
from __future__ import annotations

import os
import sys

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


def test_work_weekends_checkbox_disabled_without_day_zero(qapp):
    doc, block = _build_document_and_block()
    widget = DependencyGanttBlockWidget(block, doc)
    assert widget._start_date_checkbox.isChecked() is False
    assert widget._work_weekends_checkbox.isEnabled() is False


def test_work_weekends_checkbox_enabled_when_day_zero_toggled(qapp):
    doc, block = _build_document_and_block()
    widget = DependencyGanttBlockWidget(block, doc)
    widget._start_date_checkbox.setChecked(True)
    assert widget._work_weekends_checkbox.isEnabled() is True
    widget._start_date_checkbox.setChecked(False)
    assert widget._work_weekends_checkbox.isEnabled() is False


def test_work_weekends_checkbox_enabled_when_day_zero_already_set(qapp):
    doc, block = _build_document_and_block()
    block.start_date = "2026-08-17"
    widget = DependencyGanttBlockWidget(block, doc)
    assert widget._start_date_checkbox.isChecked() is True
    assert widget._work_weekends_checkbox.isEnabled() is True
