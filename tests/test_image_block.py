"""
PATCH 12 — Vérifie la sérialisation/reconstruction du bloc Image et
sa compatibilité avec la sauvegarde/chargement du document (PATCH 8/9).
"""
from __future__ import annotations

import base64
import unittest

from blocks.image_block import ImageBlock
from blocks.registry import block_from_dict
from core.document import Document

# 1x1 PNG rouge valide, minimal.
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class ImageBlockTests(unittest.TestCase):
    def test_default_width_is_none(self) -> None:
        block = ImageBlock(image_base64=_TINY_PNG_B64, image_format="png")
        self.assertIsNone(block.width)

    def test_width_setter(self) -> None:
        block = ImageBlock(image_base64=_TINY_PNG_B64, image_format="png")
        block.width = 320
        self.assertEqual(block.width, 320)
        self.assertEqual(block.data["width"], 320)

    def test_registry_reconstructs_image_block(self) -> None:
        raw = {
            "id": "abc",
            "type": "image",
            "data": {"image_base64": _TINY_PNG_B64, "format": "png", "width": 200},
        }
        block = block_from_dict(raw)
        self.assertIsInstance(block, ImageBlock)
        self.assertEqual(block.id, "abc")
        self.assertEqual(block.image_base64, _TINY_PNG_B64)
        self.assertEqual(block.width, 200)

    def test_document_roundtrip_preserves_image_data(self) -> None:
        document = Document()
        image = ImageBlock(image_base64=_TINY_PNG_B64, image_format="png", width=150)
        document.add_block(image)

        restored = Document.from_dict(document.to_dict())

        self.assertEqual(len(restored), 1)
        restored_image = restored.blocks[0]
        self.assertIsInstance(restored_image, ImageBlock)
        self.assertEqual(restored_image.image_base64, _TINY_PNG_B64)
        self.assertEqual(restored_image.width, 150)
        self.assertEqual(restored_image.image_format, "png")

    def test_base64_payload_decodes_to_bytes(self) -> None:
        block = ImageBlock(image_base64=_TINY_PNG_B64, image_format="png")
        raw_bytes = base64.b64decode(block.image_base64)
        self.assertTrue(raw_bytes.startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()
