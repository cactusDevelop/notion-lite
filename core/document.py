"""
Gestionnaire de document.

Le Document est l'unique source de vérité : il contient la liste
ordonnée des blocs et expose les opérations de base (ajout,
suppression, déplacement, recherche par ID).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from core.block import Block
from core.people_registry import PERSON_COLOR_PALETTE, PeopleRegistry

DOCUMENT_FORMAT_VERSION = 1

# Ré-exporté pour compatibilité (le registre partagé, core.people_registry,
# est désormais la source de vérité de la palette — PATCH 82).
__all__ = ["Document", "DOCUMENT_FORMAT_VERSION", "PERSON_COLOR_PALETTE"]


class Document:
    """Représente un document composé d'une liste ordonnée de blocs.

    Depuis le PATCH 82, le nom et la couleur des personnes ne sont
    plus stockés dans le document lui-même mais dans un registre
    système partagé, réutilisable d'un projet à l'autre (voir
    `core.people_registry.PeopleRegistry`). Le document ne conserve que
    la liste des identifiants de personnes qu'il référence : c'est ce
    qui permet à une même personne de garder le même nom et la même
    couleur dans tous les projets, et à un projet de "détacher" une
    personne sans la supprimer ailleurs.
    """

    def __init__(self, people_registry: PeopleRegistry | None = None) -> None:
        self._blocks: list[Block] = []
        self._people_registry = people_registry or PeopleRegistry()
        self._person_ids: list[str] = []
        self._favorite_ids: list[str] = []
        # PATCH 83 — Abonnés notifiés à chaque changement du registre de
        # personnes DE CE PROJET (ajout/retrait/renommage/couleur), pour
        # que toutes les vues affichant les personnes (bloc "Effectif",
        # popup "Personne" des tableaux...) restent synchronisées entre
        # elles sans nécessiter un re-rendu complet du document.
        self._people_listeners: list[Callable[[], None]] = []

    @property
    def people_registry(self) -> PeopleRegistry:
        """Le registre système partagé utilisé par ce document."""
        return self._people_registry

    def add_people_listener(self, callback: Callable[[], None]) -> None:
        """S'abonne aux changements de la liste des personnes de ce
        projet. `callback` est appelé (sans argument) après chaque
        ajout, retrait, renommage ou changement de couleur."""
        self._people_listeners.append(callback)

    def remove_people_listener(self, callback: Callable[[], None]) -> None:
        """Se désabonne (à appeler quand la vue est détruite, sinon la
        liste d'abonnés grandirait indéfiniment au fil des re-rendus)."""
        if callback in self._people_listeners:
            self._people_listeners.remove(callback)

    def _notify_people_changed(self) -> None:
        for callback in list(self._people_listeners):
            callback()

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

    # -- Registre des personnes (PATCH 16, revu PATCH 82) -----------------
    #
    # Le nom et la couleur vivent dans le registre système partagé
    # (self._people_registry) ; le document ne garde que les ids des
    # personnes qui font partie de CE projet (self._person_ids), pour
    # savoir lesquelles afficher dans le bloc "Effectif" et proposer
    # dans les colonnes "Personne" des tableaux.

    @property
    def people(self) -> list[dict[str, Any]]:
        """Personnes de ce projet (nom/couleur résolus depuis le
        registre système partagé). Une personne dont l'id n'existerait
        plus dans le registre (supprimée ailleurs) est simplement
        omise, plutôt que de faire planter l'affichage."""
        people = []
        for person_id in self._person_ids:
            person = self._people_registry.find_person(person_id)
            if person is not None:
                people.append(person)
        return people

    def find_person(self, person_id: str) -> Optional[dict[str, Any]]:
        """Une personne, mais seulement si elle fait partie de ce projet."""
        if person_id not in self._person_ids:
            return None
        return self._people_registry.find_person(person_id)

    def add_person(self, name: str, color: str | None = None) -> dict[str, Any]:
        """Ajoute (ou réutilise, si elle existe déjà sous ce nom dans le
        registre partagé) une personne, et l'associe à ce projet."""
        person = self._people_registry.add_person(name, color)
        if person["id"] not in self._person_ids:
            self._person_ids.append(person["id"])
        self._notify_people_changed()
        return person

    def link_person(self, person_id: str) -> bool:
        """Associe à ce projet une personne déjà connue du registre
        partagé (typiquement créée depuis un autre projet). Retourne
        False si cet id est inconnu du registre."""
        if self._people_registry.find_person(person_id) is None:
            return False
        if person_id not in self._person_ids:
            self._person_ids.append(person_id)
        self._notify_people_changed()
        return True

    def rename_person(self, person_id: str, name: str) -> bool:
        if person_id not in self._person_ids:
            return False
        renamed = self._people_registry.rename_person(person_id, name)
        if renamed:
            self._notify_people_changed()
        return renamed

    def set_person_color(self, person_id: str, color: str) -> bool:
        if person_id not in self._person_ids:
            return False
        changed = self._people_registry.set_person_color(person_id, color)
        if changed:
            self._notify_people_changed()
        return changed

    def remove_person(self, person_id: str) -> bool:
        """Détache une personne de CE projet et purge ses références
        dans les colonnes "Personne" des blocs Tableau du document.

        Contrairement à l'ancien comportement (PATCH 16), ceci ne
        supprime PAS la personne du registre partagé : elle reste
        disponible pour les autres projets. Pour la supprimer
        définitivement partout, voir `self.people_registry.remove_person`.
        """
        if person_id not in self._person_ids:
            return False
        self._person_ids.remove(person_id)

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
        self._notify_people_changed()
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
        """Sérialise le document entier (format de sauvegarde JSON).

        Depuis le PATCH 82, seuls les identifiants des personnes de ce
        projet sont sauvegardés ("person_ids") : leur nom et leur
        couleur vivent dans le registre système partagé, pas dans ce
        fichier (voir `core.people_registry`).
        """
        return {
            "version": DOCUMENT_FORMAT_VERSION,
            "blocks": [block.to_dict() for block in self._blocks],
            "person_ids": list(self._person_ids),
            "favorite_ids": list(self._favorite_ids),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any], people_registry: PeopleRegistry | None = None) -> "Document":
        """Reconstruit un document complet à partir d'un dictionnaire JSON.

        Toutes les données de chaque bloc (id, type, contenu complet)
        sont restaurées à l'identique (PATCH 9).

        Args:
            raw: Le document sérialisé (voir `to_dict`).
            people_registry: Registre système à utiliser. Par défaut,
                celui de l'utilisateur courant (voir
                `core.people_registry.default_registry_path`).

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

        document = cls(people_registry=people_registry)
        for raw_block in raw["blocks"]:
            document.add_block(block_from_dict(raw_block))

        # PATCH 82 — Rétrocompatibilité : les fichiers créés avant ce
        # patch embarquent encore une liste "people" complète (id, nom,
        # couleur). On la migre dans le registre partagé, en évitant
        # les doublons si une personne du même nom y existe déjà.
        for raw_person in raw.get("people", []):
            name = raw_person.get("name", "")
            existing = document._people_registry.find_person(raw_person.get("id", ""))
            if existing is not None:
                person_id = existing["id"]
            else:
                migrated = document._people_registry.add_person(
                    name, raw_person.get("color")
                )
                person_id = migrated["id"]
            if person_id not in document._person_ids:
                document._person_ids.append(person_id)

        # Format courant : uniquement des ids, résolus dans le registre.
        for person_id in raw.get("person_ids", []):
            if document._people_registry.find_person(person_id) is not None:
                if person_id not in document._person_ids:
                    document._person_ids.append(person_id)

        # Ne conserve que les ids référençant un bloc effectivement chargé
        # (robustesse face à un fichier corrompu ou édité à la main).
        existing_ids = {block.id for block in document._blocks}
        document._favorite_ids = [
            fid for fid in raw.get("favorite_ids", []) if fid in existing_ids
        ]
        return document
