"""
Vérifie que Maj+Entrée sépare un bloc texte en deux, et qu'Entrée
seule insère un simple retour à la ligne dans le même bloc (comportement
inversé par rapport à Notion, sur demande explicite).
"""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QKeyEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from blocks.text_block import TextBlock  # noqa: E402
from ui.blocks.text_block_widget import TextBlockWidget  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication(sys.argv)


def _press_enter(widget: TextBlockWidget, shift: bool) -> None:
    modifiers = Qt.ShiftModifier if shift else Qt.NoModifier
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, modifiers, "\r")
    widget.keyPressEvent(event)


def test_plain_enter_inserts_newline_without_splitting(qapp):
    widget = TextBlockWidget(TextBlock(content="Bonjour"))
    widget.setPlainText("Bonjour")
    cursor = widget.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    widget.setTextCursor(cursor)

    received = []
    widget.split_requested.connect(lambda *args: received.append(args))

    _press_enter(widget, shift=False)

    assert received == []
    assert "\n" in widget.toPlainText()


def test_shift_enter_requests_a_split(qapp):
    widget = TextBlockWidget(TextBlock(content="Bonjour le monde"))
    widget.setPlainText("Bonjour le monde")
    cursor = widget.textCursor()
    cursor.setPosition(len("Bonjour"))
    widget.setTextCursor(cursor)

    received = []
    widget.split_requested.connect(lambda w, before, after: received.append((before, after)))

    _press_enter(widget, shift=True)

    assert received == [("Bonjour", " le monde")]
