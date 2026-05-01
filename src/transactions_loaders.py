"""Load transactions from supported file formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.transactions_io import read_transactions_from_csv, read_transactions_from_excel


def read_transactions_from_json(path: str | Path) -> list[dict[str, Any]]:
    """Read financial transactions from a JSON file.

    Expects a JSON array of objects.

    Args:
        path: Path to JSON file.

    Returns:
        List of dicts with transactions.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def load_transactions(source: str, path: str | Path) -> list[dict[str, Any]]:
    """Load transactions from one of the supported sources.

    Args:
        source: One of: json, csv, xlsx.
        path: Path to the source file.

    Returns:
        List of dicts with transactions.
    """
    source_normalized = source.strip().lower()
    if source_normalized == "json":
        return read_transactions_from_json(path)
    if source_normalized == "csv":
        return read_transactions_from_csv(path)
    if source_normalized in {"xlsx", "excel"}:
        return read_transactions_from_excel(path)
    raise ValueError(f"Unsupported source: {source}")
