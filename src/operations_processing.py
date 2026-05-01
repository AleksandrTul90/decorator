"""Processing helpers for bank operations."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


def process_bank_search(
    data: list[dict[str, Any]], search: str
) -> list[dict[str, Any]]:
    """Filter operations by a search string in the description field.

    Search is performed with regular expressions (case-insensitive).

    Args:
        data: List of operations dicts.
        search: Search string or regex to find in operation description.

    Returns:
        Filtered list of operations where description matches the search.
    """
    if not search:
        return []

    pattern = re.compile(search, flags=re.IGNORECASE)
    result: list[dict[str, Any]] = []
    for op in data:
        description = op.get("description")
        if isinstance(description, str) and pattern.search(description):
            result.append(op)
    return result


def process_bank_operations(
    data: list[dict[str, Any]], categories: list[str]
) -> dict[str, int]:
    """Count operations by categories based on matching description.

    Args:
        data: List of operations dicts.
        categories: List of category names/keywords to count.

    Returns:
        Dict where keys are category names and values are counts.
    """
    normalized_categories = [c for c in categories if isinstance(c, str) and c]
    if not normalized_categories:
        return {}

    counts: Counter[str] = Counter()
    for op in data:
        description = op.get("description")
        if not isinstance(description, str):
            continue
        lowered = description.lower()
        for category in normalized_categories:
            if category.lower() in lowered:
                counts[category] += 1

    return dict(counts)
