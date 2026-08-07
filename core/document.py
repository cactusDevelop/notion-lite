"""
Gestionnaire de document.

Le Document est l'unique source de vérité : il contient la liste
ordonnée des blocs et expose les opérations de base (ajout,
suppression, déplacement, recherche par ID).
"""
from __future__ import annotations

from typing import Any, Optional

from core.block import Block

DOCUMENT_FORMAT_VERSION = 1


class Document:
    """Représente un document composé d'une liste ordonnée de blocs."""

    def __init__(self) -> None:
        self._blocks: list[Block] = []

    @property
    def blocks(self) -> list[Block]:
        """Retourne la liste ordonnée des blocs (copie superficielle)."""
        return list(self._blocks)

    def add_block(self, block: Block, index: Optional[int] = None) -> None:
        """Ajoute un bloc au document.

        Args:
            block: Le bloc à ajouter.
            index: Position d'insertion. Si None, ajoute à la fin.
        """
        if index is None:
            self._blocks.append(block)
        else:
            self._blocks.insert(index, block)

    def remove_block(self, block_id: str) -> bool:
        """Supprime un bloc par son ID.

        Returns:
            True si un bloc a été supprimé, False s'il n'a pas été trouvé.
        """
        block = self.find_block(block_id)
        if block is None:
            return False
        self._blocks.remove(block)
        return True

    def move_block(self, block_id: str, new_index: int) -> bool:
        """Déplace un bloc vers une nouvelle position.

        Returns:
            True si le déplacement a réussi, False si le bloc est introuvable.
        """
        block = self.find_block(block_id)
        if block is None:
            return False
        self._blocks.remove(block)
        new_index = max(0, min(new_index, len(self._blocks)))
        self._blocks.insert(new_index, block)
        return True

    def find_block(self, block_id: str) -> Optional[Block]:
        """Recherche un bloc par son ID.

        Returns:
            Le bloc correspondant, ou None si aucun bloc ne correspond.
        """
        for block in self._blocks:
            if block.id == block_id:
                return block
        return None

    def __len__(self) -> int:
        return len(self._blocks)

    # -- Sauvegarde / chargement JSON (PATCH 8) ---------------------------

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le document entier (format de sauvegarde JSON)."""
        return {
            "version": DOCUMENT_FORMAT_VERSION,
            "blocks": [block.to_dict() for block in self._blocks],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Document":
        """Reconstruit un document complet à partir d'un dictionnaire JSON."""
        # Import local pour éviter un import circulaire (blocks -> core.block).
        from blocks.registry import block_from_dict

        document = cls()
        for raw_block in raw.get("blocks", []):
            document.add_block(block_from_dict(raw_block))
        return document
