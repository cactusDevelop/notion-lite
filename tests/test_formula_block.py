from __future__ import annotations

from blocks.formula_block import (
    FormulaBlock,
    available_boolean_columns,
    available_number_columns,
    compute_formula_result,
    find_source_table,
    format_formula_text,
)
from blocks.registry import block_from_dict
from blocks.table_block import COLUMN_TYPE_BOOLEAN, COLUMN_TYPE_NUMBER, COLUMN_TYPE_TEXT, TableBlock
from core.document import Document


def _build_document():
    doc = Document()
    table = TableBlock()
    name_col = table.add_column("Catégorie", col_type=COLUMN_TYPE_TEXT)
    state_col = table.add_column("État", col_type=COLUMN_TYPE_BOOLEAN)
    points_col = table.add_column("Points", col_type=COLUMN_TYPE_NUMBER)
    table.add_row(values={name_col["id"]: "A", state_col["id"]: True, points_col["id"]: "5"})
    table.add_row(values={name_col["id"]: "B", state_col["id"]: False, points_col["id"]: "3"})
    table.add_row(values={name_col["id"]: "C", state_col["id"]: True, points_col["id"]: "2"})
    doc.add_block(table)
    return doc, table, state_col, points_col


def test_formula_sums_checked_rows_over_total():
    doc, table, state_col, points_col = _build_document()
    formula = FormulaBlock(table_block_id=table.id, number_column_id=points_col["id"], boolean_column_id=state_col["id"])
    doc.add_block(formula)

    result = compute_formula_result(doc, formula)
    assert result == (7.0, 10.0)
    assert format_formula_text(formula, result) == "Résultat: 7 / 10"


def test_formula_updates_automatically_after_table_edit():
    doc, table, state_col, points_col = _build_document()
    formula = FormulaBlock(table_block_id=table.id, number_column_id=points_col["id"], boolean_column_id=state_col["id"])
    doc.add_block(formula)

    table.set_cell(table.rows[1]["id"], state_col["id"], True)
    result = compute_formula_result(doc, formula)
    assert result == (10.0, 10.0)


def test_formula_custom_label():
    doc, table, state_col, points_col = _build_document()
    formula = FormulaBlock(
        table_block_id=table.id,
        number_column_id=points_col["id"],
        boolean_column_id=state_col["id"],
        label="Score : ",
    )
    result = compute_formula_result(doc, formula)
    assert format_formula_text(formula, result) == "Score : 7 / 10"


def test_formula_without_source_returns_none():
    doc = Document()
    formula = FormulaBlock()
    doc.add_block(formula)
    assert compute_formula_result(doc, formula) is None
    assert format_formula_text(formula, None) == "Résultat: (source non configurée)"


def test_formula_source_deleted_returns_none():
    doc, table, state_col, points_col = _build_document()
    formula = FormulaBlock(table_block_id=table.id, number_column_id=points_col["id"], boolean_column_id=state_col["id"])
    doc.add_block(formula)

    doc.remove_block(table.id)
    assert find_source_table(doc, formula) is None
    assert compute_formula_result(doc, formula) is None


def test_available_columns_filter_by_type():
    _, table, state_col, points_col = _build_document()
    assert [c["id"] for c in available_number_columns(table)] == [points_col["id"]]
    assert [c["id"] for c in available_boolean_columns(table)] == [state_col["id"]]


def test_formula_roundtrip_via_registry():
    doc, table, state_col, points_col = _build_document()
    formula = FormulaBlock(
        table_block_id=table.id,
        number_column_id=points_col["id"],
        boolean_column_id=state_col["id"],
        label="Score : ",
    )

    rebuilt = block_from_dict(formula.to_dict())
    assert isinstance(rebuilt, FormulaBlock)
    assert rebuilt.table_block_id == table.id
    assert rebuilt.number_column_id == points_col["id"]
    assert rebuilt.boolean_column_id == state_col["id"]
    assert rebuilt.label == "Score : "
