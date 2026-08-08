from __future__ import annotations

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.gantt_block import GanttBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.block_icons import icon_for_block


def test_each_block_type_has_a_distinct_icon():
    blocks = [
        TextBlock(),
        HeadingBlock(level=1),
        ChecklistBlock(),
        ListBlock(),
        TableBlock(),
        SimpleTableBlock(),
        GanttBlock(),
        ImageBlock(),
        QuoteBlock(),
        CodeBlock(),
        SeparatorBlock(),
    ]
    icons = [icon_for_block(b) for b in blocks]
    assert all(icon for icon in icons)
    assert len(set(icons)) == len(icons)


def test_heading_checked_before_text_no_collision():
    # HeadingBlock ne doit jamais recevoir l'icône du texte simple.
    assert icon_for_block(HeadingBlock(level=2)) != icon_for_block(TextBlock())


def test_unknown_block_falls_back_to_default_icon():
    class _Mystery:
        pass

    assert icon_for_block(_Mystery()) == "▫"
