from __future__ import annotations

from blocks.dependency_gantt_block import (
    FORMAT_MACRO,
    FORMAT_MICRO,
    UNIT_DAYS,
    UNIT_MONTHS,
    DependencyGanttBlock,
    available_delta_columns,
    compute_schedule,
    find_source_table,
    format_duration_in_unit,
)
from blocks.registry import block_from_dict
from blocks.table_block import (
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_TEXT,
    TableBlock,
)
from core.document import Document


def _build_document():
    doc = Document()
    alice = doc.add_person("Alice")
    bob = doc.add_person("Bob")

    table = TableBlock()
    label_col = table.add_column("Sous-tâches", col_type=COLUMN_TYPE_TEXT)
    person_col = table.add_column("Prsn. assignées", col_type=COLUMN_TYPE_PERSON)
    duration_col = table.add_column("Temps estimé (jours)", col_type=COLUMN_TYPE_NUMBER)
    risk_col = table.add_column("Risques", col_type=COLUMN_TYPE_SELECT, options=["vert", "orange", "rouge"])
    dep_col = table.add_column(
        "Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT, options=["Conception", "Développement"]
    )

    table.add_row(values={
        label_col["id"]: "Conception",
        person_col["id"]: [alice["id"]],
        duration_col["id"]: "3",
        risk_col["id"]: "vert",
        dep_col["id"]: [],
    })
    table.add_row(values={
        label_col["id"]: "Développement",
        person_col["id"]: [bob["id"]],
        duration_col["id"]: "5",
        risk_col["id"]: "orange",
        dep_col["id"]: ["Conception"],
    })
    doc.add_block(table)
    return doc, table, label_col, person_col, duration_col, risk_col, dep_col


def _make_block(table, label_col, person_col, duration_col, risk_col, dep_col):
    return DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        person_column_id=person_col["id"],
        duration_column_id=duration_col["id"],
        risk_column_id=risk_col["id"],
        dependency_column_id=dep_col["id"],
    )


def test_independent_task_starts_at_zero():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    doc.add_block(gantt)

    schedule = compute_schedule(doc, gantt)
    conception = next(r for r in schedule if r["label"] == "Conception")
    assert conception["start"] == 0.0
    assert conception["end"] == 3.0
    assert conception["resolution"] == 3.0
    assert conception["color"] == "#4caf50"
    assert conception["person_names"] == ["Alice"]


def test_dependent_task_starts_at_dependency_resolution_on_time():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    doc.add_block(gantt)

    schedule = compute_schedule(doc, gantt)
    dev = next(r for r in schedule if r["label"] == "Développement")
    assert dev["start"] == 3.0
    assert dev["end"] == 8.0
    assert dev["resolution"] == 8.0


def test_delay_extends_resolution_and_shifts_dependent_start():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    doc.add_block(gantt)

    conception_row = next(r for r in table.rows if row_label(table, r, label_col) == "Conception")
    gantt.set_delta(conception_row["id"], 2)  # 2 jours de retard

    schedule = compute_schedule(doc, gantt)
    conception = next(r for r in schedule if r["label"] == "Conception")
    dev = next(r for r in schedule if r["label"] == "Développement")

    assert conception["resolution"] == 5.0  # fin planifiée (3) + retard (2)
    assert dev["start"] == 5.0
    assert dev["end"] == 10.0


def test_advance_pulls_resolution_earlier_and_dependent_starts_earlier():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    doc.add_block(gantt)

    conception_row = next(r for r in table.rows if row_label(table, r, label_col) == "Conception")
    gantt.set_delta(conception_row["id"], -1)  # 1 jour d'avance

    schedule = compute_schedule(doc, gantt)
    conception = next(r for r in schedule if r["label"] == "Conception")
    dev = next(r for r in schedule if r["label"] == "Développement")

    assert conception["resolution"] == 2.0  # fin planifiée (3) - avance (1)
    assert dev["start"] == 2.0
    assert dev["end"] == 7.0


def test_circular_dependency_does_not_infinite_loop():
    doc = Document()
    table = TableBlock()
    label_col = table.add_column("Sous-tâches", col_type=COLUMN_TYPE_TEXT)
    duration_col = table.add_column("Temps estimé (jours)", col_type=COLUMN_TYPE_NUMBER)
    dep_col = table.add_column("Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT, options=["A", "B"])
    table.add_row(values={label_col["id"]: "A", duration_col["id"]: "2", dep_col["id"]: ["B"]})
    table.add_row(values={label_col["id"]: "B", duration_col["id"]: "2", dep_col["id"]: ["A"]})
    doc.add_block(table)

    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        duration_column_id=duration_col["id"],
        dependency_column_id=dep_col["id"],
    )
    doc.add_block(gantt)

    schedule = compute_schedule(doc, gantt)  # ne doit pas lever de RecursionError
    assert len(schedule) == 2


