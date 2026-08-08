"""
PATCH 27 — Tests de la pile Undo/Redo générique (sans Qt).
"""
from __future__ import annotations

import unittest

from core.history import UndoHistory


class UndoHistoryTests(unittest.TestCase):
    def test_check_is_a_noop_when_nothing_changed(self) -> None:
        history = UndoHistory("A")
        self.assertFalse(history.check("A"))
        self.assertFalse(history.can_undo())

    def test_check_creates_undo_point_on_change(self) -> None:
        history = UndoHistory("A")
        self.assertTrue(history.check("B"))
        self.assertTrue(history.can_undo())
        self.assertEqual(history.baseline, "B")

    def test_undo_returns_previous_state(self) -> None:
        history = UndoHistory("A")
        history.check("B")
        previous = history.undo("B")
        self.assertEqual(previous, "A")
        self.assertEqual(history.baseline, "A")

    def test_undo_flushes_pending_change_first(self) -> None:
        """Ctrl+Z doit annuler même une frappe pas encore "sondée"."""
        history = UndoHistory("A")
        # Aucun history.check("B") explicite avant l'undo : il doit
        # quand même être pris en compte (flush synchrone).
        previous = history.undo("B")
        self.assertEqual(previous, "A")

    def test_undo_with_nothing_to_undo_returns_none(self) -> None:
        history = UndoHistory("A")
        self.assertIsNone(history.undo("A"))

    def test_redo_restores_undone_state(self) -> None:
        history = UndoHistory("A")
        history.check("B")
        history.undo("B")
        self.assertEqual(history.redo(), "B")
        self.assertEqual(history.baseline, "B")

    def test_redo_with_nothing_to_redo_returns_none(self) -> None:
        history = UndoHistory("A")
        self.assertIsNone(history.redo())

    def test_new_action_after_undo_clears_redo_stack(self) -> None:
        history = UndoHistory("A")
        history.check("B")
        history.undo("B")  # baseline = "A", redo dispo = "B"
        self.assertTrue(history.can_redo())

        history.check("C")  # nouvelle action : redo devient obsolète
        self.assertFalse(history.can_redo())

    def test_multi_step_undo_redo_round_trip(self) -> None:
        history = UndoHistory("A")
        history.check("B")
        history.check("C")
        history.check("D")

        self.assertEqual(history.undo("D"), "C")
        self.assertEqual(history.undo("C"), "B")
        self.assertEqual(history.undo("B"), "A")
        self.assertIsNone(history.undo("A"))

        self.assertEqual(history.redo(), "B")
        self.assertEqual(history.redo(), "C")
        self.assertEqual(history.redo(), "D")
        self.assertIsNone(history.redo())

    def test_max_history_caps_undo_stack_size(self) -> None:
        history = UndoHistory("0", max_history=3)
        for i in range(1, 10):
            history.check(str(i))

        undo_count = 0
        current = "9"
        while True:
            previous = history.undo(current)
            if previous is None:
                break
            current = previous
            undo_count += 1

        self.assertEqual(undo_count, 3)


if __name__ == "__main__":
    unittest.main()
