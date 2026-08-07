from __future__ import annotations

from blocks.table_block import (
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_CHECKLIST,
    COLUMN_TYPE_DURATION,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    TableBlock,
)
from blocks.registry import block_from_dict


def test_default_value_matches_column_type():
    table = TableBlock()
    bool_col = table.add_column("Fait", col_type=COLUMN_TYPE_BOOLEAN)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_DURATION)
    person_col = table.add_column("Assigné", col_type=COLUMN_TYPE_PERSON)
    row = table.add_row()

    assert row["cells"][bool_col["id"]] is False
    assert row["cells"][duration_col["id"]] == {"amount": 0, "unit": "jours"}
    assert row["cells"][person_col["id"]] == []


def test_select_options_reset_invalid_cells():
    table = TableBlock()
    col = table.add_column("Statut", col_type=COLUMN_TYPE_SELECT, options=["A", "B"])
    row = table.add_row(values={col["id"]: "A"})

    table.set_column_options(col["id"], ["B", "C"])
    assert row["cells"][col["id"]] == ""  # "A" n'est plus un choix valide


def test_multi_select_keeps_only_valid_values():
    table = TableBlock()
    col = table.add_column("Tags", col_type=COLUMN_TYPE_MULTI_SELECT, options=["A", "B", "C"])
    row = table.add_row(values={col["id"]: ["A", "B"]})

    table.set_column_options(col["id"], ["B", "C"])
    assert row["cells"][col["id"]] == ["B"]


def test_checklist_cell_normalizes_items():
    table = TableBlock()
    col = table.add_column("Sous-tâches", col_type=COLUMN_TYPE_CHECKLIST)
    row = table.add_row()

    table.set_cell(row["id"], col["id"], [{"text": "Étape 1", "checked": True}])
    items = table.rows[0]["cells"][col["id"]]
    assert len(items) == 1
    assert items[0]["text"] == "Étape 1"
    assert items[0]["checked"] is True
    assert "id" in items[0]


def test_typed_table_roundtrip_via_registry():
    table = TableBlock()
    bool_col = table.add_column("Fait", col_type=COLUMN_TYPE_BOOLEAN)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_DURATION)
    row = table.add_row(values={bool_col["id"]: True, duration_col["id"]: {"amount": 3, "unit": "semaines"}})

    rebuilt = block_from_dict(table.to_dict())

    assert isinstance(rebuilt, TableBlock)
    assert rebuilt.columns[0]["type"] == COLUMN_TYPE_BOOLEAN
    assert rebuilt.rows[0]["cells"][bool_col["id"]] is True
    assert rebuilt.rows[0]["cells"][duration_col["id"]] == {"amount": 3, "unit": "semaines"}


def test_unknown_column_type_falls_back_to_text():
    table = TableBlock(columns=[{"id": "c1", "name": "X", "type": "inconnu"}])
    assert table.columns[0]["type"] == "text"
