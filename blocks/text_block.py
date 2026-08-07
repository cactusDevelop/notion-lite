"""
Bloc Texte.

Premier type de bloc concret. Sert de base au reste du projet
(les titres du PATCH 4 en seront des variantes).

Depuis le PATCH 6, le contenu est aussi conservé au format HTML
afin de préserver la mise en forme (gras, italique, listes, etc.).
"""
from __future__ import annotations

import uuid

from core.block import Block

TEXT_BLOCK_TYPE = "text"


class TextBlock(Block):
    """Bloc de texte libre.

    Attributes (dans data):
        content: texte brut (sans mise en forme), utile pour la
            recherche (PATCH 28) et comme donnée de secours.
        html: représentation HTML complète du contenu, avec mise
            en forme (PATCH 6).
    """

    def __init__(self, content: str = "", html: str = "", id: str | None = None) -> None:
        super().__init__(
            type=TEXT_BLOCK_TYPE,
            data={"content": content, "html": html},
            id=id or str(uuid.uuid4()),
        )

    @property
    def content(self) -> str:
        return self.data.get("content", "")

    @content.setter
    def content(self, value: str) -> None:
        self.data["content"] = value

    @property
    def html(self) -> str:
        return self.data.get("html", "")

    @html.setter
    def html(self, value: str) -> None:
        self.data["html"] = value
