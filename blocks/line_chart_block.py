"""
Bloc "Courbes" (PATCH 47).

Trace une ou plusieurs droites passant par l'origine (y = pente * x)
sur un même repère. Chaque série a sa pente définie soit
manuellement (constante éditable — couvre par exemple "idéal"
y = x avec une pente de 1, ou une "vélocité" arbitraire), soit
calculée automatiquement à partir d'un bloc "Planning par
dépendances" (ratio durée planifiée / (durée planifiée + retard),
voir compute_efficiency_ratio) — ce qui couvre le besoin d'une droite
de "vélocité réelle" recalculée à chaque modification du planning.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from blocks.dependency_gantt_block import DependencyGanttBlock, compute_efficiency_ratio
from core.block import Block

LINE_CHART_BLOCK_TYPE = "line_chart"

SLOPE_MODE_CONSTANT = "constant"
SLOPE_MODE_EFFICIENCY = "efficiency"

_DEFAULT_COLORS = ["#1976d2", "#e53935", "#43a047", "#fb8c00", "#8e24aa"]


class LineChartBlock(Block):
    """Bloc graphique en courbes.

    Données (data) :
        title: titre affiché au-dessus du graphique.
        x_max: borne supérieure de l'axe des abscisses.
        series: liste de {
            id, name, color,
            mode: "constant" | "efficiency",
            slope: pente utilisée si mode == "constant",
            source_block_id: id d'un DependencyGanttBlock utilisé si
                mode == "efficiency" (la pente est alors recalculée à
                chaque lecture, jamais stockée),
        }
    """

    def __init__(
        self,
        title: str = "Efficacité",
        x_max: float = 10.0,
        series: list[dict[str, Any]] | None = None,
        id: str | None = None,
    ) -> None:
        normalized_series: list[dict[str, Any]] = []
        for s in series or []:
            normalized_series.append({**s, "id": s.get("id") or str(uuid.uuid4())})
        super().__init__(
            type=LINE_CHART_BLOCK_TYPE,
            data={"title": title, "x_max": x_max, "series": normalized_series},
            id=id or str(uuid.uuid4()),
        )

    @property
    def title(self) -> str:
        return self.data.get("title", "")

    @title.setter
    def title(self, value: str) -> None:
        self.data["title"] = value

    @property
    def x_max(self) -> float:
        return float(self.data.get("x_max", 10.0))

    @x_max.setter
    def x_max(self, value: float) -> None:
        self.data["x_max"] = max(float(value), 0.01)

    @property
    def series(self) -> list[dict[str, Any]]:
        return self.data.setdefault("series", [])

    def _find_series(self, series_id: str) -> Optional[dict[str, Any]]:
        for s in self.series:
            if s["id"] == series_id:
                return s
        return None

    def add_series(
        self,
        name: str = "Série",
        mode: str = SLOPE_MODE_CONSTANT,
        slope: float = 1.0,
        source_block_id: Optional[str] = None,
        color: Optional[str] = None,
    ) -> dict[str, Any]:
        s = {
            "id": str(uuid.uuid4()),
            "name": name,
            "color": color or _DEFAULT_COLORS[len(self.series) % len(_DEFAULT_COLORS)],
            "mode": mode if mode in (SLOPE_MODE_CONSTANT, SLOPE_MODE_EFFICIENCY) else SLOPE_MODE_CONSTANT,
            "slope": float(slope),
            "source_block_id": source_block_id,
        }
        self.series.append(s)
        return s

    def remove_series(self, series_id: str) -> bool:
        s = self._find_series(series_id)
        if s is None:
            return False
        self.series.remove(s)
        return True

    def set_series_name(self, series_id: str, name: str) -> bool:
        s = self._find_series(series_id)
        if s is None:
            return False
        s["name"] = name
        return True

    def set_series_slope(self, series_id: str, slope: float) -> bool:
        s = self._find_series(series_id)
        if s is None:
            return False
        s["slope"] = float(slope)
        return True

    def set_series_mode(self, series_id: str, mode: str, source_block_id: Optional[str] = None) -> bool:
        s = self._find_series(series_id)
        if s is None or mode not in (SLOPE_MODE_CONSTANT, SLOPE_MODE_EFFICIENCY):
            return False
        s["mode"] = mode
        s["source_block_id"] = source_block_id
        return True


def resolve_series_slope(document, series: dict[str, Any]) -> float:
    """Pente effective d'une série : constante, ou recalculée depuis un
    bloc de planning (0.0 si la source n'est pas/plus valide)."""
    if series["mode"] != SLOPE_MODE_EFFICIENCY:
        return float(series.get("slope", 0.0))
    source = document.find_block(series.get("source_block_id"))
    if not isinstance(source, DependencyGanttBlock):
        return 0.0
    ratio = compute_efficiency_ratio(document, source)
    return ratio if ratio is not None else 0.0


def compute_line_series(document, block: LineChartBlock) -> list[dict[str, Any]]:
    """Retourne, pour chaque série, {id, name, color, slope, x0, y0, x1, y1}
    (segment de droite entre 0 et x_max) prêt à être tracé."""
    x_max = block.x_max
    result = []
    for s in block.series:
        slope = resolve_series_slope(document, s)
        result.append(
            {
                "id": s["id"],
                "name": s["name"],
                "color": s["color"],
                "slope": slope,
                "x0": 0.0,
                "y0": 0.0,
                "x1": x_max,
                "y1": slope * x_max,
            }
        )
    return result
