"""
Bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49, PATCH 54).

Barres "Prévu" (bleu) avec, pour chacune, une valeur "Réel"
optionnelle affichée sous forme de marqueur en pointillés (rouge si
le réel dépasse le prévu — dépassement de budget —, vert sinon).
Utilisé par exemple pour le graphique "Delta de budget" du template.

PATCH 54 : le graphique peut désormais être relié à un bloc "Planning
par dépendances" (`source_gantt_id`), et regroupé par une colonne
texte de son tableau source (`group_column_id`, ex : "Phases"). Une
fois relié, les barres ne sont plus éditées manuellement : elles sont
recalculées en direct à chaque lecture à partir des durées et des
écarts ("Ecarts") des sous-tâches du planning, groupées par
`group_column_id` (ou par sous-tâche si aucun regroupement choisi) —
même principe de synchronisation, jamais stockée, que la droite
"Vélocité réelle" du bloc Courbes (voir compute_efficiency_ratio).
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
        bars: liste de {id, label, value, actual, color} — ignorée
            (contenu affiché en lecture seule car recalculé, voir
            sync_bars_from_gantt) tant que `source_gantt_id` est défini.
            value: montant "Prévu" (barre pleine bleue).
            actual: montant "Réel" (marqueur en pointillés), ou None
                si pas encore renseigné (aucun marqueur affiché).
        source_gantt_id: id d'un DependencyGanttBlock (PATCH 54). Si
            défini, les barres sont recalculées en direct à partir de
            ses sous-tâches plutôt que lues depuis `bars`.
        group_column_id: id d'une colonne texte du tableau source du
            Gantt relié, utilisée pour regrouper les sous-tâches en
            barres (ex : "Phases"). Si None (mais source_gantt_id
            défini), chaque sous-tâche forme sa propre barre.
    """

    def __init__(
        self,
        title: str = "Graphique",
        y_axis_label: str = "",
        bars: list[dict[str, Any]] | None = None,
        source_gantt_id: Optional[str] = None,
        group_column_id: Optional[str] = None,
        id: str | None = None,
    ) -> None:
        normalized_bars: list[dict[str, Any]] = []
        for bar in bars or []:
            normalized = {**bar, "id": bar.get("id") or str(uuid.uuid4())}
            normalized.setdefault("actual", None)
            normalized_bars.append(normalized)
        super().__init__(
            type=BAR_CHART_BLOCK_TYPE,
            data={
                "title": title,
                "y_axis_label": y_axis_label,
                "bars": normalized_bars,
                "source_gantt_id": source_gantt_id,
                "group_column_id": group_column_id,
            },
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

    @property
    def source_gantt_id(self) -> Optional[str]:
        return self.data.get("source_gantt_id")

    @property
    def group_column_id(self) -> Optional[str]:
        return self.data.get("group_column_id")

    def set_source(self, source_gantt_id: Optional[str], group_column_id: Optional[str] = None) -> None:
        """PATCH 54 — Relie (ou détache si None) ce graphique à un
        DependencyGanttBlock ; group_column_id choisit le regroupement
        des sous-tâches en barres."""
        self.data["source_gantt_id"] = source_gantt_id
        self.data["group_column_id"] = group_column_id

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


def sync_bars_from_gantt(document, block: "BarChartBlock") -> list[dict[str, Any]]:
    """PATCH 54 — Recalcule les barres en direct à partir d'un planning
    par dépendances relié (`block.source_gantt_id`), jamais stockées
    (même principe que compute_schedule/compute_efficiency_ratio).

    Pour chaque sous-tâche du planning : "Prévu" = durée, "Réel" =
    durée + écart ("Ecarts", qu'il vienne de la colonne du tableau ou
    de l'ancien stockage propre au bloc — voir compute_schedule). Les
    sous-tâches sont regroupées par `group_column_id` (une colonne
    texte du tableau source, ex : "Phases") si définie, sinon chacune
    forme sa propre barre. Liste vide si non relié ou planning vide.
    """
    # Import différé : évite un import circulaire (dependency_gantt_block
    # ne dépend pas de bar_chart_block, mais les deux modules de blocs
    # sont souvent importés ensemble au niveau du registre).
    from blocks.dependency_gantt_block import DependencyGanttBlock, compute_schedule, find_source_table

    if block.source_gantt_id is None:
        return []
    gantt = document.find_block(block.source_gantt_id)
    if not isinstance(gantt, DependencyGanttBlock):
        return []
    schedule = compute_schedule(document, gantt)
    if not schedule:
        return []

    table = find_source_table(document, gantt)
    group_column = None
    if table is not None and block.group_column_id:
        group_column = table._find_column(block.group_column_id)
    rows_by_id = {row["id"]: row for row in table.rows} if table is not None else {}

    order: list[str] = []
    totals: dict[str, dict[str, float]] = {}
    for task in schedule:
        if group_column is not None:
            row = rows_by_id.get(task["row_id"])
            key = str(row["cells"].get(group_column["id"], "")) if row is not None else task["label"]
        else:
            key = task["label"]
        if key not in totals:
            totals[key] = {"value": 0.0, "actual": 0.0}
            order.append(key)
        totals[key]["value"] += task["duration"]
        totals[key]["actual"] += task["duration"] + task["delta"]

    return [
        {
            "id": key,
            "label": key,
            "value": totals[key]["value"],
            "actual": totals[key]["actual"],
            "color": PLANNED_BAR_COLOR,
        }
        for key in order
    ]