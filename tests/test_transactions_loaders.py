from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.transactions_loaders import load_transactions, read_transactions_from_json


def test_read_transactions_from_json_returns_list_of_dicts_only() -> None:
    payload = json.dumps([{"a": 1}, "x", 123, {"b": 2}])

    with patch("builtins.open", mock_open(read_data=payload)):
        result = read_transactions_from_json("any.json")

    assert result == [{"a": 1}, {"b": 2}]


def test_load_transactions_dispatches_csv_and_xlsx() -> None:
    with patch(
        "src.transactions_loaders.read_transactions_from_csv",
        return_value=[{"csv": True}],
    ) as csv_mock:
        assert load_transactions("csv", "a.csv") == [{"csv": True}]
        csv_mock.assert_called_once_with("a.csv")

    with patch(
        "src.transactions_loaders.read_transactions_from_excel",
        return_value=[{"xlsx": True}],
    ) as xlsx_mock:
        assert load_transactions("xlsx", Path("a.xlsx")) == [{"xlsx": True}]
        xlsx_mock.assert_called_once_with(Path("a.xlsx"))


def test_load_transactions_unsupported_source_raises() -> None:
    with pytest.raises(ValueError):
        load_transactions("xml", "a.xml")
