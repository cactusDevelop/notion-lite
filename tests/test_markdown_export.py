from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.gantt_block import GanttBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import COLUMN_TYPE_BOOLEAN, COLUMN_TYPE_TEXT, TableBlock
from blocks.text_block import TextBlock
from core.document import Document
from core.document_markdown_export import document_to_markdown


def test_heading_uses_correct_number_of_hashes():
    doc = Document()
    doc.add_block(HeadingBlock(level=3, content="Titre"))
    assert document_to_markdown(doc) == "### Titre"


def test_text_block_plain_content():
    doc = Document()
    block = TextBlock(content="Bonjour")
    block.html = "<p><b>Bonjour</b></p>"
    doc.add_block(block)
    assert document_to_markdown(doc) == "Bonjour"


def test_checklist_rendered_as_task_list():
    doc = Document()
    block = ChecklistBlock()
    block.add_item("Fait")
    block.add_item("À faire")
    block.set_checked(block.items[0]["id"], True) if hasattr(block, "set_checked") else block.items[0].__setitem__("checked", True)
    doc.add_block(block)
    md = document_to_markdown(doc)
    assert "- [x] Fait" in md
    assert "- [ ] À faire" in md


def test_numbered_list_renders_with_numbers():
    doc = Document()
    block = ListBlock(list_type=LIST_TYPE_NUMBERED)
    block.add_item("Un")
    block.add_item("Deux")
    doc.add_block(block)
    assert document_to_markdown(doc) == "1. Un\n2. Deux"


def test_table_renders_valid_markdown_table():
    doc = Document()
    table = TableBlock()
    col = table.add_column("Nom", col_type=COLUMN_TYPE_TEXT)
    table.add_row(values={col["id"]: "Alice"})
    doc.add_block(table)
    md = document_to_markdown(doc)
    lines = md.split("\n")
    assert lines[0] == "| Nom |"
    assert lines[1] == "| --- |"
    assert lines[2] == "| Alice |"


def test_boolean_cell_rendered_as_checkbox_symbol():
    doc = Document()
    table = TableBlock()
    col = table.add_column("Fait", col_type=COLUMN_TYPE_BOOLEAN)
    table.add_row(values={col["id"]: True})
    doc.add_block(table)
    assert "☑" in document_to_markdown(doc)


def test_pipe_character_is_escaped_in_table_cells():
    doc = Document()
    table = TableBlock()
    col = table.add_column("Nom", col_type=COLUMN_TYPE_TEXT)
    table.add_row(values={col["id"]: "A | B"})
    doc.add_block(table)
    assert "A \\| B" in document_to_markdown(doc)


def test_simple_table_first_row_is_header():
    doc = Document()
    doc.add_block(SimpleTableBlock(rows=[["a", "b"], ["c", "d"]]))
    md = document_to_markdown(doc)
    assert md.split("\n")[0] == "| a | b |"


def test_quote_and_code_and_separator():
    doc = Document()
    doc.add_block(QuoteBlock(content="Sagesse"))
    doc.add_block(CodeBlock(content="x = 1", language="python"))
    doc.add_block(SeparatorBlock())
    md = document_to_markdown(doc)
    assert "> Sagesse" in md
    assert "```python\nx = 1\n```" in md
    assert "---" in md


def test_empty_gantt_block_renders_placeholder():
    doc = Document()
    doc.add_block(GanttBlock())
    assert "Gantt vide" in document_to_markdown(doc)


def test_blocks_separated_by_blank_line():
    doc = Document()
    doc.add_block(TextBlock(content="Un"))
    doc.add_block(TextBlock(content="Deux"))
    assert document_to_markdown(doc) == "Un\n\nDeux"
