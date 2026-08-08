from __future__ import annotations

from blocks.list_block import LIST_BLOCK_TYPE, LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock
from blocks.registry import block_from_dict


def test_list_block_defaults():
    block = ListBlock()
    assert block.type == LIST_BLOCK_TYPE
    assert block.list_type == LIST_TYPE_BULLET
    assert block.items == []


def test_add_remove_item():
    block = ListBlock()
    item = block.add_item("Premier")
    assert len(block.items) == 1

    assert block.remove_item(item["id"]) is True
    assert block.items == []
    assert block.remove_item("inconnu") is False


def test_set_item_text():
    block = ListBlock()
    item = block.add_item("A")
    assert block.set_item_text(item["id"], "B") is True
    assert block.items[0]["text"] == "B"
    assert block.set_item_text("inconnu", "X") is False


def test_move_item():
    block = ListBlock()
    a = block.add_item("A")
    b = block.add_item("B")
    block.move_item(b["id"], 0)
    assert [i["text"] for i in block.items] == ["B", "A"]


def test_set_list_type():
    block = ListBlock()
    assert block.set_list_type(LIST_TYPE_NUMBERED) is True
    assert block.list_type == LIST_TYPE_NUMBERED
    assert block.set_list_type("inconnu") is False
    assert block.list_type == LIST_TYPE_NUMBERED


def test_list_block_roundtrip_via_registry():
    block = ListBlock(list_type=LIST_TYPE_NUMBERED)
    block.add_item("Étape 1")
    block.add_item("Étape 2")

    rebuilt = block_from_dict(block.to_dict())

    assert isinstance(rebuilt, ListBlock)
    assert rebuilt.list_type == LIST_TYPE_NUMBERED
    assert [i["text"] for i in rebuilt.items] == ["Étape 1", "Étape 2"]
