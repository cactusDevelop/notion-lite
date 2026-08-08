from __future__ import annotations

from ui.command_registry import COMMANDS, filter_commands


def test_filter_commands_empty_query_returns_all():
    assert filter_commands("") == COMMANDS


def test_filter_commands_by_keyword():
    results = filter_commands("tableau")
    ids = [c["id"] for c in results]
    assert "table" in ids
    assert "simple_table" in ids
    assert "text" not in ids


def test_filter_commands_by_label_case_insensitive():
    results = filter_commands("GANTT")
    assert [c["id"] for c in results] == ["gantt"]


def test_filter_commands_no_match():
    assert filter_commands("xyz123") == []
