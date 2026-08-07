"""
PATCH 11 — Vérifie que ChecklistBlock.sort_by_status trie les tâches
non cochées avant les tâches cochées, de façon stable.
"""
from __future__ import annotations

import unittest

from blocks.checklist_block import ChecklistBlock


class ChecklistSortTests(unittest.TestCase):
    def test_unchecked_come_before_checked(self) -> None:
        block = ChecklistBlock()
        block.add_item("Déjà faite", checked=True)
        block.add_item("À faire A", checked=False)
        block.add_item("À faire B", checked=False)

        block.sort_by_status()

        self.assertEqual(
            [item["text"] for item in block.items],
            ["À faire A", "À faire B", "Déjà faite"],
        )

    def test_sort_is_stable_within_each_group(self) -> None:
        block = ChecklistBlock()
        block.add_item("checked 1", checked=True)
        block.add_item("unchecked 1", checked=False)
        block.add_item("checked 2", checked=True)
        block.add_item("unchecked 2", checked=False)

        block.sort_by_status()

        self.assertEqual(
            [item["text"] for item in block.items],
            ["unchecked 1", "unchecked 2", "checked 1", "checked 2"],
        )

    def test_toggling_an_item_moves_it_to_the_checked_group(self) -> None:
        block = ChecklistBlock()
        item_a = block.add_item("A", checked=False)
        block.add_item("B", checked=False)
        block.add_item("C", checked=False)

        block.set_item_checked(item_a["id"], True)  # "A" cochée
        block.sort_by_status()

        self.assertEqual([item["text"] for item in block.items], ["B", "C", "A"])

    def test_legacy_items_without_id_are_backfilled(self) -> None:
        """Les checklists sauvegardées avant le correctif d'API (id) se
        rechargent sans erreur : un id est généré à la volée."""
        block = ChecklistBlock(items=[{"text": "Ancien format", "checked": False}])

        self.assertTrue(block.items[0]["id"])
        self.assertTrue(block.set_item_checked(block.items[0]["id"], True))
        self.assertTrue(block.items[0]["checked"])


if __name__ == "__main__":
    unittest.main()
