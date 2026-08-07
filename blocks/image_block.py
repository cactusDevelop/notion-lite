"""
Bloc Image.

L'image est stockée encodée en base64 directement dans les données
du bloc, afin d'être incluse telle quelle dans la sauvegarde JSON
(PATCH 8/9) sans fichier annexe à gérer séparément.
"""
from __future__ import annotations

import uuid
from typing import Optional

from core.block import Block

IMAGE_BLOCK_TYPE = "image"


class ImageBlock(Block):
    """Bloc contenant une image redimensionnable.

    Données (data) :
        image_base64: contenu binaire de l'image, encodé en base64.
        format: extension/format d'origine (png, jpg, ...).
        width: largeur d'affichage en pixels (None = taille native).
    """

    def __init__(
        self,
        image_base64: str = "",
        image_format: str = "png",
        width: Optional[int] = None,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=IMAGE_BLOCK_TYPE,
            data={
                "image_base64": image_base64,
                "format": image_format,
                "width": width,
            },
            id=id or str(uuid.uuid4()),
        )

    @property
    def image_base64(self) -> str:
        return self.data.get("image_base64", "")

    @property
    def image_format(self) -> str:
        return self.data.get("format", "png")

    @property
    def width(self) -> Optional[int]:
        return self.data.get("width")

    @width.setter
    def width(self, value: Optional[int]) -> None:
        self.data["width"] = value
