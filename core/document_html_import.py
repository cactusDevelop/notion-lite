"""
Import HTML (PATCH 40).

Fonction pure `html_to_document(html_text)` : lit un document HTML
(idéalement produit par `document_to_full_html`, PATCH 38, mais
tolérant à du HTML raisonnablement simple écrit à la main) et
reconstruit un Document avec les blocs correspondants.

Analyseur à base d'expressions régulières (pas de dépendance externe
type BeautifulSoup) : suffisant pour une structure de blocs top-level
non imbriqués (ce que produit notre propre export), mais ne gère pas
les imbrications profondes (ex. liste dans une liste) — limitation
documentée, comme pour l'import Markdown (PATCH 39).
"""
from __future__ import annotations

import html as html_module
import re

from blocks.checklist_block import ChecklistBlock
from blocks.code_block import CodeBlock
from blocks.heading_block import HeadingBlock
from blocks.image_block import ImageBlock
from blocks.list_block import LIST_TYPE_BULLET, LIST_TYPE_NUMBERED, ListBlock
from blocks.quote_block import QuoteBlock
from blocks.separator_block import SeparatorBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.text_block import TextBlock
from core.document import Document

_TAG_RE = re.compile(r"<[^>]+>")
_LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'src="data:image/([^;]+);base64,([^"]+)"')
_IMG_WIDTH_RE = re.compile(r'width="(\d+)"')

_BLOCK_RE = re.compile(
    r"<(?P<tag>h[1-6]|p|ul|ol|blockquote|pre|table)\b[^>]*>(?P<inner>.*?)</(?P=tag)>"
    r"|<hr\s*/?>"
    r"|<img\b[^>]*/?>",
    re.DOTALL | re.IGNORECASE,
)


def _strip_tags(fragment: str) -> str:
    """Retire les balises et décode les entités HTML."""
    return html_module.unescape(_TAG_RE.sub("", fragment)).strip()


def _extract_body(text: str) -> str:
    """Ne garde que le contenu de <body>...</body> s'il existe (retire
    doctype/head/style), sinon retourne le texte tel quel."""
    match = re.search(r"<body[^>]*>(.*)</body>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else text


def _parse_list_items(inner_html: str) -> list[str]:
    return [_strip_tags(item) for item in _LI_RE.findall(inner_html)]


def _parse_table_rows(inner_html: str) -> list[list[str]]:
    rows = []
    for row_html in _ROW_RE.findall(inner_html):
        rows.append([_strip_tags(cell) for cell in _CELL_RE.findall(row_html)])
    return rows


def _list_block_from(tag: str, inner_html: str) -> ListBlock | ChecklistBlock:
    items = _parse_list_items(inner_html)
    # Une liste dont TOUS les éléments commencent par ☑/☐ (marqueurs
    # produits par notre propre export de checklist) redevient une
    # ChecklistBlock plutôt qu'une ListBlock générique.
    if items and all(item.startswith(("☑", "☐")) for item in items):
        block = ChecklistBlock()
        for item in items:
            checked = item.startswith("☑")
            block.add_item(item[1:].strip(), checked=checked)
        return block

    list_type = LIST_TYPE_NUMBERED if tag == "ol" else LIST_TYPE_BULLET
    block = ListBlock(list_type=list_type)
    for item in items:
        block.add_item(item)
    return block


def _image_block_from(tag_html: str) -> ImageBlock | None:
    src_match = _IMG_SRC_RE.search(tag_html)
    if not src_match:
        return None
    width_match = _IMG_WIDTH_RE.search(tag_html)
    return ImageBlock(
        image_base64=src_match.group(2),
        image_format=src_match.group(1),
        width=int(width_match.group(1)) if width_match else None,
    )


def html_to_document(text: str) -> Document:
    """Reconstruit un Document à partir d'une chaîne HTML."""
    document = Document()
    body = _extract_body(text)

    for match in _BLOCK_RE.finditer(body):
        whole = match.group(0)
        tag = match.group("tag")

        if tag is None:
            if whole.lower().startswith("<hr"):
                document.add_block(SeparatorBlock())
            elif whole.lower().startswith("<img"):
                image = _image_block_from(whole)
                if image is not None:
                    document.add_block(image)
            continue

        inner = match.group("inner")
        tag = tag.lower()

        if tag.startswith("h") and tag[1:].isdigit():
            level = min(int(tag[1:]), 3)
            document.add_block(HeadingBlock(level=level, content=_strip_tags(inner)))
        elif tag == "p":
            text_content = _strip_tags(inner)
            if text_content:
                block = TextBlock(content=text_content)
                block.html = f"<p>{inner}</p>"
                document.add_block(block)
        elif tag in ("ul", "ol"):
            document.add_block(_list_block_from(tag, inner))
        elif tag == "blockquote":
            document.add_block(QuoteBlock(content=_strip_tags(inner)))
        elif tag == "pre":
            code_match = re.search(r"<code[^>]*>(.*?)</code>", inner, re.DOTALL | re.IGNORECASE)
            code_text = html_module.unescape(code_match.group(1) if code_match else inner)
            document.add_block(CodeBlock(content=code_text.strip("\n")))
        elif tag == "table":
            rows = _parse_table_rows(inner)
            if rows:
                document.add_block(SimpleTableBlock(rows=rows))

    return document
