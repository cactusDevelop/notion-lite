from __future__ import annotations

from blocks.registry import block_from_dict
from blocks.simple_table_block import SIMPLE_TABLE_BLOCK_TYPE, SimpleTableBlock


def test_default_grid_is_2x2():
    block = SimpleTableBlock()
    assert block.type == SIMPLE_TABLE_BLOCK_TYPE
    assert block.row_count == 2
    assert block.column_count == 2


def test_set_and_get_cell():
    block = SimpleTableBlock()
    assert block.set_cell(0, 0, "Bonjour") is True
    assert block.get_cell(0, 0) == "Bonjour"
    assert block.set_cell(5, 5, "x") is False


def test_add_remove_row():
    block = SimpleTableBlock(row_count=1, column_count=2)
    block.add_row()
    assert block.row_count == 2
    assert block.remove_row(0) is True
    assert block.row_count == 1
    assert block.remove_row(5) is False


def test_add_remove_column_affects_all_rows():
    block = SimpleTableBlock(row_count=2, column_count=1)
    block.add_column()
    assert block.column_count == 2
    assert all(len(row) == 2 for row in block.rows)

    block.remove_column(0)
    assert block.column_count == 1
    assert all(len(row) == 1 for row in block.rows)


def test_rectangularize_pads_short_rows():
    block = SimpleTableBlock(rows=[["a", "b"], ["c"]])
    assert block.rows == [["a", "b"], ["c", ""]]


def test_simple_table_roundtrip_via_registry():
    block = SimpleTableBlock(rows=[["a", "b"], ["c", "d"]])
    rebuilt = block_from_dict(block.to_dict())

    assert isinstance(rebuilt, SimpleTableBlock)
    assert rebuilt.rows == [["a", "b"], ["c", "d"]]
