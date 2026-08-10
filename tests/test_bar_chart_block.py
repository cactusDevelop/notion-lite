from __future__ import annotations

from blocks.bar_chart_block import (
    OVER_BUDGET_COLOR,
    UNDER_BUDGET_COLOR,
    BarChartBlock,
    budget_marker_color,
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