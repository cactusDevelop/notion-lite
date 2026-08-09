"""
Support des emojis (PATCH 35).

Fonctions pures (indépendantes de Qt) : liste catégorisée d'emojis
avec leur "shortcode" façon Slack/Discord (ex. ``:smile:`` -> 😄),
recherche par nom/shortcode, et résolution d'un shortcode tapé au
clavier.
"""
from __future__ import annotations

import re

# (emoji, shortcode, catégorie) — liste volontairement compacte mais
# couvrant les usages courants d'une prise de notes.
EMOJIS: list[tuple[str, str, str]] = [
    ("😀", "grinning", "Émotions"),
    ("😄", "smile", "Émotions"),
    ("😂", "joy", "Émotions"),
    ("🙂", "slight_smile", "Émotions"),
    ("😉", "wink", "Émotions"),
    ("😍", "heart_eyes", "Émotions"),
    ("😢", "cry", "Émotions"),
    ("😡", "angry", "Émotions"),
    ("😱", "scream", "Émotions"),
    ("🤔", "thinking", "Émotions"),
    ("👍", "thumbsup", "Gestes"),
    ("👎", "thumbsdown", "Gestes"),
    ("👏", "clap", "Gestes"),
    ("🙏", "pray", "Gestes"),
    ("💪", "muscle", "Gestes"),
    ("✅", "white_check_mark", "Symboles"),
    ("❌", "x", "Symboles"),
    ("⚠️", "warning", "Symboles"),
    ("⭐", "star", "Symboles"),
    ("🔥", "fire", "Symboles"),
    ("💡", "bulb", "Symboles"),
    ("📌", "pushpin", "Symboles"),
    ("📎", "paperclip", "Symboles"),
    ("📅", "calendar", "Objets"),
    ("⏰", "alarm_clock", "Objets"),
    ("📝", "memo", "Objets"),
    ("📊", "bar_chart", "Objets"),
    ("💻", "computer", "Objets"),
    ("📁", "file_folder", "Objets"),
    ("🚀", "rocket", "Objets"),
    ("🎉", "tada", "Objets"),
    ("☕", "coffee", "Objets"),
    ("🍕", "pizza", "Objets"),
]

_SHORTCODE_RE = re.compile(r":([a-zA-Z0-9_+\-]+):$")
_SHORTCODE_TO_EMOJI: dict[str, str] = {shortcode: emoji for emoji, shortcode, _ in EMOJIS}


def search_emojis(query: str) -> list[tuple[str, str, str]]:
    """Filtre EMOJIS dont le shortcode contient `query` (insensible à la casse)."""
    query = (query or "").strip().lower()
    if not query:
        return list(EMOJIS)
    return [item for item in EMOJIS if query in item[1].lower()]


def shortcode_to_emoji(shortcode: str) -> str | None:
    """Résout un shortcode exact (sans les ':') vers son emoji, ou None."""
    return _SHORTCODE_TO_EMOJI.get(shortcode)


def resolve_trailing_shortcode(text: str) -> tuple[str, str] | None:
    """Si `text` se termine par un shortcode complet (ex. "Salut :smile:"),
    retourne (texte_avec_emoji, emoji_inséré). None sinon ou si le
    shortcode est inconnu.

    Utilisé pour la conversion automatique façon Slack/Discord au fil
    de la frappe : dès que l'utilisateur tape le ":" fermant, le
    shortcode reconnu est remplacé par l'emoji correspondant.
    """
    match = _SHORTCODE_RE.search(text)
    if not match:
        return None
    emoji = shortcode_to_emoji(match.group(1))
    if emoji is None:
        return None
    new_text = text[: match.start()] + emoji
    return new_text, emoji
