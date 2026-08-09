"""
Import Markdown (PATCH 39).

Fonction pure `markdown_to_document(text)` : lit du Markdown standard
(GitHub-flavored pour les tableaux et cases à cocher) et reconstruit
un Document avec les blocs correspondants. Analyseur ligne par ligne,
volontairement simple (pas de dépendance externe), pensé pour
retrouver au mieux les blocs produits par `document_to_markdown`
(PATCH 37) — l'aller-retour Markdown n'est donc pas parfait pour du
Markdown écrit à la main dans un style très différent, mais couvre
la syntaxe standard.
"""
from __future__ import annotations

import re

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.text_block import TextBlock
from core.document import Document

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$")
_CHECKLIST_RE = re.compile(r"^[-*]\s+\[( |x|X)\]\s+(.*)$")
_HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
_NUMBERED_RE = re.compile(r"^\d+\.\s+(.*)$")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)$")


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def markdown_to_document(text: str) -> Document:
    """Reconstruit un Document à partir d'une chaîne Markdown."""
    document = Document()
    lines = text.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # Bloc de code : ```langage ... ```
        if line.strip().startswith("```"):
            language = line.strip()[3:].strip() or "text"
            i += 1
            code_lines: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # saute la clôture ```
            document.add_block(CodeBlock(content="\n".join(code_lines), language=language))
            continue

        # Titre : # à ###### (les niveaux > 3 sont ramenés à 3, HeadingBlock
        # ne supportant que H1-H3).
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            level = min(len(heading_match.group(1)), 3)
            document.add_block(HeadingBlock(level=level, content=heading_match.group(2).strip()))
            i += 1
            continue

        # Tableau : ligne d'en-tête "|...|" suivie d'une ligne séparatrice.
        if line.strip().startswith("|") and i + 1 < n and _TABLE_SEPARATOR_RE.match(lines[i + 1]):
            table_rows = [_split_table_row(line)]
            i += 2  # saute l'en-tête + la ligne séparatrice
            while i < n and lines[i].strip().startswith("|"):
                table_rows.append(_split_table_row(lines[i]))
                i += 1
            document.add_block(SimpleTableBlock(rows=table_rows))
            continue

        # Checklist : "- [ ] texte" / "- [x] texte" (avant la liste à puces,
        # dont c'est un cas particulier).
        if _CHECKLIST_RE.match(line):
            block = ChecklistBlock()
            while i < n:
                match = _CHECKLIST_RE.match(lines[i])
                if not match:
                    break
                block.add_item(match.group(2), checked=match.group(1).lower() == "x")
                i += 1
            document.add_block(block)
            continue

        # Séparateur : ligne de tirets/astérisques seule.
        if _HR_RE.match(line.strip()):
            document.add_block(SeparatorBlock())
            i += 1
            continue

        # Liste numérotée : "1. texte", "2. texte", ...
        if _NUMBERED_RE.match(line):
            block = ListBlock(list_type=LIST_TYPE_NUMBERED)
            while i < n:
                match = _NUMBERED_RE.match(lines[i])
                if not match:
                    break
                block.add_item(match.group(1))
                i += 1
            document.add_block(block)
            continue

        # Liste à puces : "- texte" / "* texte" (hors case à cocher, déjà géré).
        if _BULLET_RE.match(line) and not _CHECKLIST_RE.match(line):
            block = ListBlock(list_type=LIST_TYPE_BULLET)
            while i < n:
                if _CHECKLIST_RE.match(lines[i]):
                    break
                match = _BULLET_RE.match(lines[i])
                if not match:
                    break
                block.add_item(match.group(1))
                i += 1
            document.add_block(block)
            continue

        # Citation : lignes commençant par ">"
        if line.strip().startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            document.add_block(QuoteBlock(content="\n".join(quote_lines)))
            continue

        # Paragraphe : lignes consécutives non vides -> bloc Texte.
        paragraph_lines = []
        while i < n and lines[i].strip():
            paragraph_lines.append(lines[i])
            i += 1
        document.add_block(TextBlock(content="\n".join(paragraph_lines)))

    return document
