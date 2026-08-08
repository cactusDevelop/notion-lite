from __future__ import annotations

from blocks.code_block import CODE_BLOCK_TYPE, CodeBlock, DEFAULT_LANGUAGE
from blocks.registry import block_from_dict


def test_code_block_defaults():
    block = CodeBlock()
    assert block.type == CODE_BLOCK_TYPE
    assert block.content == ""
    assert block.language == DEFAULT_LANGUAGE


def test_code_block_setters():
    block = CodeBlock()
    block.content = "print('hello')"
    block.language = "python"
    assert block.content == "print('hello')"
    assert block.language == "python"


def test_code_block_language_falls_back_when_empty():
    block = CodeBlock(language="python")
    block.language = ""
    assert block.language == DEFAULT_LANGUAGE


def test_code_block_roundtrip_via_registry():
    block = CodeBlock(content="x = 1", language="python")
    rebuilt = block_from_dict(block.to_dict())

    assert isinstance(rebuilt, CodeBlock)
    assert rebuilt.content == "x = 1"
    assert rebuilt.language == "python"
