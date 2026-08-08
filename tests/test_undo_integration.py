"""
PATCH 27 — Vérifie que MainWindow._undo/_redo couvrent bien des
actions de nature différente (ajout de bloc, édition de texte),
sans dépendre du timer de sondage (flush synchrone).
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(qapp):
    return MainWindow()


def test_undo_reverts_block_addition(window):
    before = len(window._document)
    window._append_block_from_command("quote")
    assert len(window._document) == before + 1

    window._undo()

    assert len(window._document) == before


def test_redo_restores_block_addition(window):
    before = len(window._document)
    window._append_block_from_command("quote")
    window._undo()
    assert len(window._document) == before

    window._redo()

    assert len(window._document) == before + 1


def test_undo_reverts_text_edit_without_waiting_for_poll(window):
    block = window._document.blocks[0]
    original = block.content

    block.content = "Édité sans passer par le timer"
    window._undo()  # flush synchrone, pas de _poll_undo_snapshot() appelé

    assert window._document.blocks[0].content == original


def test_undo_with_nothing_to_undo_is_a_noop(window):
    before = len(window._document)
    window._undo()
    assert len(window._document) == before


def test_new_action_clears_redo_after_undo(window):
    window._append_block_from_command("quote")
    window._undo()
    assert window._undo_history.can_redo()

    window._append_block_from_command("code")
    window._poll_undo_snapshot()  # équivalent du sondage périodique (600 ms)

    assert not window._undo_history.can_redo()
