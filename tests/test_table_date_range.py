from __future__ import annotations

from blocks.table_block import COLUMN_TYPE_DATE, TableBlock
from blocks.registry import block_from_dict


def test_date_column_default_is_single_string():
    table = TableBlock()
    col = table.add_column("Échéance", col_type=COLUMN_TYPE_DATE)
    row = table.add_row()
    assert row["cells"][col["id"]] == ""


def test_date_range_column_default_is_start_end_dict():
    table = TableBlock()
    col = table.add_column("Période", col_type=COLUMN_TYPE_DATE, date_range=True)
    row = table.add_row()
    assert row["cells"][col["id"]] == {"start": "", "end": ""}


def test_set_cell_date_range_normalizes_partial_dict():
    table = TableBlock()
    col = table.add_column("Période", col_type=COLUMN_TYPE_DATE, date_range=True)
    row = table.add_row()

    table.set_cell(row["id"], col["id"], {"start": "2026-01-01"})
    assert table.rows[0]["cells"][col["id"]] == {"start": "2026-01-01", "end": ""}


def test_toggle_date_range_resets_cells():
    table = TableBlock()
    col = table.add_column("Échéance", col_type=COLUMN_TYPE_DATE)
    row = table.add_row(values={col["id"]: "2026-05-01"})

    assert table.set_column_date_range(col["id"], True) is True
    assert table.rows[0]["cells"][col["id"]] == {"start": "", "end": ""}

    assert table.set_column_date_range(col["id"], False) is True
    assert table.rows[0]["cells"][col["id"]] == ""


def test_date_range_roundtrip_via_registry():
    table = TableBlock()
    col = table.add_column("Période", col_type=COLUMN_TYPE_DATE, date_range=True)
    table.add_row(values={col["id"]: {"start": "2026-01-01", "end": "2026-01-15"}})

    rebuilt = block_from_dict(table.to_dict())

    assert rebuilt.columns[0]["range"] is True
    assert rebuilt.rows[0]["cells"][rebuilt.columns[0]["id"]] == {
        "start": "2026-01-01",
        "end": "2026-01-15",
    }
