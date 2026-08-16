"""
PATCH 90 — Vérifie que "Sauvegarder sous" ouvre le dialogue directement
dans le dossier du projet courant (racine trouvée via
`find_project_root`) quand le document est déjà sauvegardé sur disque,
plutôt que sur le dossier par défaut de Qt.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog  # noqa: E402

from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(qapp):
    return MainWindow()


def test_save_as_starts_in_current_project_root(window):
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        doc_path = project_dir / "document.json"
        doc_path.write_text("{}", encoding="utf-8")
        window._current_file = doc_path

        with mock.patch.object(
            QFileDialog, "getSaveFileName", return_value=("", "")
        ) as mocked:
            window._save_document_as()

        args, kwargs = mocked.call_args
        start_dir = args[2] if len(args) > 2 else kwargs.get("dir", "")
        assert start_dir == str(project_dir)


def test_save_as_starts_empty_when_no_current_file(window):
    window._current_file = None

    from PySide6.QtWidgets import QFileDialog

    with mock.patch.object(
        QFileDialog, "getSaveFileName", return_value=("", "")
    ) as mocked:
        window._save_document_as()

    args, kwargs = mocked.call_args
    start_dir = args[2] if len(args) > 2 else kwargs.get("dir", "")
    assert start_dir == ""
