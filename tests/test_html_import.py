from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.list_block import LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.text_block import TextBlock
from core.document_html_import import html_to_document


def test_heading_levels():
    doc = html_to_document("<h1>Un</h1><h2>Deux</h2><h6>Six</h6>")
    blocks = doc.blocks
    assert [b.data["level"] for b in blocks] == [1, 2, 3]
    assert blocks[0].content == "Un"


def test_paragraph_preserves_rich_html():
    doc = html_to_document("<p>Salut <b>gras</b></p>")
    block = doc.blocks[0]
    assert isinstance(block, TextBlock)
    assert block.content == "Salut gras"
    assert "<b>gras</b>" in block.html


def test_empty_paragraph_is_skipped():
    doc = html_to_document("<p></p><p>Réel</p>")
    assert len(doc.blocks) == 1
    assert doc.blocks[0].content == "Réel"


def test_bullet_and_numbered_lists():
    doc = html_to_document("<ul><li>Un</li><li>Deux</li></ul><ol><li>A</li><li>B</li></ol>")
    ul_block, ol_block = doc.blocks
    assert isinstance(ul_block, ListBlock) and ul_block.list_type == LIST_TYPE_BULLET
    assert [i["text"] for i in ul_block.items] == ["Un", "Deux"]
    assert isinstance(ol_block, ListBlock) and ol_block.list_type == LIST_TYPE_NUMBERED


def test_checklist_markers_reconstruct_checklist_block():
    doc = html_to_document("<ul><li>☑ Fait</li><li>☐ À faire</li></ul>")
    block = doc.blocks[0]
    assert isinstance(block, ChecklistBlock)
    assert [i["text"] for i in block.items] == ["Fait", "À faire"]
    assert [i["checked"] for i in block.items] == [True, False]


def test_blockquote_parsing():
    doc = html_to_document("<blockquote><i>Sagesse</i></blockquote>")
    assert isinstance(doc.blocks[0], QuoteBlock)
    assert doc.blocks[0].content == "Sagesse"


def test_code_block_parsing_unescapes_entities():
    doc = html_to_document("<pre><code>if a &lt; b: pass</code></pre>")
    block = doc.blocks[0]
    assert isinstance(block, CodeBlock)
    assert block.content == "if a < b: pass"


def test_table_parsing():
    html = "<table><tr><th>Nom</th><th>Âge</th></tr><tr><td>Alice</td><td>30</td></tr></table>"
    doc = html_to_document(html)
    block = doc.blocks[0]
    assert isinstance(block, SimpleTableBlock)
    assert block.rows == [["Nom", "Âge"], ["Alice", "30"]]


def test_separator_parsing():
    doc = html_to_document("<p>Un</p><hr/><p>Deux</p>")
    assert isinstance(doc.blocks[1], SeparatorBlock)


def test_image_data_uri_parsing():
    doc = html_to_document('<img src="data:image/png;base64,QUJD" width="200" />')
    block = doc.blocks[0]
    assert isinstance(block, ImageBlock)
    assert block.data["image_base64"] == "QUJD"
    assert block.data["format"] == "png"
    assert block.data["width"] == 200


def test_full_roundtrip_via_export_then_import():
    from core.document import Document
    from core.document_html_export import document_to_full_html

    original = Document()
    original.add_block(HeadingBlock(level=2, content="Titre"))
    checklist = ChecklistBlock()
    checklist.add_item("Tâche", checked=True)
    original.add_block(checklist)
    original.add_block(SeparatorBlock())

    html = document_to_full_html(original, title="Test")
    rebuilt = html_to_document(html)

    assert isinstance(rebuilt.blocks[0], HeadingBlock)
    assert rebuilt.blocks[0].content == "Titre"
    assert isinstance(rebuilt.blocks[1], ChecklistBlock)
    assert rebuilt.blocks[1].items[0]["checked"] is True
    assert isinstance(rebuilt.blocks[2], SeparatorBlock)
