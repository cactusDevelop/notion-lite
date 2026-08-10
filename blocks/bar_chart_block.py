"""
Bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49).

Barres "Prévu" (bleu) avec, pour chacune, une valeur "Réel"
optionnelle affichée sous forme de marqueur en pointillés (rouge si
le réel dépasse le prévu — dépassement de budget —, vert sinon).
Utilisé par exemple pour le graphique "Delta de budget" du template.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from core.block import Block

BAR_CHART_BLOCK_TYPE = "bar_chart"

PLANNED_BAR_COLOR = "#1976d2"
OVER_BUDGET_COLOR = "#e53935"
UNDER_BUDGET_COLOR = "#43a047"


class BarChartBlock(Block):
    """Bloc graphique en bâtonnets.

    Données (data) :
        title: titre affiché au-dessus du graphique.
        y_axis_label: libellé de l'axe des ordonnées (ex : "Prix").
        bars: liste de {id, label, value, actual, color}.
            value: montant "Prévu" (barre pleine bleue).
            actual: montant "Réel" (marqueur en pointillés), ou None
                si pas encore renseigné (aucun marqueur affiché).
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
            normalized = {**bar, "id": bar.get("id") or str(uuid.uuid4())}
            normalized.setdefault("actual", None)
            normalized_bars.append(normalized)
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

    def add_bar(
        self,
        label: str = "",
        value: float = 0.0,
        actual: Optional[float] = None,
        color: str = PLANNED_BAR_COLOR,
    ) -> dict[str, Any]:
        bar = {
            "id": str(uuid.uuid4()),
            "label": label,
            "value": float(value),
            "actual": float(actual) if actual is not None else None,
            "color": color,
        }
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

    def set_bar_actual(self, bar_id: str, actual: Optional[float]) -> bool:
        bar = self._find_bar(bar_id)
        if bar is None:
            return False
        bar["actual"] = float(actual) if actual is not None else None
        return True


def budget_marker_color(bar: dict[str, Any]) -> Optional[str]:
    """Couleur du marqueur "Réel" : rouge en dépassement de budget
    (réel > prévu), vert sinon. None si aucun "Réel" renseigné."""
    if bar.get("actual") is None:
        return None
    return OVER_BUDGET_COLOR if bar["actual"] > bar["value"] else UNDER_BUDGET_COLOR