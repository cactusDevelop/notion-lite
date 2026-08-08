"""
Gestionnaire de document.

Le Document est l'unique source de vérité : il contient la liste
ordonnée des blocs et expose les opérations de base (ajout,
suppression, déplacement, recherche par ID).
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from core.block import Block

DOCUMENT_FORMAT_VERSION = 1

# Palette assignée automatiquement (par rotation) aux nouvelles personnes
# du gestionnaire partagé (PATCH 16).
PERSON_COLOR_PALETTE: list[str] = [
    "#e57373", "#64b5f6", "#81c784", "#ffd54f",
    "#ba68c8", "#4db6ac", "#f06292", "#a1887f",
]


class Document:
    """Représente un document composé d'une liste ordonnée de blocs.

    Depuis le PATCH 16, le document porte aussi le registre partagé des
    personnes (nom + couleur) référencées par les colonnes "Personne"
    des blocs Tableau : une même personne est ainsi cohérente (même
    couleur, renommage propagé) dans tout le document.
    """

    def __init__(self) -> None:
        self._blocks: list[Block] = []
        self._people: list[dict[str, Any]] = []
        self._favorite_ids: list[str] = []

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
        if block_id in self._favorite_ids:
            self._favorite_ids.remove(block_id)
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

    # -- Registre des personnes (PATCH 16) ---------------------------------

    @property
    def people(self) -> list[dict[str, Any]]:
        """Retourne la liste des personnes connues (copie superficielle)."""
        return list(self._people)

    def find_person(self, person_id: str) -> Optional[dict[str, Any]]:
        for person in self._people:
            if person["id"] == person_id:
                return person
        return None

    def add_person(self, name: str, color: str | None = None) -> dict[str, Any]:
        """Ajoute une personne au registre partagé et la retourne."""
        if color is None:
            color = PERSON_COLOR_PALETTE[len(self._people) % len(PERSON_COLOR_PALETTE)]
        person = {"id": str(uuid.uuid4()), "name": name, "color": color}
        self._people.append(person)
        return person

    def rename_person(self, person_id: str, name: str) -> bool:
        person = self.find_person(person_id)
        if person is None:
            return False
        person["name"] = name
        return True

    def set_person_color(self, person_id: str, color: str) -> bool:
        person = self.find_person(person_id)
        if person is None:
            return False
        person["color"] = color
        return True

    def remove_person(self, person_id: str) -> bool:
        """Retire une personne du registre et purge toutes ses références
        dans les colonnes "Personne" des blocs Tableau du document."""
        person = self.find_person(person_id)
        if person is None:
            return False
        self._people.remove(person)

        # Import local pour éviter un import circulaire (blocks -> core).
        from blocks.table_block import COLUMN_TYPE_PERSON
        from blocks.table_block import TableBlock

        for block in self._blocks:
            if not isinstance(block, TableBlock):
                continue
            person_columns = [c for c in block.columns if c["type"] == COLUMN_TYPE_PERSON]
            for column in person_columns:
                for row in block.rows:
                    current = row["cells"].get(column["id"]) or []
                    if person_id in current:
                        block.set_cell(row["id"], column["id"], [p for p in current if p != person_id])
        return True

    # -- Favoris (PATCH 31) ------------------------------------------------

    @property
    def favorite_ids(self) -> list[str]:
        """Ids des blocs favoris, dans leur ordre d'ajout aux favoris."""
        return list(self._favorite_ids)

    def is_favorite(self, block_id: str) -> bool:
        return block_id in self._favorite_ids

    def add_favorite(self, block_id: str) -> bool:
        """Marque un bloc comme favori. False si le bloc n'existe pas
        ou s'il est déjà favori."""
        if self.find_block(block_id) is None or block_id in self._favorite_ids:
            return False
        self._favorite_ids.append(block_id)
        return True

    def remove_favorite(self, block_id: str) -> bool:
        if block_id not in self._favorite_ids:
            return False
        self._favorite_ids.remove(block_id)
        return True

    def toggle_favorite(self, block_id: str) -> Optional[bool]:
        """Bascule l'état favori d'un bloc. Retourne le nouvel état
        (True si désormais favori), ou None si le bloc n'existe pas."""
        if self.find_block(block_id) is None:
            return None
        if self.is_favorite(block_id):
            self.remove_favorite(block_id)
            return False
        self.add_favorite(block_id)
        return True

    def favorite_blocks(self) -> list[Block]:
        """Blocs favoris, dans l'ordre du document (pas l'ordre d'ajout
        aux favoris) — plus utile pour un panneau de navigation."""
        favorites = set(self._favorite_ids)
        return [block for block in self._blocks if block.id in favorites]

    # -- Sauvegarde / chargement JSON (PATCH 8) ---------------------------

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le document entier (format de sauvegarde JSON)."""
        return {
            "version": DOCUMENT_FORMAT_VERSION,
            "blocks": [block.to_dict() for block in self._blocks],
            "people": list(self._people),
            "favorite_ids": list(self._favorite_ids),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Document":
        """Reconstruit un document complet à partir d'un dictionnaire JSON.

        Toutes les données de chaque bloc (id, type, contenu complet)
        sont restaurées à l'identique (PATCH 9).

        Raises:
            ValueError: si le fichier a été sauvegardé par une version
                plus récente du format que celle supportée ici.
        """
        file_version = raw.get("version", DOCUMENT_FORMAT_VERSION)
        if file_version > DOCUMENT_FORMAT_VERSION:
            raise ValueError(
                f"Ce fichier a été créé avec une version plus récente du "
                f"format ({file_version}) que celle supportée ({DOCUMENT_FORMAT_VERSION})."
            )

        # Import local pour éviter un import circulaire (blocks -> core.block).
        from blocks.registry import block_from_dict

        if "blocks" not in raw:
            raise ValueError("Fichier invalide : clé 'blocks' manquante.")

        document = cls()
        for raw_block in raw["blocks"]:
            document.add_block(block_from_dict(raw_block))
        for raw_person in raw.get("people", []):
            document._people.append(
                {
                    "id": raw_person.get("id") or str(uuid.uuid4()),
                    "name": raw_person.get("name", ""),
                    "color": raw_person.get("color", PERSON_COLOR_PALETTE[0]),
                }
            )
        # Ne conserve que les ids référençant un bloc effectivement chargé
        # (robustesse face à un fichier corrompu ou édité à la main).
        existing_ids = {block.id for block in document._blocks}
        document._favorite_ids = [
            fid for fid in raw.get("favorite_ids", []) if fid in existing_ids
        ]
        return document
