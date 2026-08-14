"""
Métadonnées système d'un projet (PATCH 82).

Avant ce patch, le "nom du projet" affiché (titre de fenêtre, projets
récents) n'était jamais que le nom du fichier .json sur disque : le
renommer, le déplacer ou le dupliquer changeait donc silencieusement
l'identité du projet aux yeux de l'application.

Ce module introduit un petit fichier système séparé,
".methodo-project.json", posé à côté du fichier .json dans le dossier
du projet. Il porte le nom "métier" du projet (et sa date de création,
son identifiant stable) indépendamment du nom de fichier utilisé pour
le stockage : renommer le fichier .json, ou le dossier qui le contient,
ne change plus le nom du projet.

Ce fichier commence par un point : les explorateurs (dont celui de
Méthodo OG, PATCH 81, basé sur QFileSystemModel) le masquent par
défaut, comme le ferait un ".git" ou un ".vscode".
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

META_FORMAT_VERSION = 1
META_FILENAME = ".methodo-project.json"


def meta_path_for(document_path: Path) -> Path:
    """Chemin du fichier système de métadonnées associé au projet
    contenant `document_path` (un seul projet = un seul dossier, PATCH
    66) : toujours ".methodo-project.json" dans ce même dossier, quel
    que soit le nom du fichier .json lui-même."""
    return document_path.parent / META_FILENAME


@dataclass
class ProjectMeta:
    """Informations "système" d'un projet, séparées du contenu du
    document (blocs, personnes) et du nom de son fichier de stockage."""

    id: str
    name: str
    created_at: str

    @classmethod
    def create(cls, name: str) -> "ProjectMeta":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": META_FORMAT_VERSION,
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProjectMeta":
        return cls(
            id=raw.get("id") or str(uuid.uuid4()),
            name=raw.get("name", ""),
            created_at=raw.get("created_at", ""),
        )

    # -- Persistance --------------------------------------------------

    def save(self, document_path: Path) -> None:
        meta_path_for(document_path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, document_path: Path) -> Optional["ProjectMeta"]:
        """Charge les métadonnées existantes du projet, ou None si le
        fichier système est absent ou illisible (projet créé avant ce
        patch, fichier corrompu...)."""
        path = meta_path_for(document_path)
        if not path.exists():
            return None
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return None

    @classmethod
    def load_or_create(cls, document_path: Path, default_name: str | None = None) -> "ProjectMeta":
        """Charge les métadonnées si elles existent déjà, sinon en crée
        et persiste de nouvelles à partir d'un nom par défaut
        (rétrocompatibilité avec les projets créés avant ce patch, qui
        n'ont pas encore de fichier système : ils en reçoivent un dès
        leur prochaine ouverture, avec leur nom de fichier actuel comme
        nom de projet initial)."""
        existing = cls.load(document_path)
        if existing is not None:
            return existing
        meta = cls.create(default_name or document_path.stem)
        meta.save(document_path)
        return meta

    def rename(self, document_path: Path, new_name: str) -> None:
        """Renomme le projet (nom "métier" uniquement) sans toucher au
        fichier .json ni à son emplacement."""
        self.name = new_name
        self.save(document_path)
