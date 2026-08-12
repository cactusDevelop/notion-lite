"""
Bloc "Graphique en bâtonnets" (PATCH 47, révisé PATCH 49, PATCH 54, PATCH 59).

Barres "Prévu" (bleu) avec, pour chacune, une valeur "Réel"
optionnelle affichée sous forme de marqueur en pointillés (rouge si
le réel dépasse le prévu — dépassement de budget —, vert sinon).
Utilisé par exemple pour le graphique "Delta de budget" du template.

PATCH 54 : le graphique peut désormais être relié à un bloc "Planning
par dépendances" (`source_gantt_id`), et regroupé par une colonne
texte de son tableau source (`group_column_id`, ex : "Phases"). Une
fois relié, les barres ne sont plus éditées manuellement : elles sont
recalculées en direct à chaque lecture.

PATCH 59 : l'édition manuelle des barres a été retirée (la ligne
"Phase / Prévu / Réel" + bouton "Ajouter une barre" ne servait plus à
rien une fois le graphique toujours relié à une source). Le calcul se
base désormais, par défaut, sur deux colonnes "Nombre" du tableau
source (`value_column_id`/`actual_column_id`, ex : "Prix estimé" /
"Prix réel") plutôt que sur la durée/l'écart en jours des
sous-tâches — utilisé notamment pour "Delta de budget", qui n'a
jamais représenté un nombre de jours mais bien un montant. Si aucune
colonne de prix n'est choisie, on retombe sur l'ancien calcul
durée + écart (voir sync_bars_from_gantt).
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
    """Bloc graphique en bâtonnets, toujours recalculé à partir d'un
    planning par dépendances relié (PATCH 59 — plus d'édition manuelle).

    Données (data) :
        title: titre affiché au-dessus du graphique.
        y_axis_label: libellé de l'axe des ordonnées (ex : "Prix").
        source_gantt_id: id d'un DependencyGanttBlock. Si None, aucune
            barre n'est affichée (voir sync_bars_from_gantt).
        group_column_id: id d'une colonne texte du tableau source du
            Gantt relié, utilisée pour regrouper les sous-tâches en
            barres (ex : "Phases"). Si None, chaque sous-tâche forme
            sa propre barre.
        value_column_id / actual_column_id (PATCH 59) : id de colonnes
            "Nombre" du tableau source utilisées comme montant "Prévu"
            / "Réel" (ex : "Prix estimé" / "Prix réel"). Si
            value_column_id est None, repli sur l'ancien calcul
            durée + écart ("Ecarts") des sous-tâches.
    """

    def __init__(
        self,
        title: str = "Graphique",
        y_axis_label: str = "",
        source_gantt_id: Optional[str] = None,
        group_column_id: Optional[str] = None,
        value_column_id: Optional[str] = None,
        actual_column_id: Optional[str] = None,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=BAR_CHART_BLOCK_TYPE,
            data={
                "title": title,
                "y_axis_label": y_axis_label,
                "source_gantt_id": source_gantt_id,
                "group_column_id": group_column_id,
                "value_column_id": value_column_id,
                "actual_column_id": actual_column_id,
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
    def source_gantt_id(self) -> Optional[str]:
        return self.data.get("source_gantt_id")

    @property
    def group_column_id(self) -> Optional[str]:
        return self.data.get("group_column_id")

    @property
    def value_column_id(self) -> Optional[str]:
        return self.data.get("value_column_id")

    @property
    def actual_column_id(self) -> Optional[str]:
        return self.data.get("actual_column_id")

    def set_source(
        self,
        source_gantt_id: Optional[str],
        group_column_id: Optional[str] = None,
        value_column_id: Optional[str] = None,
        actual_column_id: Optional[str] = None,
    ) -> None:
        """PATCH 54, étendu PATCH 59 — Relie (ou détache si None) ce
        graphique à un DependencyGanttBlock ; `group_column_id` choisit
        le regroupement des sous-tâches en barres ; `value_column_id`/
        `actual_column_id` choisissent les colonnes "Prévu"/"Réel"
        (repli sur durée + écart si `value_column_id` est None)."""
        self.data["source_gantt_id"] = source_gantt_id
        self.data["group_column_id"] = group_column_id
        self.data["value_column_id"] = value_column_id
        self.data["actual_column_id"] = actual_column_id


def budget_marker_color(bar: dict[str, Any]) -> Optional[str]:
    """Couleur du marqueur "Réel" : rouge en dépassement de budget
    (réel > prévu), vert sinon. None si aucun "Réel" renseigné."""
    if bar.get("actual") is None:
        return None
    return OVER_BUDGET_COLOR if bar["actual"] > bar["value"] else UNDER_BUDGET_COLOR


def _to_number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ".").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def sync_bars_from_gantt(document, block: "BarChartBlock") -> list[dict[str, Any]]:
    """PATCH 54, étendu PATCH 59 — Recalcule les barres en direct à
    partir d'un planning par dépendances relié (`block.source_gantt_id`),
    jamais stockées (même principe que compute_schedule/
    compute_efficiency_ratio).

    Si `value_column_id` est configuré (ex : "Prix estimé"), "Prévu"/
    "Réel" viennent de ces deux colonnes "Nombre" du tableau source
    (PATCH 59). Sinon, repli sur l'ancien calcul : "Prévu" = durée,
    "Réel" = durée + écart ("Ecarts"). Les sous-tâches sont regroupées
    par `group_column_id` (une colonne texte du tableau source, ex :
    "Phases") si définie, sinon chacune forme sa propre barre. Liste
    vide si non relié ou planning vide.
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

    value_column = None
    actual_column = None
    if table is not None and block.value_column_id:
        value_column = table._find_column(block.value_column_id)
    if table is not None and block.actual_column_id:
        actual_column = table._find_column(block.actual_column_id)
    use_price_columns = value_column is not None

    order: list[str] = []
    totals: dict[str, dict[str, Any]] = {}
    for task in schedule:
        row = rows_by_id.get(task["row_id"])
        if group_column is not None:
            key = str(row["cells"].get(group_column["id"], "")) if row is not None else task["label"]
        else:
            key = task["label"]
        if key not in totals:
            totals[key] = {
                "value": 0.0,
                # PATCH 59 — sans colonne "Réel" configurée, aucun
                # marqueur n'est affiché (None), plutôt qu'un 0 trompeur.
                "actual": 0.0 if (not use_price_columns or actual_column is not None) else None,
            }
            order.append(key)

        if use_price_columns:
            totals[key]["value"] += _to_number(row["cells"].get(value_column["id"])) if row is not None else 0.0
            if actual_column is not None:
                totals[key]["actual"] += _to_number(row["cells"].get(actual_column["id"])) if row is not None else 0.0
        else:
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