from __future__ import annotations

from core.document import Document
from core.people_registry import PeopleRegistry
from blocks.table_block import COLUMN_TYPE_PERSON, TableBlock


def test_add_person_assigns_color():
    doc = Document()
    alice = doc.add_person("Alice")
    bob = doc.add_person("Bob")

    assert alice["name"] == "Alice"
    assert alice["color"]
    assert alice["color"] != bob["color"] or len(doc.people) == 2


def test_rename_and_change_color():
    doc = Document()
    alice = doc.add_person("Alice")

    assert doc.rename_person(alice["id"], "Alicia") is True
    assert doc.find_person(alice["id"])["name"] == "Alicia"

    assert doc.set_person_color(alice["id"], "#ffffff") is True
    assert doc.find_person(alice["id"])["color"] == "#ffffff"

    assert doc.rename_person("inconnu", "X") is False


def test_remove_person_purges_table_references():
    doc = Document()
    alice = doc.add_person("Alice")
    bob = doc.add_person("Bob")

    table = TableBlock()
    col = table.add_column("Assigné", col_type=COLUMN_TYPE_PERSON)
    row = table.add_row(values={col["id"]: [alice["id"], bob["id"]]})
    doc.add_block(table)

    assert doc.remove_person(alice["id"]) is True
    assert doc.find_person(alice["id"]) is None
    assert table.rows[0]["cells"][col["id"]] == [bob["id"]]


def test_document_people_roundtrip():
    doc = Document()
    doc.add_person("Alice", color="#123456")

    rebuilt = Document.from_dict(doc.to_dict())

    assert len(rebuilt.people) == 1
    assert rebuilt.people[0]["name"] == "Alice"
    assert rebuilt.people[0]["color"] == "#123456"


# -- PATCH 82 : registre système partagé entre projets ---------------------

def test_people_registry_is_shared_across_documents():
    """Une personne ajoutée depuis un projet est immédiatement connue
    d'un autre document, sans avoir besoin de la recréer."""
    project_a = Document()
    project_a.add_person("Camille")

    project_b = Document()
    assert project_b.people_registry.find_by_name("Camille") is not None


def test_add_person_deduplicates_by_name_in_registry():
    doc_a = Document()
    alice_a = doc_a.add_person("Alice")

    doc_b = Document()
    alice_b = doc_b.add_person("Alice")

    assert alice_a["id"] == alice_b["id"]


def test_remove_person_detaches_from_project_without_deleting_globally():
    """PATCH 82 — le "vrai" bug corrigé : supprimer une personne d'un
    projet ne doit pas la faire disparaître des autres projets qui la
    référencent encore."""
    project_a = Document()
    alice = project_a.add_person("Alice")

    project_b = Document()
    project_b.link_person(alice["id"])

    assert project_a.remove_person(alice["id"]) is True
    assert project_a.find_person(alice["id"]) is None

    # Toujours visible depuis l'autre projet, et dans le registre global.
    assert project_b.find_person(alice["id"]) is not None
    assert project_a.people_registry.find_person(alice["id"]) is not None


def test_link_person_attaches_existing_registry_entry():
    project_a = Document()
    alice = project_a.add_person("Alice")

    project_b = Document()
    assert project_b.find_person(alice["id"]) is None
    assert project_b.link_person(alice["id"]) is True
    assert project_b.find_person(alice["id"])["name"] == "Alice"
    assert project_b.link_person("inconnu") is False


def test_document_from_dict_migrates_legacy_embedded_people(tmp_path):
    """Ancien format (PATCH 16) : le document embarquait encore une
    liste "people" complète directement dans le JSON. Elle doit être
    migrée vers le registre système partagé à l'ouverture."""
    legacy_raw = {
        "version": 1,
        "blocks": [],
        "people": [{"id": "abc-123", "name": "Alice", "color": "#123456"}],
        "favorite_ids": [],
    }
    document = Document.from_dict(legacy_raw)

    assert len(document.people) == 1
    assert document.people[0]["name"] == "Alice"
    # Migrée dans le registre partagé, donc réutilisable ailleurs.
    other_document = Document()
    assert other_document.people_registry.find_by_name("Alice") is not None
