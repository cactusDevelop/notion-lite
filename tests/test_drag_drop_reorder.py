"""
PATCH 13 — Vérifie que Document.move_block, combiné à l'ajustement
d'index utilisé par MainWindow._on_block_dropped, replace bien un
bloc glissé-déposé à l'endroit attendu (avant ou après sa position
d'origine).
"""
from __future__ import annotations

import unittest

from blocks.text_block import TextBlock
from core.document import Document


def _dropped_index(current_index: int, target_index: int) -> int:
    """Reproduit l'ajustement d'index fait par MainWindow._on_block_dropped."""
    if target_index > current_index:
        target_index -= 1
    return target_index


class DragDropReorderTests(unittest.TestCase):
    def _build_document(self, labels: list[str]) -> Document:
        document = Document()
        for label in labels:
            document.add_block(TextBlock(content=label))
        return document

    def test_move_block_earlier(self) -> None:
        document = self._build_document(["A", "B", "C", "D"])
        block_id = document.blocks[2].id  # "C"

        target = _dropped_index(current_index=2, target_index=0)
        document.move_block(block_id, target)

        self.assertEqual([b.content for b in document.blocks], ["C", "A", "B", "D"])

    def test_move_block_later(self) -> None:
        document = self._build_document(["A", "B", "C", "D"])
        block_id = document.blocks[0].id  # "A"

        # Dépose entre "C" et "D" (index brut 3 dans le layout).
        target = _dropped_index(current_index=0, target_index=3)
        document.move_block(block_id, target)

        self.assertEqual([b.content for b in document.blocks], ["B", "C", "A", "D"])

    def test_drop_on_same_spot_is_a_noop(self) -> None:
        document = self._build_document(["A", "B", "C"])
        block_id = document.blocks[1].id  # "B"

        target = _dropped_index(current_index=1, target_index=1)
        self.assertEqual(target, 1)
        document.move_block(block_id, target)

        self.assertEqual([b.content for b in document.blocks], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
