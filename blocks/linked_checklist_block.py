"""
Bloc "Checklists liées" (PATCH 44).

Deux checklists côte à côte séparées par un séparateur ajustable :
à gauche les éléments non cochés ("à faire"), à droite les éléments
cochés ("faites"). Cocher un élément le fait basculer du panneau
gauche vers le panneau droit ; le décocher le fait revenir à gauche.

Contrairement à ChecklistBlock (une seule liste triée), les éléments
sont ici répartis entre deux panneaux visuellement distincts, d'où
un stockage dédié plutôt qu'une réutilisation directe.
"""
from __future__ import annotations

import uuid
from typing import Any

from core.block import Block

LINKED_CHECKLIST_BLOCK_TYPE = "linked_checklist"


class LinkedChecklistBlock(Block):
    """Bloc de deux checklists liées par l'état coché de leurs éléments.

    Données (data) :
        items: liste de {"id": str, "text": str, "checked": bool}.
        split: position (0..1) du séparateur ajustable entre panneaux.
    """

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        split: float = 0.5,
        id: str | None = None,
    ) -> None:
        normalized_items: list[dict[str, Any]] = []
        for item in items or []:
            normalized_items.append({**item, "id": item.get("id") or str(uuid.uuid4())})

        super().__init__(
            type=LINKED_CHECKLIST_BLOCK_TYPE,
            data={"items": normalized_items, "split": split},
            id=id or str(uuid.uuid4()),
        )

    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data.setdefault("items", [])

    @property
    def split(self) -> float:
        return float(self.data.get("split", 0.5))

    @split.setter
    def split(self, value: float) -> None:
        self.data["split"] = max(0.05, min(0.95, value))

    def _find_item(self, item_id: str) -> dict[str, Any] | None:
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None

    def add_item(self, text: str = "", checked: bool = False) -> dict[str, Any]:
        """Ajoute un élément (toujours côté "à faire" par défaut) et le retourne."""
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
        """Coche/décoche un élément (le fait ainsi changer de panneau)."""
        item = self._find_item(item_id)
        if item is None:
            return False
        item["checked"] = checked
        return True

    def todo_items(self) -> list[dict[str, Any]]:
        """Éléments du panneau gauche ("à faire")."""
        return [item for item in self.items if not item.get("checked", False)]

    def done_items(self) -> list[dict[str, Any]]:
        """Éléments du panneau droit ("faites")."""
        return [item for item in self.items if item.get("checked", False)]
