"""
Bloc Code (PATCH 22).

Bloc de texte brut destiné au code : police monospace à l'affichage.
La coloration syntaxique est explicitement une amélioration future
(voir le plan du projet) — ce patch pose la structure de données et
l'affichage monospace uniquement.
"""
from __future__ import annotations

import uuid

from core.block import Block

CODE_BLOCK_TYPE = "code"

# Langage par défaut, informatif seulement (pas encore utilisé pour
# la coloration syntaxique, prévue dans une amélioration future).
DEFAULT_LANGUAGE = "text"


class CodeBlock(Block):
    """Bloc de code : texte brut affiché en police monospace.

    Attributes (dans data):
        content: code brut, sans mise en forme.
        language: étiquette de langage (informative pour l'instant).
    """

    def __init__(self, content: str = "", language: str = DEFAULT_LANGUAGE, id: str | None = None) -> None:
        super().__init__(
            type=CODE_BLOCK_TYPE,
            data={"content": content, "language": language},
            id=id or str(uuid.uuid4()),
        )

    @property
    def content(self) -> str:
        return self.data.get("content", "")

    @content.setter
    def content(self, value: str) -> None:
        self.data["content"] = value

    @property
    def language(self) -> str:
        return self.data.get("language", DEFAULT_LANGUAGE)

    @language.setter
    def language(self, value: str) -> None:
        self.data["language"] = value or DEFAULT_LANGUAGE
