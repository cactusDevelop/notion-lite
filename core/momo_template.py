"""
Template par défaut "Méthodo Momo" (PATCH 48).

Construit un Document complet illustrant l'ensemble des blocs du
projet : titres, effectif, checklists liées, tableau de critères
noté avec résultat calculé, tableau d'assignation de tâches relié à
un planning par dépendances, et deux graphiques (courbes
"Efficacité" et bâtonnets "Delta de budget").

Toutes les valeurs d'exemple (noms, critères, tâches, montants) sont
arbitraires et destinées à être modifiées par l'utilisateur.
"""
from __future__ import annotations

import random

from blocks.bar_chart_block import BarChartBlock
from blocks.dependency_gantt_block import DependencyGanttBlock
from blocks.formula_block import FormulaBlock
from blocks.heading_block import HeadingBlock
from blocks.line_chart_block import SLOPE_MODE_CONSTANT, SLOPE_MODE_EFFICIENCY, LineChartBlock
from blocks.linked_checklist_block import LinkedChecklistBlock
from blocks.table_block import (
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_MULTI_SELECT,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_PERSON,
    COLUMN_TYPE_SELECT,
    COLUMN_TYPE_TEXT,
    TableBlock,
)
from blocks.text_block import TextBlock
from core.document import Document

# Vivier de noms utilisé pour tirer l'effectif d'exemple au hasard
# (PATCH 48) : trois noms différents à chaque nouveau document créé
# depuis ce template.
_SAMPLE_NAMES = [
    "Camille Dupont",
    "Yanis Bernard",
    "Lina Rousseau",
    "Hugo Lefevre",
    "Nora Girard",
    "Théo Morel",
    "Chloé Fontaine",
    "Adam Perrin",
]

_RISK_OPTIONS = ["vert", "orange", "rouge"]


def build_momo_template() -> Document:
    """Construit un nouveau Document à partir du template "Méthodo Momo"."""
    document = Document()

    # -- Titre + Effectif -------------------------------------------------
    document.add_block(HeadingBlock(level=1, content="Méthodo Momo"))
    document.add_block(HeadingBlock(level=2, content="Effectif"))

    names = random.sample(_SAMPLE_NAMES, 3)
    people = [document.add_person(name) for name in names]
    document.add_block(TextBlock(content="\n".join(f"• {name}" for name in names)))

    # -- Checklist initiale (deux checklists liées) ------------------------
    document.add_block(HeadingBlock(level=2, content="Checklist initiale"))
    checklist = LinkedChecklistBlock()
    for label in ("A", "B", "C"):
        checklist.add_item(text=label)
    document.add_block(checklist)

    # -- Critères (tableau noté + résultat calculé) ------------------------
    document.add_block(HeadingBlock(level=2, content="Critères"))
    criteria_table = TableBlock()
    cat_col = criteria_table.add_column("Catégorie", col_type=COLUMN_TYPE_TEXT)
    state_col = criteria_table.add_column("Etat", col_type=COLUMN_TYPE_BOOLEAN)
    points_col = criteria_table.add_column("Points", col_type=COLUMN_TYPE_NUMBER)
    details_col = criteria_table.add_column("Détails", col_type=COLUMN_TYPE_TEXT)
    for cat, state, points, details in (
        ("Qualité du code", True, "5", "Revue effectuée, conventions respectées"),
        ("Tests automatisés", False, "3", "Couverture partielle à compléter"),
        ("Documentation", True, "2", "README à jour"),
    ):
        criteria_table.add_row(
            values={
                cat_col["id"]: cat,
                state_col["id"]: state,
                points_col["id"]: points,
                details_col["id"]: details,
            }
        )
    document.add_block(criteria_table)

    result_block = FormulaBlock(
        table_block_id=criteria_table.id,
        number_column_id=points_col["id"],
        boolean_column_id=state_col["id"],
        label="Résultat: ",
    )
    document.add_block(result_block)

    # -- Assignation des tâches (planning par dépendances) -----------------
    document.add_block(HeadingBlock(level=2, content="Assignation des tâches"))
    tasks_table = TableBlock()
    phase_col = tasks_table.add_column("Phases", col_type=COLUMN_TYPE_TEXT)
    subtask_col = tasks_table.add_column("Sous-tâches", col_type=COLUMN_TYPE_TEXT)
    assignee_col = tasks_table.add_column("Prsn. assignées", col_type=COLUMN_TYPE_PERSON)
    duration_col = tasks_table.add_column("Temps estimé (jours)", col_type=COLUMN_TYPE_NUMBER)
    risk_col = tasks_table.add_column("Risques", col_type=COLUMN_TYPE_SELECT, options=list(_RISK_OPTIONS))
    dependency_col = tasks_table.add_column("Dépendances", col_type=COLUMN_TYPE_MULTI_SELECT)
    delta_col = tasks_table.add_column("Ecarts", col_type=COLUMN_TYPE_NUMBER)

    example_tasks = [
        ("Phase 1", "Conception", [people[0]["id"]], "3", "vert", [], "0"),
        ("Phase 1", "Maquettes", [people[1]["id"]], "2", "orange", ["Conception"], "0"),
        ("Phase 2", "Développement", [people[1]["id"], people[2]["id"]], "5", "orange", ["Maquettes"], "0"),
        ("Phase 2", "Tests", [people[2]["id"]], "2.5", "rouge", ["Développement"], "0"),
    ]
    subtask_labels = [row[1] for row in example_tasks]
    tasks_table.set_column_options(dependency_col["id"], subtask_labels)

    for phase, subtask, assignees, duration, risk, dependencies, ecart in example_tasks:
        tasks_table.add_row(
            values={
                phase_col["id"]: phase,
                subtask_col["id"]: subtask,
                assignee_col["id"]: assignees,
                duration_col["id"]: duration,
                risk_col["id"]: risk,
                dependency_col["id"]: dependencies,
                delta_col["id"]: ecart,
            }
        )
    document.add_block(tasks_table)

    gantt = DependencyGanttBlock(
        table_block_id=tasks_table.id,
        label_column_id=subtask_col["id"],
        person_column_id=assignee_col["id"],
        duration_column_id=duration_col["id"],
        risk_column_id=risk_col["id"],
        dependency_column_id=dependency_col["id"],
        delta_column_id=delta_col["id"],
    )
    document.add_block(gantt)

    # -- Graphique "Efficacité" ---------------------------------------------
    efficiency_chart = LineChartBlock(
        title="Efficacité", x_axis_label="Temps", y_axis_label="Avancement moyen", x_max=12
    )
    efficiency_chart.add_series(name="Idéal", mode=SLOPE_MODE_CONSTANT, slope=1.0, color="#43a047")
    # Constante de vélocité arbitraire, à ajuster par l'utilisateur.
    efficiency_chart.add_series(name="Vélocité", mode=SLOPE_MODE_CONSTANT, slope=0.8, color="#fb8c00")
    efficiency_chart.add_series(
        name="Vélocité réelle",
        mode=SLOPE_MODE_EFFICIENCY,
        source_block_id=gantt.id,
        color="#1976d2",
    )
    document.add_block(efficiency_chart)

    # -- Graphique "Delta de budget" (une barre "Prévu" par phase, marqueur
    # "Réel" en pointillés — contenu provisoire) -----------------------------
    budget_chart = BarChartBlock(title="Delta de budget", y_axis_label="Prix")
    budget_chart.add_bar(label="Phase 1", value=1000, actual=1150)
    budget_chart.add_bar(label="Phase 2", value=1500, actual=1400)
    document.add_block(budget_chart)

    return document