from __future__ import annotations

import os
import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.people_list_block import PeopleListBlock  # noqa: E402
from blocks.table_block import COLUMN_TYPE_PERSON, TableBlock  # noqa: E402
from core.document import Document  # noqa: E402
from ui.blocks.people_list_block_widget import PeopleListBlockWidget  # noqa: E402
from ui.blocks.table_cell_dialogs import edit_person_list  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_remove_chip_button_actually_removes_person(qapp):
    """PATCH 83 — Régression : la croix des étiquettes du bloc Effectif
    ne faisait rien, car le signal `clicked(bool)` de Qt écrasait
    l'identifiant par défaut de la personne dans la lambda connectée."""
    document = Document()
    alice = document.add_person("Alice")
    document.add_person("Bob")
    widget = PeopleListBlockWidget(PeopleListBlock(), document)

    assert widget._chips_row.count() == 3  # Alice, Bob, stretch
    first_chip = widget._chips_row.itemAt(0).widget()
    remove_button = first_chip.findChildren(QtWidgets.QToolButton)[0]

    remove_button.click()
    qapp.processEvents()

    assert document.find_person(alice["id"]) is None
    assert [p["name"] for p in document.people] == ["Bob"]
    assert widget._chips_row.count() == 2  # Bob, stretch


def test_people_list_widget_refreshes_when_person_added_elsewhere(qapp):
    """PATCH 83 — Ajouter une personne depuis la popup "Personne" d'un
    tableau doit apparaître aussitôt dans le bloc Effectif, sans
    attendre un re-rendu complet du document."""
    document = Document()
    widget = PeopleListBlockWidget(PeopleListBlock(), document)
    assert widget._chips_row.count() == 1  # juste le stretch

    # Simule ce que fait la popup "Personne" d'une cellule de tableau :
    # elle appelle Document.add_person directement.
    document.add_person("Camille")
    qapp.processEvents()

    names = [
        chip.findChildren(QtWidgets.QLabel)[0].text()
        for i in range(widget._chips_row.count() - 1)
        for chip in [widget._chips_row.itemAt(i).widget()]
    ]
    assert names == ["Camille"]


def test_people_list_widget_refreshes_when_person_removed_via_table_dialog(qapp, monkeypatch):
    """La popup "Personne" d'un tableau peut aussi retirer une personne
    du projet (Gestionnaire, PATCH 82) ; le bloc Effectif doit suivre."""
    document = Document()
    alice = document.add_person("Alice")
    widget = PeopleListBlockWidget(PeopleListBlock(), document)
    assert widget._chips_row.count() == 2

    document.remove_person(alice["id"])
    qapp.processEvents()

    assert widget._chips_row.count() == 1


def test_people_list_widget_unsubscribes_on_destruction(qapp):
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtTest import QTest

    document = Document()
    widget = PeopleListBlockWidget(PeopleListBlock(), document)
    listener_count_before = len(document._people_listeners)
    assert listener_count_before == 1

    widget.deleteLater()
    QCoreApplication.sendPostedEvents()
    QTest.qWait(10)

    assert len(document._people_listeners) == 0
    # Ne doit pas planter même si le widget n'existe plus.
    document.add_person("Dana")
