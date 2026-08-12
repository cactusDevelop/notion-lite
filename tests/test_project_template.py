from __future__ import annotations

from blocks.bar_chart_block import BarChartBlock
from blocks.dependency_gantt_block import DependencyGanttBlock, compute_schedule
from blocks.formula_block import FormulaBlock, compute_formula_result
from blocks.heading_block import HeadingBlock
from blocks.line_chart_block import LineChartBlock, compute_line_series
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.people_list_block import PeopleListBlock
from blocks.table_block import TableBlock
from core.momo_template import build_project_template


def test_template_has_three_people():
    document = build_project_template()
    assert len(document.people) == 3
    assert len(set(p["name"] for p in document.people)) == 3


def test_template_block_order_and_types():
    document = build_project_template()
    types = [type(b) for b in document.blocks]
    assert types == [
        HeadingBlock,  # Modèle OG
        HeadingBlock,  # Effectif
        PeopleListBlock,  # liste des personnes (éditable, PATCH 52)
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
    document = build_project_template()
    h1 = document.blocks[0]
    assert isinstance(h1, HeadingBlock) and h1.level == 1 and h1.content == "Modèle OG"
    assert document.blocks[1].content == "Effectif"
    assert document.blocks[3].content == "Checklist initiale"
    assert document.blocks[5].content == "Critères"
    assert document.blocks[8].content == "Assignation des tâches"


def test_effectif_block_is_editable_people_list():
    document = build_project_template()
    people_block = document.blocks[2]
    assert isinstance(people_block, PeopleListBlock)
    # PATCH 52 — l'effectif n'a pas de contenu propre : il reflète
    # directement le registre partagé Document.people (source unique).
    names = [p["name"] for p in document.people]
    assert len(names) == 3


def test_linked_checklist_has_abc_items_all_todo():
    document = build_project_template()
    checklist = document.blocks[4]
    assert isinstance(checklist, LinkedChecklistBlock)
    assert [item["text"] for item in checklist.todo_items()] == ["A", "B", "C"]
    assert checklist.done_items() == []


def test_criteria_table_and_formula_are_consistent():
    document = build_project_template()
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
    document = build_project_template()
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
    document = build_project_template()
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


def test_budget_chart_is_synced_with_the_prices():
    """PATCH 59 — le graphique 'Delta de budget' est relié au planning et
    regroupé par 'Phases', et calculé à partir des colonnes "Prix
    estimé"/"Prix réel" du tableau (plutôt que durée + écart)."""
    document = build_project_template()
    tasks_table = document.blocks[9]
    gantt = document.blocks[10]
    chart = document.blocks[12]
    assert isinstance(chart, BarChartBlock)
    assert chart.source_gantt_id == gantt.id
    assert chart.value_column_id is not None
    assert chart.actual_column_id is not None
    assert chart.y_axis_label == "Prix"

    from blocks.bar_chart_block import sync_bars_from_gantt

    bars = sync_bars_from_gantt(document, chart)
    assert [b["label"] for b in bars] == ["Phase 1", "Phase 2"]
    phase1 = next(b for b in bars if b["label"] == "Phase 1")
    phase2 = next(b for b in bars if b["label"] == "Phase 2")
    assert phase1["value"] == 1500.0  # 900 (Conception) + 600 (Maquettes)
    assert phase1["actual"] == 1550.0  # 900 + 650 : léger dépassement
    assert phase2["value"] == 2250.0  # 1500 (Développement) + 750 (Tests)
    assert phase2["actual"] == 2200.0  # 1500 + 700 : sous le budget

    # Une modification du prix réel dans le tableau se répercute aussitôt.
    price_actual_col = next(c for c in tasks_table.columns if c["name"] == "Prix réel")
    tasks_table.set_cell(tasks_table.rows[0]["id"], price_actual_col["id"], "1000")
    bars_after = sync_bars_from_gantt(document, chart)
    phase1_after = next(b for b in bars_after if b["label"] == "Phase 1")
    assert phase1_after["actual"] == 1650.0  # 1000 + 650


def test_template_document_roundtrips_through_json():
    document = build_project_template()
    restored = document.__class__.from_dict(document.to_dict())
    assert len(restored.blocks) == len(document.blocks)
    assert [type(b) for b in restored.blocks] == [type(b) for b in document.blocks]
    assert len(restored.people) == 3