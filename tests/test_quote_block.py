from __future__ import annotations

from blocks.quote_block import QUOTE_BLOCK_TYPE, QuoteBlock
from blocks.registry import block_from_dict


def test_quote_block_default_content_is_empty():
    block = QuoteBlock()
    assert block.type == QUOTE_BLOCK_TYPE
    assert block.content == ""


def test_quote_block_content_setter():
    block = QuoteBlock()
    block.content = "La simplicité est la sophistication suprême."
    assert block.content == "La simplicité est la sophistication suprême."


def test_quote_block_roundtrip_via_registry():
    block = QuoteBlock(content="Carpe diem")
    rebuilt = block_from_dict(block.to_dict())

    assert isinstance(rebuilt, QuoteBlock)
    assert rebuilt.content == "Carpe diem"
    assert rebuilt.id == block.id
