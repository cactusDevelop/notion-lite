"""
Bloc Liste (PATCH 23) : liste à puces ou numérotée.

Chaque élément possède un texte ; l'ordre est significatif. Le style
("bullet" ou "numbered") est une propriété du bloc entier, modifiable
à tout moment sans perdre les éléments.
"""
from __future__ import annotations

import uuid
from typing import Any

from core.block import Block

LIST_BLOCK_TYPE = "list"

LIST_TYPE_BULLET = "bullet"
LIST_TYPE_NUMBERED = "numbered"
LIST_TYPES = [LIST_TYPE_BULLET, LIST_TYPE_NUMBERED]


class ListBlock(Block):
    """Bloc de liste (à puces ou numérotée).

    Données (data) :
        list_type: "bullet" ou "numbered".
        items: liste de {"id": str, "text": str}, ordre significatif.
    """

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        list_type: str = LIST_TYPE_BULLET,
        id: str | None = None,
    ) -> None:
        normalized_items: list[dict[str, Any]] = [
            {"id": item.get("id") or str(uuid.uuid4()), "text": item.get("text", "")}
            for item in items or []
        ]
        super().__init__(
            type=LIST_BLOCK_TYPE,
            data={
                "list_type": list_type if list_type in LIST_TYPES else LIST_TYPE_BULLET,
                "items": normalized_items,
            },
            id=id or str(uuid.uuid4()),
        )

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data.setdefault("items", [])

    @property
    def list_type(self) -> str:
        return self.data.get("list_type", LIST_TYPE_BULLET)

    def set_list_type(self, list_type: str) -> bool:
        if list_type not in LIST_TYPES:
            return False
        self.data["list_type"] = list_type
        return True

    def _find_item(self, item_id: str) -> dict[str, Any] | None:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def add_item(self, text: str = "", index: int | None = None) -> dict[str, Any]:
        """Ajoute un élément (à la fin, ou à `index` si fourni) et le retourne."""
        item = {"id": str(uuid.uuid4()), "text": text}
        if index is None:
            self.items.append(item)
        else:
            self.items.insert(index, item)
        return item

    def remove_item(self, item_id: str) -> bool:
        item = self._find_item(item_id)
        if item is None:
            return False
        self.items.remove(item)
        return True

    def set_item_text(self, item_id: str, text: str) -> bool:
        item = self._find_item(item_id)
        if item is None:
            return False
        item["text"] = text
        return True

    def move_item(self, item_id: str, new_index: int) -> bool:
        item = self._find_item(item_id)
        if item is None:
            return False
        self.items.remove(item)
        new_index = max(0, min(new_index, len(self.items)))
        self.items.insert(new_index, item)
        return True
