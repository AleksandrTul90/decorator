from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.transactions_io import read_transactions_from_csv, read_transactions_from_excel


def test_read_transactions_from_csv_uses_pandas_and_returns_records() -> None:
    df = pd.DataFrame(
        [
            {"id": 1, "amount": 100.5, "currency": "RUB"},
            {"id": 2, "amount": -10, "currency": "USD"},
        ]
    )

    with patch("src.transactions_io.pd.read_csv", return_value=df) as mocked:
        result = read_transactions_from_csv("any.csv")

    mocked.assert_called_once_with("any.csv")
    assert result == [
        {"id": 1, "amount": 100.5, "currency": "RUB"},
        {"id": 2, "amount": -10.0, "currency": "USD"},
    ]


def test_read_transactions_from_excel_uses_pandas_and_returns_records() -> None:
    df = pd.DataFrame([{"operation_id": "abc", "status": "EXECUTED"}])

    with patch("src.transactions_io.pd.read_excel", return_value=df) as mocked:
        result = read_transactions_from_excel(Path("any.xlsx"))

    mocked.assert_called_once_with("any.xlsx")
    assert result == [{"operation_id": "abc", "status": "EXECUTED"}]
