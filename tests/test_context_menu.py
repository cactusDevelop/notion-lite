"""
PATCH 26 — Menu contextuel : duplication, conversion et ajout de bloc
en fin de document. Teste la logique (MainWindow) sans event loop
interactif (le QMenu affiché n'est pas exercé ici, seulement les
actions qu'il déclenche).
"""
from __future__ import annotations

import sys

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.heading_block import HeadingBlock  # noqa: E402
from blocks.quote_block import QuoteBlock  # noqa: E402
from blocks.text_block import TextBlock  # noqa: E402
from core.document import Document  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def window(qapp):
    win = MainWindow()
    win._document = Document()
    win._render_document()
    return win


def test_duplicate_block_inserts_copy_right_after_original(window):
    block = TextBlock(content="Original")
    window._document.add_block(block)
    window._render_document()

    window._duplicate_block(block.id)

    assert len(window._document) == 2
    assert window._document.blocks[1].content == "Original"
    assert window._document.blocks[1].id != block.id


def test_convert_block_preserves_content(window):
    block = TextBlock(content="Bonjour")
    window._document.add_block(block)
    window._render_document()

    window._convert_block(block.id, "quote")

    assert len(window._document) == 1
    converted = window._document.blocks[0]
    assert isinstance(converted, QuoteBlock)
    assert converted.content == "Bonjour"


def test_convert_block_unknown_target_is_a_noop(window):
    block = TextBlock(content="Bonjour")
    window._document.add_block(block)
    window._render_document()

    window._convert_block(block.id, "not_a_real_target")

    assert len(window._document) == 1
    assert isinstance(window._document.blocks[0], TextBlock)


def test_append_block_from_command_adds_at_the_end(window):
    window._document.add_block(HeadingBlock(level=1, content="Titre"))
    window._render_document()

    window._append_block_from_command("quote")

    assert len(window._document) == 2
    assert window._document.blocks[-1].type == "quote"
