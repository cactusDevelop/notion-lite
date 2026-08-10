"""
Bloc "Gantt (dépendances)" (PATCH 46, révisé PATCH 49).

Contrairement à GanttBlock (qui lit des dates absolues), ce bloc
calcule un planning à partir de DURÉES (colonne "Nombre", en jours)
et de DÉPENDANCES entre sous-tâches (colonne "Liste multiple", dont
les valeurs sont les libellés d'autres lignes) : la date de début
d'une sous-tâche est déterminée par la résolution de ses dépendances,
pas par une date saisie.

Deux façons de déclarer un retard/avance (en jours) sur une
sous-tâche :
    - `delta_column_id` (PATCH 49) : référence vers une colonne
      "Nombre" du tableau source (ex : "Ecarts"). Dès qu'elle est
      configurée, c'est TOUJOURS elle qui fait foi — l'écart se
      règle alors directement dans le tableau, comme n'importe
      quelle autre valeur d'une sous-tâche.
    - `deltas` (historique, PATCH 46) : dictionnaire {row_id: jours}
      propre au bloc, utilisé uniquement tant qu'aucune
      `delta_column_id` n'est configurée (rétrocompatibilité avec
      les documents créés avant PATCH 49).

Le point de résolution d'une sous-tâche (utilisé comme date de début
des sous-tâches qui en dépendent) est toujours `fin_planifiée + delta` :
    - delta > 0 : la sous-tâche a fini en retard, la barre est
      prolongée en noir jusqu'à ce point.
    - delta < 0 : la sous-tâche a fini en avance, le temps gagné (la
      fin de la barre normale) est recoloré en bleu.
    - delta == 0 : résolution à l'heure, à la fin planifiée.

Le planning est toujours calculé et stocké EN JOURS ; PATCH 49
ajoute uniquement un affichage optionnel "en mois" côté widget
(`DAYS_PER_MONTH` / `format_duration_in_unit` ci-dessous), sans
jamais changer l'unité de stockage.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from blocks.table_block import (
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_TEXT,
    TableBlock,
)
from core.block import Block

DEPENDENCY_GANTT_BLOCK_TYPE = "dependency_gantt"

RISK_COLORS: dict[str, str] = {
    "vert": "#4caf50",
    "orange": "#ff9800",
    "rouge": "#f44336",
}
_DEFAULT_BAR_COLOR = "#4db6ac"

# PATCH 49 — équivalence utilisée uniquement pour l'affichage "en mois"
# (le stockage reste toujours en jours).
DAYS_PER_MONTH = 30.0

UNIT_DAYS = "jours"
UNIT_MONTHS = "mois"


def format_duration_in_unit(days: float, unit: str) -> str:
    """Formate une durée (toujours reçue en jours) pour l'affichage,
    selon `unit` ("jours" ou "mois"). Ne change jamais la valeur
    stockée, uniquement le texte affiché."""
    if unit == UNIT_MONTHS:
        return f"{days / DAYS_PER_MONTH:g} mois"
    return f"{days:g} j"


class DependencyGanttBlock(Block):
    """Bloc Gantt calculé à partir de durées et de dépendances.

    Données (data) :
        table_block_id / label_column_id / person_column_id /
        duration_column_id / risk_column_id / dependency_column_id :
            références vers le TableBlock source (mêmes principes que
            GanttBlock : rien d'autre n'est dupliqué ici).
        deltas: {row_id: float} — retard (positif) ou avance
            (négatif) déclaré manuellement sur une sous-tâche.
    """

    def __init__(
        self,
        table_block_id: Optional[str] = None,
        label_column_id: Optional[str] = None,
        person_column_id: Optional[str] = None,
        duration_column_id: Optional[str] = None,
        risk_column_id: Optional[str] = None,
        dependency_column_id: Optional[str] = None,
        delta_column_id: Optional[str] = None,
        deltas: dict[str, float] | None = None,
        time_unit: str = UNIT_DAYS,
        id: str | None = None,
    ) -> None:
        super().__init__(
            type=DEPENDENCY_GANTT_BLOCK_TYPE,
            data={
                "table_block_id": table_block_id,
                "label_column_id": label_column_id,
                "person_column_id": person_column_id,
                "duration_column_id": duration_column_id,
                "risk_column_id": risk_column_id,
                "dependency_column_id": dependency_column_id,
                "delta_column_id": delta_column_id,
                "deltas": dict(deltas or {}),
                "time_unit": time_unit,
            },
            id=id or str(uuid.uuid4()),
        )

    @property
    def table_block_id(self) -> Optional[str]:
        return self.data.get("table_block_id")

    @property
    def label_column_id(self) -> Optional[str]:
        return self.data.get("label_column_id")

    @property
    def person_column_id(self) -> Optional[str]:
        return self.data.get("person_column_id")

    @property
    def duration_column_id(self) -> Optional[str]:
        return self.data.get("duration_column_id")

    @property
    def risk_column_id(self) -> Optional[str]:
        return self.data.get("risk_column_id")

    @property
    def dependency_column_id(self) -> Optional[str]:
        return self.data.get("dependency_column_id")

    @property
    def delta_column_id(self) -> Optional[str]:
        return self.data.get("delta_column_id")

    @property
    def time_unit(self) -> str:
        """PATCH 49 — unité d'affichage de l'axe temporel et des valeurs
        chiffrées du planning ("jours" ou "mois"). Le stockage interne
        reste toujours en jours, voir format_duration_in_unit()."""
        return self.data.get("time_unit", UNIT_DAYS)

    @time_unit.setter
    def time_unit(self, value: str) -> None:
        self.data["time_unit"] = value if value in (UNIT_DAYS, UNIT_MONTHS) else UNIT_DAYS

    def set_source(
        self,
        table_block_id: Optional[str],
        label_column_id: Optional[str] = None,
        person_column_id: Optional[str] = None,
        duration_column_id: Optional[str] = None,
        risk_column_id: Optional[str] = None,
        dependency_column_id: Optional[str] = None,
        delta_column_id: Optional[str] = None,
    ) -> None:
        self.data["table_block_id"] = table_block_id
        self.data["label_column_id"] = label_column_id
        self.data["person_column_id"] = person_column_id
        self.data["duration_column_id"] = duration_column_id
        self.data["risk_column_id"] = risk_column_id
        self.data["dependency_column_id"] = dependency_column_id
        self.data["delta_column_id"] = delta_column_id

    @property
    def deltas(self) -> dict[str, float]:
        return self.data.setdefault("deltas", {})

    def get_delta(self, row_id: str) -> float:
        return float(self.deltas.get(row_id, 0.0))

    def set_delta(self, row_id: str, value: float) -> None:
        if value:
            self.deltas[row_id] = float(value)
        else:
            self.deltas.pop(row_id, None)


def find_source_table(document, block: DependencyGanttBlock) -> Optional[TableBlock]:
    if block.table_block_id is None:
        return None
    found = document.find_block(block.table_block_id)
    return found if isinstance(found, TableBlock) else None


def available_label_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_TEXT]


def available_person_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_PERSON]


def available_duration_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_NUMBER]


def available_delta_columns(table: TableBlock) -> list[dict[str, Any]]:
    """Colonnes "Nombre" utilisables comme colonne d'écart ("Ecarts") —
    même filtre que la durée : n'importe quelle colonne numérique."""
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_NUMBER]


