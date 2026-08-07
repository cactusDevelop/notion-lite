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
        block.add_item("A", checked=False)
        block.add_item("B", checked=False)
        block.add_item("C", checked=False)

        block.set_item_checked(0, True)  # "A" cochée
        block.sort_by_status()

        self.assertEqual([item["text"] for item in block.items], ["B", "C", "A"])


if __name__ == "__main__":
    unittest.main()
