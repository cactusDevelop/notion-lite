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
        # Rétrocompatibilité : les checklists sauvegardées avant ce
        # correctif n'ont pas d'"id" par élément ; on leur en génère un.
        normalized_items: list[dict[str, Any]] = []
        for item in items or []:
            normalized_items.append({**item, "id": item.get("id") or str(uuid.uuid4())})

        super().__init__(
            type=CHECKLIST_BLOCK_TYPE,
            data={"items": normalized_items},
            id=id or str(uuid.uuid4()),
        )

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data.setdefault("items", [])

    def _find_item(self, item_id: str) -> dict[str, Any] | None:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def add_item(self, text: str = "", checked: bool = False) -> dict[str, Any]:
        """Ajoute un élément et le retourne (avec son id généré)."""
        item = {"id": str(uuid.uuid4()), "text": text, "checked": checked}
        self.items.append(item)
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

    def set_item_checked(self, item_id: str, checked: bool) -> bool:
        item = self._find_item(item_id)
        if item is None:
            return False
        item["checked"] = checked
        return True

    def sort_by_status(self) -> None:
        """Trie la liste : tâches non cochées d'abord, cochées ensuite (PATCH 11).

        Tri stable : l'ordre relatif à l'intérieur de chaque groupe
        (non coché / coché) est conservé.
        """
        self.data["items"] = sorted(
            self.items, key=lambda item: bool(item.get("checked", False))
        )
