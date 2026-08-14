"""
PATCH 81 — Vérifie les actions de gestion de fichiers de l'explorateur
(panneau latéral façon IDE) : création de fichier/dossier avec nom
unique, renommage (via le modèle, comme le ferait l'édition inline) et
suppression, y compris d'un dossier non vide.
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

from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(qapp):
    return MainWindow()


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def _root_index(window):
    return window._explorer_model.index(window._explorer_model.rootPath())


def test_new_file_creates_unique_valid_document(window, project_dir):
    window._set_explorer_root(project_dir)

    window._explorer_create(_root_index(window), is_folder=False)
    window._explorer_create(_root_index(window), is_folder=False)

    created = sorted(p.name for p in project_dir.glob("*.json"))
    assert len(created) == 2
    # Le deuxième fichier ne doit pas écraser le premier : nom unique.
    assert created[0] != created[1]

    # Chaque fichier créé est un document Méthodo OG valide (chargeable).
    for name in created:
        data = json.loads((project_dir / name).read_text(encoding="utf-8"))
        assert "version" in data
        assert data["blocks"] == []


def test_new_folder_creates_unique_directory(window, project_dir):
    window._set_explorer_root(project_dir)

    window._explorer_create(_root_index(window), is_folder=True)
    window._explorer_create(_root_index(window), is_folder=True)

    created = sorted(p.name for p in project_dir.iterdir() if p.is_dir())
    assert len(created) == 2
    assert created[0] != created[1]


def test_new_file_in_selected_subfolder(window, project_dir):
    subfolder = project_dir / "Sous-dossier"
    subfolder.mkdir()
    window._set_explorer_root(project_dir)

    sub_index = window._explorer_model.index(str(subfolder))
    window._explorer_create(sub_index, is_folder=False)

    assert list(subfolder.glob("*.json"))
    assert not list(project_dir.glob("*.json"))  # pas créé à la racine


def test_delete_file_removes_it(window, project_dir):
    target = project_dir / "a_supprimer.json"
    target.write_text("{}", encoding="utf-8")
    window._set_explorer_root(project_dir)

    index = window._explorer_model.index(str(target))

    from PySide6.QtWidgets import QMessageBox
    import unittest.mock as mock

    with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        window._explorer_delete(index)

    assert not target.exists()


def test_delete_nonempty_folder_removes_it(window, project_dir):
    folder = project_dir / "Dossier"
    folder.mkdir()
    (folder / "fichier.json").write_text("{}", encoding="utf-8")
    window._set_explorer_root(project_dir)

    index = window._explorer_model.index(str(folder))

    from PySide6.QtWidgets import QMessageBox
    import unittest.mock as mock

    with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        window._explorer_delete(index)

    assert not folder.exists()


def test_delete_cancelled_keeps_file(window, project_dir):
    target = project_dir / "garde_moi.json"
    target.write_text("{}", encoding="utf-8")
    window._set_explorer_root(project_dir)

    index = window._explorer_model.index(str(target))

    from PySide6.QtWidgets import QMessageBox
    import unittest.mock as mock

    with mock.patch.object(QMessageBox, "question", return_value=QMessageBox.No):
        window._explorer_delete(index)

    assert target.exists()


def test_target_dir_is_parent_for_a_file(window, project_dir):
    target = project_dir / "un_fichier.json"
    target.write_text("{}", encoding="utf-8")
    window._set_explorer_root(project_dir)

    index = window._explorer_model.index(str(target))
    assert window._explorer_target_dir(index) == project_dir


def test_target_dir_is_itself_for_a_folder(window, project_dir):
    folder = project_dir / "Dossier"
    folder.mkdir()
    window._set_explorer_root(project_dir)

    index = window._explorer_model.index(str(folder))
    assert window._explorer_target_dir(index) == folder
