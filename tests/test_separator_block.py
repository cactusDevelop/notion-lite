from __future__ import annotations

from blocks.registry import block_from_dict
from blocks.separator_block import SEPARATOR_BLOCK_TYPE, SeparatorBlock


def test_separator_block_has_no_data():
    block = SeparatorBlock()
    assert block.type == SEPARATOR_BLOCK_TYPE
    assert block.data == {}


def test_separator_block_roundtrip_via_registry():
    block = SeparatorBlock()
    rebuilt = block_from_dict(block.to_dict())

    assert isinstance(rebuilt, SeparatorBlock)
    assert rebuilt.id == block.id
    assert rebuilt.type == SEPARATOR_BLOCK_TYPE
