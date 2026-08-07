"""
Registre de reconstruction des blocs (PATCH 8 / PATCH 9).

Fait le lien entre le type stocké dans le JSON et la classe de bloc
concrète à instancier. Chaque nouveau type de bloc (checklist, image,
tableau, ...) devra enregistrer sa propre reconstruction ici.
"""
from __future__ import annotations

from typing import Any

from blocks.heading_block import HEADING_TYPES, HeadingBlock
from blocks.text_block import TEXT_BLOCK_TYPE, TextBlock
from core.block import Block

_LEVEL_BY_TYPE = {value: key for key, value in HEADING_TYPES.items()}


def block_from_dict(raw: dict[str, Any]) -> Block:
    """Reconstruit un bloc concret à partir de son dictionnaire JSON.

    Raises:
        ValueError: si le type de bloc n'est pas reconnu.
    """
    block_type = raw["type"]
    data = raw.get("data", {})
    block_id = raw["id"]

    if block_type == TEXT_BLOCK_TYPE:
        return TextBlock(
            content=data.get("content", ""),
            html=data.get("html", ""),
            id=block_id,
        )

    if block_type in _LEVEL_BY_TYPE:
        return HeadingBlock(
            level=_LEVEL_BY_TYPE[block_type],
            content=data.get("content", ""),
            id=block_id,
        )

    raise ValueError(f"Type de bloc inconnu dans le fichier : {block_type!r}")
