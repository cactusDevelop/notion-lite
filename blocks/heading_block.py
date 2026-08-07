"""
Blocs Titre (Heading).

Variantes du bloc texte pour les titres H1, H2 et H3.
"""
from __future__ import annotations

import uuid

from core.block import Block

HEADING_TYPES = {1: "heading1", 2: "heading2", 3: "heading3"}


class HeadingBlock(Block):
    """Bloc de titre (H1, H2 ou H3).

    Le niveau (1, 2 ou 3) détermine le type de bloc et sa taille
    d'affichage. Le contenu reste éditable comme un bloc texte.
    """

    def __init__(self, level: int = 1, content: str = "", id: str | None = None) -> None:
        if level not in HEADING_TYPES:
            raise ValueError("Le niveau de titre doit être 1, 2 ou 3.")
        super().__init__(
            type=HEADING_TYPES[level],
            data={"content": content, "level": level},
            id=id or str(uuid.uuid4()),
        )

    @property
    def level(self) -> int:
        return self.data.get("level", 1)

    @property
    def content(self) -> str:
        return self.data.get("content", "")

    @content.setter
    def content(self, value: str) -> None:
        self.data["content"] = value
