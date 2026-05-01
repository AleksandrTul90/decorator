"""Read financial transactions from different file formats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def read_transactions_from_csv(path: str | Path) -> list[dict[str, Any]]:
    """Read financial transactions from a CSV file.

    Args:
        path: Path to a CSV file with transactions.

    Returns:
        List of dicts with transactions.
    """
    df = pd.read_csv(str(path))
    return df.to_dict(orient="records")


def read_transactions_from_excel(path: str | Path) -> list[dict[str, Any]]:
    """Read financial transactions from an Excel (.xlsx) file.

    Args:
        path: Path to an Excel file with transactions.

    Returns:
        List of dicts with transactions.
    """
    df = pd.read_excel(str(path))
    return df.to_dict(orient="records")
