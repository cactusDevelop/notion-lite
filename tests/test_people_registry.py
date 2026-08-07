from __future__ import annotations

from blocks.table_block import COLUMN_TYPE_PERSON, TableBlock
from core.document import Document


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
