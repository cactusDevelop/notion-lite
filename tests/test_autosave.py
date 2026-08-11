"""
PATCH 51 — Vérifie que la sauvegarde automatique réécrit le fichier
courant dès qu'une modification est détectée par le sondage undo,
uniquement si l'option est activée et qu'un fichier a déjà été
sauvegardé une première fois.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.text_block import TextBlock  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.settings import get_autosave_enabled, set_autosave_enabled  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(qapp):
    return MainWindow()


@pytest.fixture(autouse=True)
def _restore_autosave_setting():
    original = get_autosave_enabled()
    yield
    set_autosave_enabled(original)


def _read_text_contents(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [b.get("data", {}).get("content") for b in data["blocks"] if b.get("type") == "text"]


def test_autosave_enabled_by_default():
    assert get_autosave_enabled() is True


def test_maybe_autosave_does_nothing_without_current_file(window):
    set_autosave_enabled(True)
    window._current_file = None
    window._document.add_block(TextBlock(content="jamais sauvegardé"))
    # Ne doit pas lever d'exception ni tenter d'écrire quoi que ce soit.
    window._maybe_autosave()


def test_maybe_autosave_writes_to_current_file_when_enabled(window, tmp_path):
    set_autosave_enabled(True)
    path = tmp_path / "doc.json"
    window._write_document(path)

    window._document.add_block(TextBlock(content="ajouté après la première sauvegarde"))
    window._maybe_autosave()

    assert "ajouté après la première sauvegarde" in _read_text_contents(path)


def test_maybe_autosave_skipped_when_disabled(window, tmp_path):
    path = tmp_path / "doc.json"
    window._write_document(path)
    set_autosave_enabled(False)

    window._document.add_block(TextBlock(content="ne doit pas être sauvegardé"))
    window._maybe_autosave()

    assert "ne doit pas être sauvegardé" not in _read_text_contents(path)


def test_poll_undo_snapshot_triggers_autosave_on_real_change(window, tmp_path):
    set_autosave_enabled(True)
    path = tmp_path / "doc.json"
    window._write_document(path)

    window._document.add_block(TextBlock(content="détecté par le sondage undo"))
    window._poll_undo_snapshot()

    assert "détecté par le sondage undo" in _read_text_contents(path)
