"""
Registre de reconstruction des blocs (PATCH 8 / PATCH 9).

Fait le lien entre le type stocké dans le JSON et la classe de bloc
concrète à instancier. Chaque nouveau type de bloc (checklist, image,
tableau, ...) devra enregistrer sa propre reconstruction ici.
"""
from __future__ import annotations

from typing import Any

from blocks.checklist_block import CHECKLIST_BLOCK_TYPE, ChecklistBlock
from blocks.code_block import CODE_BLOCK_TYPE, CodeBlock
from blocks.bar_chart_block import BAR_CHART_BLOCK_TYPE, BarChartBlock
from blocks.dependency_gantt_block import DEPENDENCY_GANTT_BLOCK_TYPE, DependencyGanttBlock
from blocks.formula_block import FORMULA_BLOCK_TYPE, FormulaBlock
from blocks.gantt_block import GANTT_BLOCK_TYPE, GanttBlock
from blocks.heading_block import HEADING_TYPES, HeadingBlock
from blocks.image_block import IMAGE_BLOCK_TYPE, ImageBlock
from blocks.linked_checklist_block import LINKED_CHECKLIST_BLOCK_TYPE, LinkedChecklistBlock
from blocks.line_chart_block import LINE_CHART_BLOCK_TYPE, LineChartBlock
from blocks.list_block import LIST_BLOCK_TYPE, ListBlock
from blocks.people_list_block import PEOPLE_LIST_BLOCK_TYPE, PeopleListBlock
from blocks.quote_block import QUOTE_BLOCK_TYPE, QuoteBlock
from blocks.separator_block import SEPARATOR_BLOCK_TYPE, SeparatorBlock
from blocks.simple_table_block import SIMPLE_TABLE_BLOCK_TYPE, SimpleTableBlock
from blocks.table_block import TABLE_BLOCK_TYPE, TableBlock
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

    if block_type == CHECKLIST_BLOCK_TYPE:
        return ChecklistBlock(items=data.get("items", []), id=block_id)

    if block_type == LINKED_CHECKLIST_BLOCK_TYPE:
        return LinkedChecklistBlock(
            items=data.get("items", []), split=data.get("split", 0.5), id=block_id
        )

    if block_type == IMAGE_BLOCK_TYPE:
        return ImageBlock(
            image_base64=data.get("image_base64", ""),
            image_format=data.get("format", "png"),
            width=data.get("width"),
            id=block_id,
        )

    if block_type == TABLE_BLOCK_TYPE:
        return TableBlock(
            columns=data.get("columns", []),
            rows=data.get("rows", []),
            manual_merges=data.get("manual_merges", {}),
            id=block_id,
        )

    if block_type == GANTT_BLOCK_TYPE:
        return GanttBlock(
            table_block_id=data.get("table_block_id"),
            label_column_id=data.get("label_column_id"),
            date_column_id=data.get("date_column_id"),
            id=block_id,
        )

    if block_type == FORMULA_BLOCK_TYPE:
        return FormulaBlock(
            table_block_id=data.get("table_block_id"),
            number_column_id=data.get("number_column_id"),
            boolean_column_id=data.get("boolean_column_id"),
            label=data.get("label", "Résultat: "),
            id=block_id,
        )

    if block_type == DEPENDENCY_GANTT_BLOCK_TYPE:
        return DependencyGanttBlock(
            table_block_id=data.get("table_block_id"),
            label_column_id=data.get("label_column_id"),
            person_column_id=data.get("person_column_id"),
            duration_column_id=data.get("duration_column_id"),
            risk_column_id=data.get("risk_column_id"),
            dependency_column_id=data.get("dependency_column_id"),
            delta_column_id=data.get("delta_column_id"),
            deltas=data.get("deltas", {}),
            chart_format=data.get("chart_format", "micro"),
            start_date=data.get("start_date", ""),
            # PATCH 89 — manquait à la reconstruction : le bloc était
            # bien enregistré avec sa colonne "Phases" (voir
            # DependencyGanttBlock.set_source / to_dict), mais elle
            # était silencieusement perdue à chaque réouverture,
            # puisque jamais relue ici.
            # PATCH 89 — manquait à la reconstruction : le bloc était
            # bien enregistré avec sa colonne "Phases" (voir
            # DependencyGanttBlock.set_source / to_dict), mais elle
            # était silencieusement perdue à chaque réouverture,
            # puisque jamais relue ici.
            phase_column_id=data.get("phase_column_id"),
            id=block_id,
        )

    if block_type == LINE_CHART_BLOCK_TYPE:
        return LineChartBlock(
            title=data.get("title", ""),
            x_axis_label=data.get("x_axis_label", ""),
            y_axis_label=data.get("y_axis_label", ""),
            x_max=data.get("x_max", 10.0),
            series=data.get("series", []),
            id=block_id,
        )

    if block_type == BAR_CHART_BLOCK_TYPE:
        return BarChartBlock(
            title=data.get("title", "Graphique"),
            y_axis_label=data.get("y_axis_label", ""),
            source_gantt_id=data.get("source_gantt_id"),
            group_column_id=data.get("group_column_id"),
            value_column_id=data.get("value_column_id"),
            actual_column_id=data.get("actual_column_id"),
            id=block_id,
        )

    if block_type == SIMPLE_TABLE_BLOCK_TYPE:
        return SimpleTableBlock(rows=data.get("rows", []), id=block_id)

    if block_type == SEPARATOR_BLOCK_TYPE:
        return SeparatorBlock(id=block_id)

    if block_type == CODE_BLOCK_TYPE:
        return CodeBlock(content=data.get("content", ""), language=data.get("language", "text"), id=block_id)

    if block_type == LIST_BLOCK_TYPE:
        return ListBlock(
            items=data.get("items", []),
            list_type=data.get("list_type", "bullet"),
            id=block_id,
        )

    if block_type == PEOPLE_LIST_BLOCK_TYPE:
        return PeopleListBlock(id=block_id)

    if block_type == QUOTE_BLOCK_TYPE:
        return QuoteBlock(content=data.get("content", ""), id=block_id)

    if block_type in _LEVEL_BY_TYPE:
        return HeadingBlock(
            level=_LEVEL_BY_TYPE[block_type],
            content=data.get("content", ""),
            id=block_id,
        )

    raise ValueError(f"Type de bloc inconnu dans le fichier : {block_type!r}")
