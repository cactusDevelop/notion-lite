"""
PATCH 9 — Vérifie que la sauvegarde/chargement restaure toutes les
données d'un document (id, type, contenu complet de chaque bloc).
"""
from __future__ import annotations

import unittest

from blocks.heading_block import HeadingBlock
from blocks.text_block import TextBlock
from core.document import Document, DOCUMENT_FORMAT_VERSION


class DocumentRoundtripTests(unittest.TestCase):
    def _build_sample_document(self) -> Document:
        document = Document()
        document.add_block(HeadingBlock(level=1, content="Titre principal"))
        document.add_block(HeadingBlock(level=2, content="Sous-titre"))
        document.add_block(
            TextBlock(content="Bonjour le monde", html="<p><b>Bonjour</b> le monde</p>")
        )
        return document

    def test_to_dict_contains_version_and_ordered_blocks(self) -> None:
        raw = self._build_sample_document().to_dict()
        self.assertEqual(raw["version"], DOCUMENT_FORMAT_VERSION)
        self.assertEqual(len(raw["blocks"]), 3)

    def test_roundtrip_preserves_every_field(self) -> None:
        original = self._build_sample_document()
        restored = Document.from_dict(original.to_dict())

        self.assertEqual(len(restored), len(original))
        for original_block, restored_block in zip(original.blocks, restored.blocks):
            self.assertEqual(restored_block.id, original_block.id)
            self.assertEqual(restored_block.type, original_block.type)
            self.assertEqual(restored_block.data, original_block.data)

    def test_roundtrip_preserves_block_order(self) -> None:
        original = self._build_sample_document()
        restored = Document.from_dict(original.to_dict())

        self.assertEqual(
            [block.id for block in restored.blocks],
            [block.id for block in original.blocks],
        )

    def test_empty_document_roundtrip(self) -> None:
        restored = Document.from_dict(Document().to_dict())
        self.assertEqual(len(restored), 0)

    def test_missing_blocks_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            Document.from_dict({"version": DOCUMENT_FORMAT_VERSION})

    def test_future_version_raises(self) -> None:
        raw = self._build_sample_document().to_dict()
        raw["version"] = DOCUMENT_FORMAT_VERSION + 1
        with self.assertRaises(ValueError):
            Document.from_dict(raw)

    def test_unknown_block_type_raises(self) -> None:
        raw = {
            "version": DOCUMENT_FORMAT_VERSION,
            "blocks": [{"id": "x", "type": "not_a_real_type", "data": {}}],
        }
        with self.assertRaises(ValueError):
            Document.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
