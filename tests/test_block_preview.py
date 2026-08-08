"""
PATCH 30 — Tests de core.block_preview.preview_for_block (sans Qt).
"""
from __future__ import annotations

import unittest

from blocks.checklist_block import ChecklistBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.list_block import ListBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.block_preview import preview_for_block


class BlockPreviewTests(unittest.TestCase):
    def test_text_block_preview(self) -> None:
        block = TextBlock(content="Bonjour le monde")
        self.assertEqual(preview_for_block(block), "Bonjour le monde")

    def test_empty_text_block_preview(self) -> None:
        block = TextBlock(content="")
        self.assertEqual(preview_for_block(block), "(vide)")

    def test_heading_block_preview(self) -> None:
        block = HeadingBlock(level=1, content="Titre principal")
        self.assertEqual(preview_for_block(block), "Titre principal")

    def test_long_text_is_truncated(self) -> None:
        block = TextBlock(content="x" * 200)
        preview = preview_for_block(block)
        self.assertTrue(preview.endswith("…"))
        self.assertLess(len(preview), 200)

    def test_newlines_are_flattened(self) -> None:
        block = TextBlock(content="Ligne 1\nLigne 2")
        self.assertEqual(preview_for_block(block), "Ligne 1 Ligne 2")

    def test_checklist_preview_uses_first_item(self) -> None:
        block = ChecklistBlock()
        block.add_item("Première tâche")
        block.add_item("Deuxième tâche")
        self.assertEqual(preview_for_block(block), "Première tâche")

    def test_empty_checklist_preview(self) -> None:
        block = ChecklistBlock()
        self.assertEqual(preview_for_block(block), "(checklist vide)")

    def test_list_preview_uses_first_item(self) -> None:
        block = ListBlock()
        block.add_item("Élément unique")
        self.assertEqual(preview_for_block(block), "Élément unique")

    def test_table_preview_mentions_column_count(self) -> None:
        block = TableBlock()
        block.add_column(name="Nom")
        block.add_column(name="Âge")
        self.assertIn("2 colonnes", preview_for_block(block))

    def test_simple_table_preview_mentions_dimensions(self) -> None:
        block = SimpleTableBlock(row_count=3, column_count=2)
        self.assertIn("3×2", preview_for_block(block))

    def test_image_block_preview(self) -> None:
        block = ImageBlock()
        self.assertEqual(preview_for_block(block), "(image)")

    def test_separator_block_preview(self) -> None:
        block = SeparatorBlock()
        self.assertEqual(preview_for_block(block), "(séparateur)")


if __name__ == "__main__":
    unittest.main()
