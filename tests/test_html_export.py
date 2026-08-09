from __future__ import annotations

from blocks.heading_block import HeadingBlock
from blocks.text_block import TextBlock
from core.document import Document
from core.document_html_export import document_to_full_html, document_to_html


def test_full_html_wraps_the_fragment():
    doc = Document()
    doc.add_block(HeadingBlock(level=1, content="Titre"))
    fragment = document_to_html(doc)
    full = document_to_full_html(doc)
    assert fragment in full


def test_full_html_has_doctype_and_charset():
    doc = Document()
    doc.add_block(TextBlock(content="Bonjour"))
    full = document_to_full_html(doc)
    assert full.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8" />' in full
    assert "<html" in full and "</html>" in full


def test_full_html_title_is_escaped():
    doc = Document()
    full = document_to_full_html(doc, title="<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in full
    assert "&lt;script&gt;" in full


def test_full_html_default_title():
    doc = Document()
    full = document_to_full_html(doc)
    assert "<title>Document</title>" in full


def test_full_html_is_valid_utf8_encodable():
    doc = Document()
    doc.add_block(TextBlock(content="éàçüñ日本語"))
    full = document_to_full_html(doc)
    full.encode("utf-8")
    assert "éàçüñ日本語" in full
