"""
Registre système des personnes (PATCH 82).

Avant ce patch, chaque document stockait sa propre copie complète des
personnes (id, nom, couleur) dans son JSON. Deux projets différents ne
partageaient donc rien : ajouter "Alice" dans un projet ne la rendait
pas disponible dans un autre, et une même personne pouvait finir avec
des couleurs différentes d'un fichier à l'autre — la source de la
"gestion très buggée" des personnes.

Ce module introduit un fichier système unique par utilisateur
(~/.methodo-og/people.json par défaut, indépendant de tout projet)
qui devient la seule source de vérité pour le nom et la couleur d'une
personne. Un `Document` ne conserve plus que la liste des identifiants
de personnes qu'il référence (voir `core.document.Document`), et
délègue toute lecture/écriture de nom/couleur à ce registre partagé.

Ajouter une personne depuis n'importe quel projet la rend donc
immédiatement disponible dans tous les autres.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Optional

REGISTRY_FORMAT_VERSION = 1

# Variable d'environnement permettant de surcharger l'emplacement du
# registre (tests automatisés, installations portables/multi-poste).
_ENV_OVERRIDE = "METHODO_OG_PEOPLE_FILE"

# Palette assignée automatiquement (par rotation) aux nouvelles personnes.
PERSON_COLOR_PALETTE: list[str] = [
    "#e57373", "#64b5f6", "#81c784", "#ffd54f",
    "#ba68c8", "#4db6ac", "#f06292", "#a1887f",
]


def default_registry_path() -> Path:
    """Emplacement système par défaut du registre partagé des personnes.

    Surchargeable via la variable d'environnement METHODO_OG_PEOPLE_FILE
    (utilisé notamment par les tests, pour ne jamais toucher au vrai
    fichier de l'utilisateur qui exécute la suite).
    """
    override = os.environ.get(_ENV_OVERRIDE)
    if override:
        return Path(override)
    return Path.home() / ".methodo-og" / "people.json"


class PeopleRegistry:
    """Registre des personnes connues, persisté dans un unique fichier
    JSON système, partagé par tous les projets Méthodo OG de l'utilisateur.
    """

    def __init__(self, path: Path | None = None, *, autoload: bool = True) -> None:
        self.path = path or default_registry_path()
        self._people: list[dict[str, Any]] = []
        if autoload:
            self.load()

    # -- Persistance --------------------------------------------------

    def load(self) -> None:
        """(Re)charge le registre depuis le disque. Silencieux si le
        fichier n'existe pas encore (première utilisation) ou est
        corrompu (on repart alors d'un registre vide plutôt que de
        planter au démarrage)."""
        if not self.path.exists():
            self._people = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._people = []
            return
        self._people = [
            {
                "id": person.get("id") or str(uuid.uuid4()),
                "name": person.get("name", ""),
                "color": person.get("color") or PERSON_COLOR_PALETTE[0],
            }
            for person in raw.get("people", [])
        ]

    def save(self) -> None:
        """Écrit le registre sur disque, en créant le dossier système
        (~/.methodo-og par défaut) si besoin."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": REGISTRY_FORMAT_VERSION, "people": self._people}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # -- Lecture ----------------------------------------------------------

    @property
    def people(self) -> list[dict[str, Any]]:
        """Toutes les personnes connues, tous projets confondus."""
        return list(self._people)

    def find_person(self, person_id: str) -> Optional[dict[str, Any]]:
        for person in self._people:
            if person["id"] == person_id:
                return person
        return None

    def find_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """Recherche insensible à la casse/espaces, pour éviter que
        deux projets créent chacun un doublon "Alice" / "alice " par
        simple étourderie."""
        needle = name.strip().casefold()
        for person in self._people:
            if person["name"].strip().casefold() == needle:
                return person
        return None

    # -- Écriture -----------------------------------------------------

    def add_person(self, name: str, color: str | None = None) -> dict[str, Any]:
        """Ajoute une personne, ou retourne celle qui existe déjà sous
        ce nom (le registre est global : pas de doublon involontaire
        entre deux projets)."""
        existing = self.find_by_name(name)
        if existing is not None:
            return existing
        if color is None:
            color = PERSON_COLOR_PALETTE[len(self._people) % len(PERSON_COLOR_PALETTE)]
        person = {"id": str(uuid.uuid4()), "name": name, "color": color}
        self._people.append(person)
        self.save()
        return person

    def rename_person(self, person_id: str, name: str) -> bool:
        person = self.find_person(person_id)
        if person is None:
            return False
        person["name"] = name
        self.save()
        return True

    def set_person_color(self, person_id: str, color: str) -> bool:
        person = self.find_person(person_id)
        if person is None:
            return False
        person["color"] = color
        self.save()
        return True

    def remove_person(self, person_id: str) -> bool:
        """Supprime définitivement la personne du registre partagé
        (donc de tous les projets qui la référencent). Voir
        `Document.remove_person` pour le retrait "local" à un seul
        projet, qui ne touche pas au registre."""
        person = self.find_person(person_id)
        if person is None:
            return False
        self._people.remove(person)
        self.save()
        return True
