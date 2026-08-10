"""
Bloc "Graphique en bâtonnets" (PATCH 47).

Barres libres (catégorie + valeur), utilisées par exemple pour le
graphique "Delta de budget" du template — dont le contenu exact sera
défini plus tard, d'où des valeurs arbitraires par défaut.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from core.block import Block

BAR_CHART_BLOCK_TYPE = "bar_chart"


class BarChartBlock(Block):
    """Bloc graphique en bâtonnets.

    Données (data) :
        title: titre affiché au-dessus du graphique.
        y_axis_label: libellé de l'axe des ordonnées (ex : "Prix").
        bars: liste de {id, label, value, color}.
    """

    def __init__(
        self,
        title: str = "Graphique",
        y_axis_label: str = "",
        bars: list[dict[str, Any]] | None = None,
        id: str | None = None,
    ) -> None:
        normalized_bars: list[dict[str, Any]] = []
        for bar in bars or []:
            normalized_bars.append({**bar, "id": bar.get("id") or str(uuid.uuid4())})
        super().__init__(
            type=BAR_CHART_BLOCK_TYPE,
            data={"title": title, "y_axis_label": y_axis_label, "bars": normalized_bars},
            id=id or str(uuid.uuid4()),
        )

    @property
    def title(self) -> str:
        return self.data.get("title", "")

    @title.setter
    def title(self, value: str) -> None:
        self.data["title"] = value

    @property
    def y_axis_label(self) -> str:
        return self.data.get("y_axis_label", "")

    @y_axis_label.setter
    def y_axis_label(self, value: str) -> None:
        self.data["y_axis_label"] = value

    @property
    def bars(self) -> list[dict[str, Any]]:
        return self.data.setdefault("bars", [])

    def _find_bar(self, bar_id: str) -> Optional[dict[str, Any]]:
        for bar in self.bars:
            if bar["id"] == bar_id:
                return bar
        return None

    def add_bar(self, label: str = "", value: float = 0.0, color: str = "#7986cb") -> dict[str, Any]:
        bar = {"id": str(uuid.uuid4()), "label": label, "value": float(value), "color": color}
        self.bars.append(bar)
        return bar

    def remove_bar(self, bar_id: str) -> bool:
        bar = self._find_bar(bar_id)
        if bar is None:
            return False
        self.bars.remove(bar)
        return True

    def set_bar_label(self, bar_id: str, label: str) -> bool:
        bar = self._find_bar(bar_id)
        if bar is None:
            return False
        bar["label"] = label
        return True

    def set_bar_value(self, bar_id: str, value: float) -> bool:
        bar = self._find_bar(bar_id)
        if bar is None:
            return False
        bar["value"] = float(value)
        return True
