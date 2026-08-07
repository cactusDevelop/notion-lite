"""
PATCH 10 — Tests du bloc Checklist : édition libre des éléments et
persistance JSON via Document.to_dict / from_dict.
"""
from __future__ import annotations

import unittest

from blocks.checklist_block import ChecklistBlock
from core.document import Document


class ChecklistBlockTests(unittest.TestCase):
    def test_add_item_appends_and_returns_item(self) -> None:
        block = ChecklistBlock()
        item = block.add_item(text="Acheter du lait")

        self.assertEqual(len(block.items), 1)
        self.assertEqual(item["text"], "Acheter du lait")
        self.assertFalse(item["checked"])

    def test_set_item_text_and_checked(self) -> None:
        block = ChecklistBlock()
        item = block.add_item(text="Tâche")

        block.set_item_text(item["id"], "Tâche modifiée")
        block.set_item_checked(item["id"], True)

        self.assertEqual(block.items[0]["text"], "Tâche modifiée")
        self.assertTrue(block.items[0]["checked"])

    def test_remove_item(self) -> None:
        block = ChecklistBlock()
        item = block.add_item(text="À supprimer")

        self.assertTrue(block.remove_item(item["id"]))
        self.assertEqual(len(block.items), 0)
        self.assertFalse(block.remove_item("id-inconnu"))

    def test_document_roundtrip_preserves_checklist(self) -> None:
        document = Document()
        block = ChecklistBlock()
        block.add_item(text="Non cochée", checked=False)
        block.add_item(text="Cochée", checked=True)
        document.add_block(block)

        restored = Document.from_dict(document.to_dict())
        restored_block = restored.blocks[0]

        self.assertEqual(restored_block.type, "checklist")
        self.assertEqual(restored_block.data["items"], block.items)


if __name__ == "__main__":
    unittest.main()
