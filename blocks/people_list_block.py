"""
Bloc "Effectif" (PATCH 52).

Contrairement aux autres blocs, ce bloc n'a aucune donnée propre : il
affiche et permet d'éditer directement le registre partagé de
personnes du document (Document.people), le même registre que celui
utilisé par le Gestionnaire de personnes (Édition > Gestionnaire de
personnes) et par les colonnes "Personne" des blocs Tableau. Ajouter
une personne ici, ou depuis le Gestionnaire, les rend donc immédiatement
visibles partout ailleurs : il n'y a qu'une seule source de vérité.
"""
from __future__ import annotations

import uuid

from core.block import Block

PEOPLE_LIST_BLOCK_TYPE = "people_list"


class PeopleListBlock(Block):
    """Bloc sans donnée propre : simple point d'affichage/édition du
    registre partagé Document.people."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__(type=PEOPLE_LIST_BLOCK_TYPE, data={}, id=id or str(uuid.uuid4()))
