"""
Bloc de base du document.

Un bloc représente une unité de contenu (texte, titre, image, etc.).
Cette classe sera spécialisée par les patches suivants
(PATCH 3 : bloc texte, PATCH 4 : titres, etc.).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Block:
    """Représente un bloc générique dans le document.

    Attributes:
        type: Type du bloc (ex: "text", "heading1", ...).
        data: Données propres au bloc (contenu, options, etc.).
        id: Identifiant unique du bloc (UUID en chaîne).
    """
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le bloc en dictionnaire (pour sauvegarde JSON)."""
        return {"id": self.id, "type": self.type, "data": self.data}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Block":
        """Reconstruit un bloc à partir d'un dictionnaire."""
        return cls(type=raw["type"], data=raw.get("data", {}), id=raw["id"])
