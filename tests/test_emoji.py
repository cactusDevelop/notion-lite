from __future__ import annotations

from core.emoji_data import EMOJIS, resolve_trailing_shortcode, search_emojis, shortcode_to_emoji


def test_search_emojis_empty_query_returns_all():
    assert search_emojis("") == EMOJIS


def test_search_emojis_filters_by_shortcode_substring():
    results = search_emojis("smile")
    codes = [c for _, c, _ in results]
    assert "smile" in codes
    assert "slight_smile" in codes


def test_shortcode_to_emoji_known_and_unknown():
    assert shortcode_to_emoji("fire") == "🔥"
    assert shortcode_to_emoji("inconnu_xyz") is None


def test_resolve_trailing_shortcode_converts():
    result = resolve_trailing_shortcode("Bravo :tada:")
    assert result == ("Bravo 🎉", "🎉")


def test_resolve_trailing_shortcode_no_match_returns_none():
    assert resolve_trailing_shortcode("Bonjour") is None
    assert resolve_trailing_shortcode("Bonjour :inconnuxyz:") is None
    assert resolve_trailing_shortcode("") is None


def test_resolve_trailing_shortcode_only_matches_at_end():
    # Un shortcode non terminé (curseur au milieu) n'est pas résolu.
    assert resolve_trailing_shortcode(":smile: bonjour") is None
