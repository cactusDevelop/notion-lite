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
from core.document_html_export import document_to_html


def test_heading_rendered_with_correct_level():
    doc = Document()
    doc.add_block(HeadingBlock(level=2, content="Titre"))
    html = document_to_html(doc)
    assert "<h2>Titre</h2>" in html


def test_text_block_uses_its_html_when_present():
    doc = Document()
    block = TextBlock()
    block.html = "<p><b>Gras</b></p>"
    doc.add_block(block)
    assert "<b>Gras</b>" in document_to_html(doc)


def test_checklist_rendered_as_unordered_list():
    doc = Document()
    block = ChecklistBlock()
    block.add_item("Fait")
    doc.add_block(block)
    html = document_to_html(doc)
    assert "<ul>" in html and "Fait" in html


def test_list_block_numbered_uses_ol_tag():
    doc = Document()
    block = ListBlock(list_type=LIST_TYPE_NUMBERED)
    block.add_item("Étape 1")
    doc.add_block(block)
    html = document_to_html(doc)
    assert "<ol>" in html and "Étape 1" in html


def test_table_block_renders_html_table_with_headers():
    doc = Document()
    table = TableBlock()
    col = table.add_column("Nom", col_type=COLUMN_TYPE_TEXT)
    table.add_row(values={col["id"]: "Alice"})
    doc.add_block(table)
    html = document_to_html(doc)
    assert "<th>Nom</th>" in html
    assert "<td>Alice</td>" in html


def test_boolean_cell_rendered_as_checkbox_symbol():
    doc = Document()
    table = TableBlock()
    col = table.add_column("Fait", col_type=COLUMN_TYPE_BOOLEAN)
    table.add_row(values={col["id"]: True})
    doc.add_block(table)
    assert "☑" in document_to_html(doc)


def test_simple_table_block_renders_table():
    doc = Document()
    doc.add_block(SimpleTableBlock(rows=[["a", "b"], ["c", "d"]]))
    html = document_to_html(doc)
    assert "<td>a</td>" in html and "<td>d</td>" in html


def test_quote_and_code_and_separator_rendered():
    doc = Document()
    doc.add_block(QuoteBlock(content="Citation"))
    doc.add_block(CodeBlock(content="x = 1"))
    doc.add_block(SeparatorBlock())
    html = document_to_html(doc)
    assert "<blockquote>" in html
    assert "<pre><code>x = 1</code></pre>" in html
    assert "<hr/>" in html


def test_empty_gantt_block_renders_placeholder():
    doc = Document()
    doc.add_block(GanttBlock())
    html = document_to_html(doc)
    assert "Gantt vide" in html


def test_html_is_escaped_to_avoid_injection():
    doc = Document()
    doc.add_block(HeadingBlock(level=1, content="<script>alert(1)</script>"))
    html = document_to_html(doc)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_document_to_html_keeps_all_blocks_in_order():
    doc = Document()
    doc.add_block(TextBlock(content="Un"))
    doc.add_block(SeparatorBlock())
    doc.add_block(TextBlock(content="Deux"))
    html = document_to_html(doc)
    assert html.index("Un") < html.index("<hr/>") < html.index("Deux")


def test_export_document_to_pdf_creates_a_real_file(tmp_path):
    import os
    import sys

    import pytest

    pytest.importorskip("PySide6.QtPrintSupport")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication(sys.argv)

    from ui.export_pdf import export_document_to_pdf

    doc = Document()
    doc.add_block(HeadingBlock(level=1, content="Rapport"))
    doc.add_block(TextBlock(content="Contenu de test."))

    output = tmp_path / "export.pdf"
    export_document_to_pdf(doc, str(output))

    assert output.exists()
    assert output.stat().st_size > 0
    assert output.read_bytes().startswith(b"%PDF")