def available_risk_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_SELECT]


def available_dependency_columns(table: TableBlock) -> list[dict[str, Any]]:
    return [c for c in table.columns if c["type"] == COLUMN_TYPE_MULTI_SELECT]


def _to_number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ".").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def compute_efficiency_ratio(document, block: "DependencyGanttBlock") -> Optional[float]:
    """Ratio "vélocité réelle" = durée planifiée totale / (durée planifiée
    totale + retard total), utilisé par le bloc graphique "Courbes"
    pour tracer une droite de vélocité réelle du planning. None si le
    planning est vide ou sans aucune durée."""
    schedule = compute_schedule(document, block)
    if not schedule:
        return None
    total_duration = sum(t["duration"] for t in schedule)
    total_delay = sum(max(t["delta"], 0.0) for t in schedule)
    denominator = total_duration + total_delay
    if denominator <= 0:
        return None
    return total_duration / denominator


def compute_schedule(document, block: DependencyGanttBlock) -> list[dict[str, Any]]:
    """Calcule le planning complet à partir de l'état actuel du document.

    Retourne une liste (dans l'ordre des lignes du tableau) de :
        {row_id, label, person_names, risk, dependencies (libellés),
         duration, planned_start, planned_end, start, end, resolution,
         delta}
    "start"/"end" sont les bornes de la barre normale (après décalage
    en cascade par les dépendances) ; "resolution" est le point où la
    sous-tâche est effectivement considérée comme terminée, utilisé
    comme point de départ des sous-tâches qui en dépendent.
    """
    table = find_source_table(document, block)
    if table is None:
        return []

    label_column = table._find_column(block.label_column_id) if block.label_column_id else None
    duration_column = table._find_column(block.duration_column_id) if block.duration_column_id else None
    person_column = table._find_column(block.person_column_id) if block.person_column_id else None
    risk_column = table._find_column(block.risk_column_id) if block.risk_column_id else None
    dependency_column = table._find_column(block.dependency_column_id) if block.dependency_column_id else None
    delta_column = table._find_column(block.delta_column_id) if block.delta_column_id else None

    if label_column is None or duration_column is None:
        return []

    # Résolution des dépendances par libellé (premier match si doublon).
    row_id_by_label: dict[str, str] = {}
    for row in table.rows:
        label = str(row["cells"].get(label_column["id"], ""))
        row_id_by_label.setdefault(label, row["id"])

    rows_by_id = {row["id"]: row for row in table.rows}

    def _dependency_row_ids(row: dict[str, Any]) -> list[str]:
        if dependency_column is None:
            return []
        labels = row["cells"].get(dependency_column["id"]) or []
        return [row_id_by_label[label] for label in labels if label in row_id_by_label]

    def _duration(row: dict[str, Any]) -> float:
        return max(_to_number(row["cells"].get(duration_column["id"])), 0.0)

    def _get_delta(row: dict[str, Any], row_id: str) -> float:
        """L'écart vient de la colonne "Ecarts" si configurée (PATCH 49),
        sinon repli sur l'ancien stockage `deltas` du bloc (documents
        enregistrés avant cette colonne)."""
        if delta_column is not None:
            return _to_number(row["cells"].get(delta_column["id"]))
        return block.get_delta(row_id)

    memo: dict[str, dict[str, float]] = {}

    def _resolve(row_id: str, visiting: set[str]) -> dict[str, float]:
        if row_id in memo:
            return memo[row_id]
        row = rows_by_id.get(row_id)
        if row is None:
            result = {"start": 0.0, "end": 0.0, "resolution": 0.0}
            memo[row_id] = result
            return result
        if row_id in visiting:
            # Dépendance circulaire : on casse la boucle en ignorant les
            # dépendances de cette ligne plutôt que de boucler à l'infini.
            start = 0.0
        else:
            visiting = visiting | {row_id}
            dep_ids = _dependency_row_ids(row)
            start = max((_resolve(dep_id, visiting)["resolution"] for dep_id in dep_ids), default=0.0)

        duration = _duration(row)
        end = start + duration
        delta = _get_delta(row, row_id)
        resolution = end + delta
        result = {"start": start, "end": end, "resolution": resolution}
        memo[row_id] = result
        return result

    people_by_id = {person["id"]: person for person in document.people}

    schedule: list[dict[str, Any]] = []
    for row in table.rows:
        computed = _resolve(row["id"], set())
        person_ids = row["cells"].get(person_column["id"], []) if person_column else []
        person_names = [people_by_id[pid]["name"] for pid in person_ids if pid in people_by_id]
        risk = row["cells"].get(risk_column["id"], "") if risk_column else ""
        dependencies = row["cells"].get(dependency_column["id"], []) if dependency_column else []
        schedule.append(
            {
                "row_id": row["id"],
                "label": str(row["cells"].get(label_column["id"], "")),
                "person_names": person_names,
                "risk": risk,
                "color": RISK_COLORS.get(risk, _DEFAULT_BAR_COLOR),
                "dependencies": list(dependencies),
                "duration": _duration(row),
                "start": computed["start"],
                "end": computed["end"],
                "resolution": computed["resolution"],
                "delta": _get_delta(row, row["id"]),
            }
        )
    return schedule