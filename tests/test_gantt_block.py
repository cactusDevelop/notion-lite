from __future__ import annotations

from blocks.gantt_block import GanttBlock, available_date_columns, compute_gantt_rows, find_source_table
from blocks.registry import block_from_dict
from blocks.table_block import COLUMN_TYPE_DATE, COLUMN_TYPE_TEXT, TableBlock
from core.document import Document


def _build_document():
    doc = Document()
    table = TableBlock()
    name_col = table.add_column("Tâche", col_type=COLUMN_TYPE_TEXT)
    date_col = table.add_column("Période", col_type=COLUMN_TYPE_DATE, date_range=True)
    table.add_row(values={
        name_col["id"]: "Conception",
        date_col["id"]: {"start": "2026-01-01", "end": "2026-01-05"},
    })
    table.add_row(values={
        name_col["id"]: "Développement",
        date_col["id"]: {"start": "2026-01-06", "end": "2026-01-20"},
    })
    doc.add_block(table)
    return doc, table, name_col, date_col


def test_gantt_reads_directly_from_table_no_own_data():
    doc, table, name_col, date_col = _build_document()
    gantt = GanttBlock(table_block_id=table.id, label_column_id=name_col["id"], date_column_id=date_col["id"])
    doc.add_block(gantt)

    rows = compute_gantt_rows(doc, gantt)
    assert len(rows) == 2
    assert rows[0]["label"] == "Conception"
    assert rows[0]["start"] == "2026-01-01"
    assert rows[0]["end"] == "2026-01-05"
    # Rien dans les données propres du bloc Gantt hormis les références.
    assert set(gantt.data.keys()) == {"table_block_id", "label_column_id", "date_column_id"}


def test_gantt_updates_automatically_after_table_edit():
    doc, table, name_col, date_col = _build_document()
    gantt = GanttBlock(table_block_id=table.id, label_column_id=name_col["id"], date_column_id=date_col["id"])
    doc.add_block(gantt)

    table.set_cell(table.rows[0]["id"], name_col["id"], "Conception (renommée)")
    table.add_row(values={name_col["id"]: "Tests", date_col["id"]: {"start": "2026-01-21", "end": "2026-01-25"}})

    rows = compute_gantt_rows(doc, gantt)
    assert rows[0]["label"] == "Conception (renommée)"
    assert len(rows) == 3
    assert rows[2]["label"] == "Tests"


def test_gantt_with_single_date_column_uses_same_start_and_end():
    doc = Document()
    table = TableBlock()
    name_col = table.add_column("Tâche", col_type=COLUMN_TYPE_TEXT)
    date_col = table.add_column("Échéance", col_type=COLUMN_TYPE_DATE)
    table.add_row(values={name_col["id"]: "Jalon", date_col["id"]: "2026-02-01"})
    doc.add_block(table)

    gantt = GanttBlock(table_block_id=table.id, label_column_id=name_col["id"], date_column_id=date_col["id"])
    doc.add_block(gantt)

    rows = compute_gantt_rows(doc, gantt)
    assert rows[0]["start"] == rows[0]["end"] == "2026-02-01"


def test_gantt_without_source_returns_empty():
    doc = Document()
    gantt = GanttBlock()
    doc.add_block(gantt)
    assert compute_gantt_rows(doc, gantt) == []


def test_gantt_source_deleted_returns_empty():
    doc, table, name_col, date_col = _build_document()
    gantt = GanttBlock(table_block_id=table.id, label_column_id=name_col["id"], date_column_id=date_col["id"])
    doc.add_block(gantt)

    doc.remove_block(table.id)
    assert find_source_table(doc, gantt) is None
    assert compute_gantt_rows(doc, gantt) == []


def test_available_date_columns_filters_by_type():
    _, table, name_col, date_col = _build_document()
    date_columns = available_date_columns(table)
    assert [c["id"] for c in date_columns] == [date_col["id"]]


def test_gantt_roundtrip_via_registry():
    doc, table, name_col, date_col = _build_document()
    gantt = GanttBlock(table_block_id=table.id, label_column_id=name_col["id"], date_column_id=date_col["id"])

    rebuilt = block_from_dict(gantt.to_dict())
    assert isinstance(rebuilt, GanttBlock)
    assert rebuilt.table_block_id == table.id
    assert rebuilt.label_column_id == name_col["id"]
    assert rebuilt.date_column_id == date_col["id"]
