"""
Bloc Texte.

Premier type de bloc concret. Sert de base au reste du projet
(les titres du PATCH 4 en seront des variantes).
"""
from __future__ import annotations

import uuid

from core.block import Block

TEXT_BLOCK_TYPE = "text"


class TextBlock(Block):
    """Bloc de texte libre.

    Les données du bloc contiennent une seule clé "content"
    représentant le texte brut du bloc (avec retours à la ligne).
    """

    def __init__(self, content: str = "", id: str | None = None) -> None:
        super().__init__(
            type=TEXT_BLOCK_TYPE,
            data={"content": content},
            id=id or str(uuid.uuid4()),
        )

    @property
    def content(self) -> str:
        return self.data.get("content", "")

    @content.setter
    def content(self, value: str) -> None:
        self.data["content"] = value
