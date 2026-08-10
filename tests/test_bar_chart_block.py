from __future__ import annotations

from blocks.bar_chart_block import BarChartBlock
from blocks.registry import block_from_dict


def test_add_bar():
    block = BarChartBlock()
    bar = block.add_bar(label="Prévu", value=1000)
    assert block.bars == [bar]
    assert bar["value"] == 1000.0


def test_remove_bar():
    block = BarChartBlock()
    bar = block.add_bar(label="A", value=1)
    assert block.remove_bar(bar["id"])
    assert block.bars == []
    assert not block.remove_bar("id-inconnu")


def test_set_bar_label_and_value():
    block = BarChartBlock()
    bar = block.add_bar(label="A", value=1)
    assert block.set_bar_label(bar["id"], "Réel")
    assert block.set_bar_value(bar["id"], 42)
    assert block.bars[0]["label"] == "Réel"
    assert block.bars[0]["value"] == 42.0


def test_roundtrip_via_registry():
    block = BarChartBlock(title="Delta de budget", y_axis_label="Prix")
    block.add_bar(label="Prévu", value=1000, color="#7986cb")
    block.add_bar(label="Réel", value=1200, color="#e57373")

    rebuilt = block_from_dict(block.to_dict())
    assert isinstance(rebuilt, BarChartBlock)
    assert rebuilt.title == "Delta de budget"
    assert rebuilt.y_axis_label == "Prix"
    assert [b["label"] for b in rebuilt.bars] == ["Prévu", "Réel"]
    assert [b["value"] for b in rebuilt.bars] == [1000.0, 1200.0]
