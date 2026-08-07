from __future__ import annotations

from core.duration import format_duration, parse_duration_text, to_hours


def test_format_duration_singular_plural():
    assert format_duration({"amount": 1, "unit": "jours"}) == "1 jour"
    assert format_duration({"amount": 2, "unit": "jours"}) == "2 jours"
    assert format_duration({"amount": 1, "unit": "semaines"}) == "1 semaine"
    assert format_duration({"amount": 3, "unit": "heures"}) == "3 heures"
    assert format_duration({"amount": 1, "unit": "heures"}) == "1 heure"


def test_parse_duration_text_variants():
    assert parse_duration_text("2 semaines") == {"amount": 2, "unit": "semaines"}
    assert parse_duration_text("1 jour") == {"amount": 1, "unit": "jours"}
    assert parse_duration_text("3h") == {"amount": 3, "unit": "heures"}
    assert parse_duration_text("1j") == {"amount": 1, "unit": "jours"}
    assert parse_duration_text("5sem") == {"amount": 5, "unit": "semaines"}


def test_parse_duration_text_invalid():
    assert parse_duration_text("") is None
    assert parse_duration_text("bonjour") is None
    assert parse_duration_text("2 mois") is None


def test_to_hours_conversion():
    assert to_hours({"amount": 3, "unit": "heures"}) == 3
    assert to_hours({"amount": 1, "unit": "jours"}) == 24
    assert to_hours({"amount": 2, "unit": "semaines"}) == 336
