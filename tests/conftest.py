"""
PATCH 82 — Configuration partagée de la suite de tests.

Le registre système des personnes vit par défaut dans
~/.methodo-og/people.json (voir core.people_registry). Sans précaution,
la suite de tests lirait/écrirait ce vrai fichier utilisateur. Ce
conftest redirige METHODO_OG_PEOPLE_FILE vers un fichier temporaire
propre à chaque test, pour rester hermétique et reproductible.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_people_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("METHODO_OG_PEOPLE_FILE", str(tmp_path / "people.json"))
    yield
