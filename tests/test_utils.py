from __future__ import annotations

from pathlib import Path

from src.utils import load_transactions


def test_load_transactions_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    assert load_transactions(missing) == []


def test_load_transactions_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "ops.json"
    p.write_text("", encoding="utf-8")
    assert load_transactions(p) == []


def test_load_transactions_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "ops.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_transactions(p) == []


def test_load_transactions_not_a_list(tmp_path: Path) -> None:
    p = tmp_path / "ops.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert load_transactions(p) == []


def test_load_transactions_list_of_dicts(tmp_path: Path) -> None:
    p = tmp_path / "ops.json"
    p.write_text('[{"id": 1}, {"id": 2}]', encoding="utf-8")
    assert load_transactions(p) == [{"id": 1}, {"id": 2}]


def test_load_transactions_filters_non_dict_entries(tmp_path: Path) -> None:
    p = tmp_path / "ops.json"
    p.write_text('[{"id": 1}, 2, "x", {"id": 3}]', encoding="utf-8")
    assert load_transactions(p) == [{"id": 1}, {"id": 3}]
