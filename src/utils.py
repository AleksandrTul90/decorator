from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


def load_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Load a list of transaction dicts from a JSON file.

    Returns an empty list if the file is missing, empty, invalid JSON,
    or does not contain a JSON list at the top level.
    """
    file_path = Path(path)
    try:
        raw = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError:
        return []

    if not raw.strip():
        return []

    try:
        data = json.loads(raw)
    except JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return [item for item in data if isinstance(item, dict)]

