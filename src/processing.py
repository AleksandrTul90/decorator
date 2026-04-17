from __future__ import annotations

from typing import Any


def filter_by_state(
    operations: list[dict[str, Any]], state: str = "EXECUTED"
) -> list[dict[str, Any]]:
    """Return operations whose ``state`` equals the given value."""
    return [op for op in operations if op.get("state") == state]


def sort_by_date(
    operations: list[dict[str, Any]], reverse: bool = True
) -> list[dict[str, Any]]:
    """Return operations sorted by ISO date string in ``date`` field."""
    return sorted(operations, key=lambda op: op.get("date", ""), reverse=reverse)
