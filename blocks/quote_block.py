"""
Bloc Citation (PATCH 21).

Variante simple du bloc texte : un unique champ `content`, affiché
avec une mise en forme dédiée (barre verticale, italique) plutôt que
stocké en HTML riche comme TextBlock.
"""
from __future__ import annotations

import uuid

from core.block import Block

QUOTE_BLOCK_TYPE = "quote"


class QuoteBlock(Block):
    """Bloc citation : texte libre affiché avec une mise en forme dédiée."""

    def __init__(self, content: str = "", id: str | None = None) -> None:
        super().__init__(
            type=QUOTE_BLOCK_TYPE,
            data={"content": content},
            id=id or str(uuid.uuid4()),
        )

    @property
    def content(self) -> str:
        return self.data.get("content", "")

    @content.setter
    def content(self, value: str) -> None:
        self.data["content"] = value
