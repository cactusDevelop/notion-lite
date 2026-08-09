from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.text_block import TextBlock
from core.document_markdown_import import markdown_to_document


def test_heading_levels():
    doc = markdown_to_document("# Un\n\n## Deux\n\n### Trois\n\n###### Six")
    blocks = doc.blocks
    assert [isinstance(b, HeadingBlock) for b in blocks] == [True] * 4
    assert [b.data["level"] for b in blocks] == [1, 2, 3, 3]  # niveau 6 ramené à 3
    assert blocks[0].content == "Un"


def test_paragraph_becomes_text_block():
    doc = markdown_to_document("Bonjour le monde.")
    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], TextBlock)
    assert doc.blocks[0].content == "Bonjour le monde."


def test_code_fence_with_language():
    doc = markdown_to_document("```python\nx = 1\ny = 2\n```")
    block = doc.blocks[0]
    assert isinstance(block, CodeBlock)
    assert block.language == "python"
    assert block.content == "x = 1\ny = 2"


def test_checklist_parsing():
    doc = markdown_to_document("- [x] Fait\n- [ ] À faire")
    block = doc.blocks[0]
    assert isinstance(block, ChecklistBlock)
    assert [i["text"] for i in block.items] == ["Fait", "À faire"]
    assert [i["checked"] for i in block.items] == [True, False]


def test_bullet_list_does_not_capture_checklist_lines():
    doc = markdown_to_document("- Un\n- Deux")
    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.list_type == LIST_TYPE_BULLET
    assert [i["text"] for i in block.items] == ["Un", "Deux"]


def test_numbered_list_parsing():
    doc = markdown_to_document("1. Un\n2. Deux\n3. Trois")
    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.list_type == LIST_TYPE_NUMBERED
    assert [i["text"] for i in block.items] == ["Un", "Deux", "Trois"]


def test_table_parsing():
    md = "| Nom | Âge |\n| --- | --- |\n| Alice | 30 |\n| Bob | 25 |"
    doc = markdown_to_document(md)
    block = doc.blocks[0]
    assert isinstance(block, SimpleTableBlock)
    assert block.rows == [["Nom", "Âge"], ["Alice", "30"], ["Bob", "25"]]


def test_separator_parsing():
    doc = markdown_to_document("Un\n\n---\n\nDeux")
    assert isinstance(doc.blocks[1], SeparatorBlock)


def test_quote_parsing_multiline():
    doc = markdown_to_document("> Ligne 1\n> Ligne 2")
    block = doc.blocks[0]
    assert isinstance(block, QuoteBlock)
    assert block.content == "Ligne 1\nLigne 2"


def test_full_roundtrip_via_export_then_import():
    from core.document import Document
    from core.document_markdown_export import document_to_markdown

    original = Document()
    original.add_block(HeadingBlock(level=2, content="Titre"))
    original.add_block(TextBlock(content="Un paragraphe."))
    checklist = ChecklistBlock()
    checklist.add_item("Tâche", checked=True)
    original.add_block(checklist)

    md = document_to_markdown(original)
    rebuilt = markdown_to_document(md)

    assert isinstance(rebuilt.blocks[0], HeadingBlock)
    assert rebuilt.blocks[0].content == "Titre"
    assert isinstance(rebuilt.blocks[1], TextBlock)
    assert isinstance(rebuilt.blocks[2], ChecklistBlock)
    assert rebuilt.blocks[2].items[0]["checked"] is True
