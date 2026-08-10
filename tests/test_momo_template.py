from __future__ import annotations

from blocks.bar_chart_block import BarChartBlock
from blocks.dependency_gantt_block import DependencyGanttBlock, compute_schedule
from blocks.formula_block import FormulaBlock, compute_formula_result
from blocks.heading_block import HeadingBlock
from blocks.line_chart_block import LineChartBlock, compute_line_series
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.momo_template import build_momo_template


def test_template_has_three_people():
    document = build_momo_template()
    assert len(document.people) == 3
    assert len(set(p["name"] for p in document.people)) == 3


def test_template_block_order_and_types():
    document = build_momo_template()
    types = [type(b) for b in document.blocks]
    assert types == [
        HeadingBlock,  # Méthodo Momo
        HeadingBlock,  # Effectif
        TextBlock,  # liste des personnes
        HeadingBlock,  # Checklist initiale
        LinkedChecklistBlock,
        HeadingBlock,  # Critères
        TableBlock,  # critères
        FormulaBlock,
        HeadingBlock,  # Assignation des tâches
        TableBlock,  # tâches
        DependencyGanttBlock,
        LineChartBlock,
        BarChartBlock,
    ]


def test_template_titles():
    document = build_momo_template()
    h1 = document.blocks[0]
    assert isinstance(h1, HeadingBlock) and h1.level == 1 and h1.content == "Méthodo Momo"
    assert document.blocks[1].content == "Effectif"
    assert document.blocks[3].content == "Checklist initiale"
    assert document.blocks[5].content == "Critères"
    assert document.blocks[8].content == "Assignation des tâches"


def test_effectif_text_lists_the_three_people():
    document = build_momo_template()
    names = [p["name"] for p in document.people]
    text_block = document.blocks[2]
    assert isinstance(text_block, TextBlock)
    for name in names:
        assert name in text_block.content


def test_linked_checklist_has_abc_items_all_todo():
    document = build_momo_template()
    checklist = document.blocks[4]
    assert isinstance(checklist, LinkedChecklistBlock)
    assert [item["text"] for item in checklist.todo_items()] == ["A", "B", "C"]
    assert checklist.done_items() == []


def test_criteria_table_and_formula_are_consistent():
    document = build_momo_template()
    table = document.blocks[6]
    formula = document.blocks[7]
    assert isinstance(table, TableBlock)
    assert isinstance(formula, FormulaBlock)

    result = compute_formula_result(document, formula)
    assert result is not None
    checked_total, total = result
    assert total == 10.0  # 5 + 3 + 2
    assert checked_total == 7.0  # lignes cochées : 5 + 2


def test_tasks_table_and_dependency_gantt_are_consistent():
    document = build_momo_template()
    tasks_table = document.blocks[9]
    gantt = document.blocks[10]
    assert isinstance(tasks_table, TableBlock)
    assert isinstance(gantt, DependencyGanttBlock)

    schedule = compute_schedule(document, gantt)
    assert len(schedule) == 4
    conception = next(t for t in schedule if t["label"] == "Conception")
    tests = next(t for t in schedule if t["label"] == "Tests")
    assert conception["start"] == 0.0
    # Chaîne de dépendances Conception -> Maquettes -> Développement -> Tests
    assert tests["start"] == conception["duration"] + 2 + 5  # 3 + 2 + 5 = 10
    assert tests["person_names"] != []


def test_efficiency_chart_tracks_the_gantt_block():
    document = build_momo_template()
    gantt = document.blocks[10]
    chart = document.blocks[11]
    assert isinstance(chart, LineChartBlock)

    series = compute_line_series(document, chart)
    assert [s["name"] for s in series] == ["Idéal", "Vélocité", "Vélocité réelle"]
    assert series[0]["slope"] == 1.0

    # Sans retard déclaré, la vélocité réelle vaut 1.0 (aucun écart).
    assert series[2]["slope"] == 1.0

    # Un retard sur une sous-tâche fait baisser la vélocité réelle.
    # Le Gantt du template a une colonne "Ecarts" configurée : l'écart se
    # règle désormais via cette colonne du tableau, plus via set_delta.
    table = document.find_block(gantt.table_block_id)
    table.set_cell(table.rows[0]["id"], gantt.delta_column_id, "5")
    series_after_delay = compute_line_series(document, chart)
    assert series_after_delay[2]["slope"] < 1.0


def test_budget_chart_has_two_placeholder_bars():
    document = build_momo_template()
    chart = document.blocks[12]
    assert isinstance(chart, BarChartBlock)
    assert [b["label"] for b in chart.bars] == ["Phase 1", "Phase 2"]
    assert all(b["actual"] is not None for b in chart.bars)


def test_template_document_roundtrips_through_json():
    document = build_momo_template()
    restored = document.__class__.from_dict(document.to_dict())
    assert len(restored.blocks) == len(document.blocks)
    assert [type(b) for b in restored.blocks] == [type(b) for b in document.blocks]
    assert len(restored.people) == 3