def test_without_source_returns_empty():
    doc = Document()
    gantt = DependencyGanttBlock()
    doc.add_block(gantt)
    assert compute_schedule(doc, gantt) == []


def test_source_deleted_returns_empty():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    doc.add_block(gantt)

    doc.remove_block(table.id)
    assert find_source_table(doc, gantt) is None
    assert compute_schedule(doc, gantt) == []


def test_delta_of_zero_is_not_stored():
    block = DependencyGanttBlock()
    block.set_delta("row-1", 3)
    assert block.deltas == {"row-1": 3.0}
    block.set_delta("row-1", 0)
    assert block.deltas == {}


def test_roundtrip_via_registry_preserves_deltas():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    gantt.set_delta("some-row", 4)

    rebuilt = block_from_dict(gantt.to_dict())
    assert isinstance(rebuilt, DependencyGanttBlock)
    assert rebuilt.table_block_id == table.id
    assert rebuilt.deltas == {"some-row": 4.0}


def test_roundtrip_via_registry_preserves_phase_column_id():
    """PATCH 89 — Régression : `block_from_dict` ne relisait jamais
    `phase_column_id` (oubli dans blocks/registry.py), donc la colonne
    "Phases" choisie à la création (ex. par le template "Modèle OG")
    disparaissait dès la première réouverture du fichier."""
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    phase_col = table.add_column("Phases", col_type=COLUMN_TYPE_TEXT)
    gantt = _make_block(table, label_col, person_col, duration_col, risk_col, dep_col)
    gantt.data["phase_column_id"] = phase_col["id"]

    rebuilt = block_from_dict(gantt.to_dict())
    assert isinstance(rebuilt, DependencyGanttBlock)
    assert rebuilt.phase_column_id == phase_col["id"]


def row_label(table, row, label_col):
    return row["cells"].get(label_col["id"])


def test_delta_from_column_takes_priority_over_legacy_deltas():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    delta_col = table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)
    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        person_column_id=person_col["id"],
        duration_column_id=duration_col["id"],
        risk_column_id=risk_col["id"],
        dependency_column_id=dep_col["id"],
        delta_column_id=delta_col["id"],
    )
    doc.add_block(gantt)

    conception_row = next(r for r in table.rows if row_label(table, r, label_col) == "Conception")
    # Un ancien "delta" côté bloc est ignoré dès qu'une colonne "Ecarts" est configurée.
    gantt.set_delta(conception_row["id"], 99)
    table.set_cell(conception_row["id"], delta_col["id"], "2")

    schedule = compute_schedule(doc, gantt)
    conception = next(r for r in schedule if r["label"] == "Conception")
    assert conception["delta"] == 2.0
    assert conception["resolution"] == 5.0


def test_delta_column_updates_cascade_like_legacy_delta():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    delta_col = table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)
    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        person_column_id=person_col["id"],
        duration_column_id=duration_col["id"],
        risk_column_id=risk_col["id"],
        dependency_column_id=dep_col["id"],
        delta_column_id=delta_col["id"],
    )
    doc.add_block(gantt)

    conception_row = next(r for r in table.rows if row_label(table, r, label_col) == "Conception")
    table.set_cell(conception_row["id"], delta_col["id"], "-1")

    schedule = compute_schedule(doc, gantt)
    dev = next(r for r in schedule if r["label"] == "Développement")
    assert dev["start"] == 2.0


def test_chart_format_defaults_to_micro_and_is_settable():
    block = DependencyGanttBlock()
    assert block.chart_format == FORMAT_MICRO
    block.chart_format = FORMAT_MACRO
    assert block.chart_format == FORMAT_MACRO
    # Valeur invalide : repli silencieux sur "micro".
    block.chart_format = "meso"
    assert block.chart_format == FORMAT_MICRO


def test_format_duration_in_unit():
    assert format_duration_in_unit(30, UNIT_DAYS) == "30 j"
    assert format_duration_in_unit(30, UNIT_MONTHS) == "1 mois"
    assert format_duration_in_unit(45, UNIT_MONTHS) == "1.5 mois"


def test_roundtrip_via_registry_preserves_delta_column_and_chart_format():
    doc, table, label_col, person_col, duration_col, risk_col, dep_col = _build_document()
    delta_col = table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)
    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        duration_column_id=duration_col["id"],
        delta_column_id=delta_col["id"],
        chart_format=FORMAT_MACRO,
    )

    rebuilt = block_from_dict(gantt.to_dict())
    assert isinstance(rebuilt, DependencyGanttBlock)
    assert rebuilt.delta_column_id == delta_col["id"]
    assert rebuilt.chart_format == FORMAT_MACRO


def test_available_delta_columns_are_number_columns():
    _, table, _, _, duration_col, _, _ = _build_document()
    delta_col = table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)
    columns = available_delta_columns(table)
    assert {c["id"] for c in columns} == {duration_col["id"], delta_col["id"]}