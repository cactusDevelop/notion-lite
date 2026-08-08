"""
Bloc Séparateur (PATCH 20).

Ligne horizontale purement visuelle, sans contenu ni interaction :
elle sert uniquement à structurer visuellement le document.
"""
from __future__ import annotations

import uuid

from core.block import Block

SEPARATOR_BLOCK_TYPE = "separator"


class SeparatorBlock(Block):
    """Bloc séparateur : aucune donnée, juste un marqueur de type."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__(type=SEPARATOR_BLOCK_TYPE, data={}, id=id or str(uuid.uuid4()))
