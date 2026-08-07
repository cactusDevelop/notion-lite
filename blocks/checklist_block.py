"""
Bloc Checklist.

Chaque élément de la checklist possède un texte et un état
coché/décoché. L'ordre des éléments dans la liste est significatif.
"""
from __future__ import annotations

import uuid
from typing import Any

from core.block import Block

CHECKLIST_BLOCK_TYPE = "checklist"


class ChecklistBlock(Block):
    """Bloc de liste à cocher.

    Les données du bloc contiennent une seule clé "items" : une
    liste de dictionnaires {"text": str, "checked": bool}.
    """

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=CHECKLIST_BLOCK_TYPE,
            data={"items": items if items is not None else []},
            id=id or str(uuid.uuid4()),
        )

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data.setdefault("items", [])

    def add_item(self, text: str = "", checked: bool = False) -> None:
        self.items.append({"text": text, "checked": checked})

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self.items):
            del self.items[index]

    def set_item_text(self, index: int, text: str) -> None:
        self.items[index]["text"] = text

    def set_item_checked(self, index: int, checked: bool) -> None:
        self.items[index]["checked"] = checked
