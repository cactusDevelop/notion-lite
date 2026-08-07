from __future__ import annotations

from blocks.table_block import TableBlock
from blocks.registry import block_from_dict


def test_add_column_adds_empty_cell_to_existing_rows():
    table = TableBlock()
    table.add_column(name="A")
    row = table.add_row()
    table.add_column(name="B")

    assert set(row["cells"].keys()) == {table.columns[0]["id"], table.columns[1]["id"]}
    assert row["cells"][table.columns[1]["id"]] == ""


def test_remove_column_removes_cell_from_all_rows():
    table = TableBlock()
    col_a = table.add_column(name="A")
    col_b = table.add_column(name="B")
    row = table.add_row()

    assert table.remove_column(col_a["id"]) is True
    assert col_a["id"] not in row["cells"]
    assert col_b["id"] in row["cells"]
    assert len(table.columns) == 1


def test_add_and_remove_row():
    table = TableBlock()
    table.add_column(name="A")
    row = table.add_row()

    assert len(table.rows) == 1
    assert table.remove_row(row["id"]) is True
    assert len(table.rows) == 0
    assert table.remove_row("inconnu") is False


def test_move_column_and_row():
    table = TableBlock()
    col_a = table.add_column(name="A")
    col_b = table.add_column(name="B")
    row1 = table.add_row()
    row2 = table.add_row()

    table.move_column(col_b["id"], 0)
    assert [c["id"] for c in table.columns] == [col_b["id"], col_a["id"]]

    table.move_row(row2["id"], 0)
    assert [r["id"] for r in table.rows] == [row2["id"], row1["id"]]


def test_set_cell_updates_value():
    table = TableBlock()
    col = table.add_column(name="A")
    row = table.add_row()

    assert table.set_cell(row["id"], col["id"], "hello") is True
    assert row["cells"][col["id"]] == "hello"
    assert table.set_cell("inconnu", col["id"], "x") is False


def test_table_roundtrip_via_registry():
    table = TableBlock()
    col = table.add_column(name="Nom")
    table.add_row(values={col["id"]: "Alice"})

    rebuilt = block_from_dict(table.to_dict())

    assert isinstance(rebuilt, TableBlock)
    assert rebuilt.columns[0]["name"] == "Nom"
    assert rebuilt.rows[0]["cells"][rebuilt.columns[0]["id"]] == "Alice"
