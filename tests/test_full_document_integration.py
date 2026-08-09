"""
PATCH 42 — Test d'intégration bout-en-bout : un document contenant un
bloc de chaque type, sauvegardé puis rechargé (même sérialisation que
Fichier > Sauvegarder/Ouvrir), et quelques opérations transverses
(recherche, remplacement, undo/redo, favoris) menées dessus.

Ce test sert de garde-fou de non-régression global avant la
publication de la version 1.0 : il ne teste pas un mécanisme en
isolation (déjà largement couvert ailleurs) mais que tous les types
de blocs cohabitent correctement dans un même document, à travers un
cycle complet sauvegarde -> chargement.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.checklist_block import ChecklistBlock  # noqa: E402
from blocks.code_block import CodeBlock  # noqa: E402
from blocks.gantt_block import GanttBlock  # noqa: E402
from blocks.heading_block import HeadingBlock  # noqa: E402
from blocks.image_block import ImageBlock  # noqa: E402
from blocks.list_block import ListBlock  # noqa: E402
from blocks.quote_block import QuoteBlock  # noqa: E402
from blocks.separator_block import SeparatorBlock  # noqa: E402
from blocks.simple_table_block import SimpleTableBlock  # noqa: E402
from blocks.table_block import TableBlock  # noqa: E402
from blocks.text_block import TextBlock  # noqa: E402
from core.document import Document  # noqa: E402
from core.replace import replace_all  # noqa: E402
from core.search import search_document  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


def _build_one_of_every_block_type(document: Document) -> dict[str, str]:
    """Peuple `document` avec un bloc de chaque type et retourne
    {type: id} pour pouvoir les retrouver ensuite."""
    ids: dict[str, str] = {}

    def add(block):
        document.add_block(block)
        ids[block.type] = block.id
        return block

    add(HeadingBlock(level=1, content="Rapport findable"))
    add(TextBlock(content="Paragraphe findable"))

    checklist = ChecklistBlock()
    checklist.add_item("Tâche findable")
    add(checklist)

    lst = ListBlock()
    lst.add_item("Élément findable")
    add(lst)

    add(QuoteBlock(content="Citation findable"))
    add(CodeBlock(content="print('findable')", language="python"))
    add(SeparatorBlock())
    add(ImageBlock())

    table = TableBlock()
    column = table.add_column(name="Nom", col_type="text")
    row = table.add_row()
    table.set_cell(row["id"], column["id"], "Cellule findable")
    add(table)

    add(SimpleTableBlock(rows=[["A", "findable"], ["C", "D"]]))
    add(GanttBlock())

    return ids


def test_one_of_every_block_type_survives_save_and_reload(tmp_path):
    document = Document()
    ids = _build_one_of_every_block_type(document)
    document.toggle_favorite(ids["text"])

    file_path = tmp_path / "roundtrip.json"
    file_path.write_text(
        json.dumps(document.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    reloaded = Document.from_dict(json.loads(file_path.read_text(encoding="utf-8")))

    assert len(reloaded) == len(document)
    assert {b.type for b in reloaded.blocks} == {b.type for b in document.blocks}
    assert reloaded.favorite_ids == document.favorite_ids
    # Chaque bloc garde le même id après un aller-retour disque.
    assert {b.id for b in reloaded.blocks} == {b.id for b in document.blocks}


def test_search_finds_a_match_in_every_textual_block_type(qapp):
    document = Document()
    _build_one_of_every_block_type(document)

    results = search_document(document, "findable")

    matched_types = {r.block_type for r in results}
    # Un séparateur, une image et un Gantt vide n'ont rien de textuel :
    # tout le reste doit avoir été trouvé.
    expected = {"heading1", "text", "checklist", "list", "quote", "code", "table", "simple_table"}
    assert expected <= matched_types


def test_replace_all_updates_matches_across_block_types(qapp):
    document = Document()
    _build_one_of_every_block_type(document)

    count = replace_all(document, "findable", "trouvé")

    assert count >= len(
        {"heading1", "text", "checklist", "list", "quote", "code", "table", "simple_table"}
    )
    # Plus aucune occurrence de la chaîne d'origine.
    assert search_document(document, "findable") == []


def test_full_window_smoke_test_with_undo_redo(qapp):
    """Ajoute un bloc de chaque type via les vraies méthodes de
    MainWindow, puis vérifie que undo/redo restent cohérents."""
    window = MainWindow()
    baseline = len(window._document)

    window._add_text_block("Un paragraphe")
    window._add_checklist_block()
    window._add_list_block()
    window._add_code_block()
    window._add_quote_block()
    window._add_separator_block()
    window._add_table_block()
    window._add_simple_table_block()
    window._add_gantt_block()

    added = len(window._document) - baseline
    assert added == 9

    # Ctrl+Z doit défaire tout le lot en un point (aucun sondage
    # intermédiaire n'a eu lieu), Ctrl+Y doit le rétablir.
    window._undo()
    assert len(window._document) == baseline

    window._redo()
    assert len(window._document) == baseline + added
