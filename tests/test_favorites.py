from __future__ import annotations

from blocks.text_block import TextBlock
from core.document import Document


def _make_document():
    doc = Document()
    b1 = TextBlock(content="Un")
    b2 = TextBlock(content="Deux")
    b3 = TextBlock(content="Trois")
    doc.add_block(b1)
    doc.add_block(b2)
    doc.add_block(b3)
    return doc, b1, b2, b3


def test_add_and_check_favorite():
    doc, b1, _, _ = _make_document()
    assert doc.is_favorite(b1.id) is False
    assert doc.add_favorite(b1.id) is True
    assert doc.is_favorite(b1.id) is True
    assert doc.add_favorite(b1.id) is False  # déjà favori


def test_add_favorite_unknown_block_fails():
    doc, _, _, _ = _make_document()
    assert doc.add_favorite("inconnu") is False


def test_remove_favorite():
    doc, b1, _, _ = _make_document()
    doc.add_favorite(b1.id)
    assert doc.remove_favorite(b1.id) is True
    assert doc.is_favorite(b1.id) is False
    assert doc.remove_favorite(b1.id) is False


def test_toggle_favorite():
    doc, b1, _, _ = _make_document()
    assert doc.toggle_favorite(b1.id) is True
    assert doc.toggle_favorite(b1.id) is False
    assert doc.toggle_favorite("inconnu") is None


def test_favorite_blocks_follows_document_order():
    doc, b1, b2, b3 = _make_document()
    # Ajoutés dans le désordre : b3 puis b1.
    doc.add_favorite(b3.id)
    doc.add_favorite(b1.id)
    assert [b.id for b in doc.favorite_blocks()] == [b1.id, b3.id]


def test_remove_block_purges_favorite():
    doc, b1, _, _ = _make_document()
    doc.add_favorite(b1.id)
    doc.remove_block(b1.id)
    assert doc.is_favorite(b1.id) is False
    assert doc.favorite_ids == []


def test_favorites_roundtrip_via_document_dict():
    doc, b1, b2, _ = _make_document()
    doc.add_favorite(b1.id)
    doc.add_favorite(b2.id)

    rebuilt = Document.from_dict(doc.to_dict())

    assert set(rebuilt.favorite_ids) == {b1.id, b2.id}
    assert rebuilt.is_favorite(b1.id) is True


def test_favorites_roundtrip_drops_unknown_ids():
    doc, b1, _, _ = _make_document()
    raw = doc.to_dict()
    raw["favorite_ids"] = [b1.id, "id-fantome"]

    rebuilt = Document.from_dict(raw)

    assert rebuilt.favorite_ids == [b1.id]
