"""
PATCH 44 — Tests du bloc "Checklists liées" : répartition des
éléments entre panneaux selon leur état coché, et persistance JSON.
"""
from __future__ import annotations

import unittest

from blocks.linked_checklist_block import LinkedChecklistBlock
from core.document import Document


class LinkedChecklistBlockTests(unittest.TestCase):
    def test_add_item_is_todo_by_default(self) -> None:
        block = LinkedChecklistBlock()
        item = block.add_item(text="A")

        self.assertEqual(block.todo_items(), [item])
        self.assertEqual(block.done_items(), [])

    def test_checking_item_moves_it_to_done(self) -> None:
        block = LinkedChecklistBlock()
        item = block.add_item(text="A")

        block.set_item_checked(item["id"], True)

        self.assertEqual(block.todo_items(), [])
        self.assertEqual(len(block.done_items()), 1)
        self.assertTrue(block.done_items()[0]["checked"])

    def test_unchecking_item_moves_it_back_to_todo(self) -> None:
        block = LinkedChecklistBlock()
        item = block.add_item(text="A", checked=True)

        block.set_item_checked(item["id"], False)

        self.assertEqual(block.done_items(), [])
        self.assertEqual(len(block.todo_items()), 1)

    def test_remove_item(self) -> None:
        block = LinkedChecklistBlock()
        item = block.add_item(text="À supprimer")

        self.assertTrue(block.remove_item(item["id"]))
        self.assertEqual(len(block.items), 0)
        self.assertFalse(block.remove_item("id-inconnu"))

    def test_split_is_clamped(self) -> None:
        block = LinkedChecklistBlock()

        block.split = 1.5
        self.assertEqual(block.split, 0.95)

        block.split = -1
        self.assertEqual(block.split, 0.05)

    def test_document_roundtrip_preserves_items_and_split(self) -> None:
        document = Document()
        block = LinkedChecklistBlock(split=0.3)
        block.add_item(text="A")
        block.add_item(text="B", checked=True)
        document.add_block(block)

        restored = Document.from_dict(document.to_dict())
        restored_block = restored.blocks[0]

        self.assertIsInstance(restored_block, LinkedChecklistBlock)
        self.assertEqual(restored_block.split, 0.3)
        self.assertEqual(len(restored_block.todo_items()), 1)
        self.assertEqual(len(restored_block.done_items()), 1)


if __name__ == "__main__":
    unittest.main()
