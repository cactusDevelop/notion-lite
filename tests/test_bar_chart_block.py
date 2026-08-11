from __future__ import annotations

from blocks.bar_chart_block import (
    OVER_BUDGET_COLOR,
    UNDER_BUDGET_COLOR,
    BarChartBlock,
    budget_marker_color,
    sync_bars_from_gantt,
)
from blocks.registry import block_from_dict


def test_add_bar():
    block = BarChartBlock()
    bar = block.add_bar(label="Phase 1", value=1000)
    assert block.bars == [bar]
    assert bar["value"] == 1000.0
    assert bar["actual"] is None


def test_add_bar_with_actual():
    block = BarChartBlock()
    bar = block.add_bar(label="Phase 1", value=1000, actual=1200)
    assert bar["actual"] == 1200.0


def test_remove_bar():
    block = BarChartBlock()
    bar = block.add_bar(label="A", value=1)
    assert block.remove_bar(bar["id"])
    assert block.bars == []
    assert not block.remove_bar("id-inconnu")


def test_set_bar_label_value_and_actual():
    block = BarChartBlock()
    bar = block.add_bar(label="A", value=1)
    assert block.set_bar_label(bar["id"], "Phase 1")
    assert block.set_bar_value(bar["id"], 42)
    assert block.set_bar_actual(bar["id"], 50)
    assert block.bars[0]["label"] == "Phase 1"
    assert block.bars[0]["value"] == 42.0
    assert block.bars[0]["actual"] == 50.0


def test_set_bar_actual_none_clears_marker():
    block = BarChartBlock()
    bar = block.add_bar(label="A", value=10, actual=20)
    assert block.set_bar_actual(bar["id"], None)
    assert block.bars[0]["actual"] is None


def test_budget_marker_color_over_and_under_budget():
    block = BarChartBlock()
    over = block.add_bar(label="Sur budget", value=1000, actual=1200)
    under = block.add_bar(label="Sous budget", value=1000, actual=800)
    no_actual = block.add_bar(label="Sans réel", value=1000)

    assert budget_marker_color(over) == OVER_BUDGET_COLOR
    assert budget_marker_color(under) == UNDER_BUDGET_COLOR
    assert budget_marker_color(no_actual) is None


def test_roundtrip_via_registry():
    block = BarChartBlock(title="Delta de budget", y_axis_label="Prix")
    block.add_bar(label="Phase 1", value=1000, actual=1150)
    block.add_bar(label="Phase 2", value=1200, actual=1100)

    rebuilt = block_from_dict(block.to_dict())
    assert isinstance(rebuilt, BarChartBlock)
    assert rebuilt.title == "Delta de budget"
    assert rebuilt.y_axis_label == "Prix"
    assert [b["label"] for b in rebuilt.bars] == ["Phase 1", "Phase 2"]
    assert [b["value"] for b in rebuilt.bars] == [1000.0, 1200.0]
    assert [b["actual"] for b in rebuilt.bars] == [1150.0, 1100.0]


def test_set_source_and_roundtrip():
    block = BarChartBlock()
    block.set_source("gantt-id", "col-id")
    assert block.source_gantt_id == "gantt-id"
    assert block.group_column_id == "col-id"

    rebuilt = block_from_dict(block.to_dict())
    assert rebuilt.source_gantt_id == "gantt-id"
    assert rebuilt.group_column_id == "col-id"


def test_sync_bars_from_gantt_grouped_by_phase():
    from core.document import Document
    from blocks.dependency_gantt_block import DependencyGanttBlock
    from blocks.table_block import COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_NUMBER, COLUMN_TYPE_TEXT, TableBlock

    document = Document()
    table = TableBlock()
    phase_col = table.add_column("Phase", col_type=COLUMN_TYPE_TEXT)
    label_col = table.add_column("Tâche", col_type=COLUMN_TYPE_TEXT)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_NUMBER)
    dep_col = table.add_column("Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT)
    delta_col = table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)
    table.add_row(values={phase_col["id"]: "P1", label_col["id"]: "A", duration_col["id"]: "3", delta_col["id"]: "0"})
    table.add_row(values={phase_col["id"]: "P1", label_col["id"]: "B", duration_col["id"]: "2", delta_col["id"]: "1"})
    table.add_row(values={phase_col["id"]: "P2", label_col["id"]: "C", duration_col["id"]: "4", delta_col["id"]: "0"})
    document.add_block(table)

    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        duration_column_id=duration_col["id"],
        dependency_column_id=dep_col["id"],
        delta_column_id=delta_col["id"],
    )
    document.add_block(gantt)

    chart = BarChartBlock()
    chart.set_source(gantt.id, phase_col["id"])
    document.add_block(chart)

    bars = sync_bars_from_gantt(document, chart)
    assert [b["label"] for b in bars] == ["P1", "P2"]
    p1 = bars[0]
    assert p1["value"] == 5.0  # 3 + 2
    assert p1["actual"] == 6.0  # 3 + (2+1)
    p2 = bars[1]
    assert p2["value"] == p2["actual"] == 4.0


def test_sync_bars_from_gantt_without_source_returns_empty():
    block = BarChartBlock()
    from core.document import Document

    assert sync_bars_from_gantt(Document(), block) == []