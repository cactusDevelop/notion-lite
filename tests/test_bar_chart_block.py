from __future__ import annotations

from blocks.bar_chart_block import (
    OVER_BUDGET_COLOR,
    UNDER_BUDGET_COLOR,
    BarChartBlock,
    budget_marker_color,
    sync_bars_from_gantt,
)
from blocks.registry import block_from_dict


def test_budget_marker_color_over_and_under_budget():
    over = {"label": "Sur budget", "value": 1000, "actual": 1200}
    under = {"label": "Sous budget", "value": 1000, "actual": 800}
    no_actual = {"label": "Sans réel", "value": 1000, "actual": None}

    assert budget_marker_color(over) == OVER_BUDGET_COLOR
    assert budget_marker_color(under) == UNDER_BUDGET_COLOR
    assert budget_marker_color(no_actual) is None


def test_roundtrip_via_registry():
    block = BarChartBlock(title="Delta de budget", y_axis_label="Prix")
    block.set_source("gantt-id", "phase-col", "price-est-col", "price-real-col")

    rebuilt = block_from_dict(block.to_dict())
    assert isinstance(rebuilt, BarChartBlock)
    assert rebuilt.title == "Delta de budget"
    assert rebuilt.y_axis_label == "Prix"
    assert rebuilt.source_gantt_id == "gantt-id"
    assert rebuilt.group_column_id == "phase-col"
    assert rebuilt.value_column_id == "price-est-col"
    assert rebuilt.actual_column_id == "price-real-col"


def test_set_source_and_roundtrip():
    block = BarChartBlock()
    block.set_source("gantt-id", "col-id")
    assert block.source_gantt_id == "gantt-id"
    assert block.group_column_id == "col-id"
    assert block.value_column_id is None
    assert block.actual_column_id is None

    rebuilt = block_from_dict(block.to_dict())
    assert rebuilt.source_gantt_id == "gantt-id"
    assert rebuilt.group_column_id == "col-id"


def test_sync_bars_from_gantt_grouped_by_phase():
    """Sans colonnes de prix configurées : repli sur l'ancien calcul
    durée + écart des sous-tâches du planning."""
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


def test_sync_bars_from_gantt_price_columns():
    """PATCH 59 — avec value_column_id/actual_column_id configurés, le
    calcul se base sur ces colonnes "Prix" plutôt que sur durée + écart."""
    from core.document import Document
    from blocks.dependency_gantt_block import DependencyGanttBlock
    from blocks.table_block import COLUMN_TYPE_MULTI_SELECT, COLUMN_TYPE_NUMBER, COLUMN_TYPE_TEXT, TableBlock

    document = Document()
    table = TableBlock()
    phase_col = table.add_column("Phase", col_type=COLUMN_TYPE_TEXT)
    label_col = table.add_column("Tâche", col_type=COLUMN_TYPE_TEXT)
    duration_col = table.add_column("Durée", col_type=COLUMN_TYPE_NUMBER)
    dep_col = table.add_column("Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT)
    price_est_col = table.add_column("Prix estimé", col_type=COLUMN_TYPE_NUMBER)
    price_real_col = table.add_column("Prix réel", col_type=COLUMN_TYPE_NUMBER)
    table.add_row(
        values={
            phase_col["id"]: "P1",
            label_col["id"]: "A",
            duration_col["id"]: "3",
            price_est_col["id"]: "900",
            price_real_col["id"]: "900",
        }
    )
    table.add_row(
        values={
            phase_col["id"]: "P1",
            label_col["id"]: "B",
            duration_col["id"]: "2",
            price_est_col["id"]: "600",
            price_real_col["id"]: "650",
        }
    )
    table.add_row(
        values={
            phase_col["id"]: "P2",
            label_col["id"]: "C",
            duration_col["id"]: "4",
            price_est_col["id"]: "1000",
            price_real_col["id"]: "900",
        }
    )
    document.add_block(table)

    gantt = DependencyGanttBlock(
        table_block_id=table.id,
        label_column_id=label_col["id"],
        duration_column_id=duration_col["id"],
        dependency_column_id=dep_col["id"],
    )
    document.add_block(gantt)

    chart = BarChartBlock()
    chart.set_source(gantt.id, phase_col["id"], price_est_col["id"], price_real_col["id"])
    document.add_block(chart)

    bars = sync_bars_from_gantt(document, chart)
    assert [b["label"] for b in bars] == ["P1", "P2"]
    p1 = next(b for b in bars if b["label"] == "P1")
    assert p1["value"] == 1500.0  # 900 + 600
    assert p1["actual"] == 1550.0  # 900 + 650 (dépassement)
    p2 = next(b for b in bars if b["label"] == "P2")
    assert p2["value"] == 1000.0
    assert p2["actual"] == 900.0  # sous budget


def test_sync_bars_from_gantt_without_source_returns_empty():
    block = BarChartBlock()
    from core.document import Document

    assert sync_bars_from_gantt(Document(), block) == []
