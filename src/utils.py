from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Any

_LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.FileHandler(_LOGS_DIR / "utils.log", mode="w", encoding="utf-8")
    _formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


def load_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Load a list of transaction dicts from a JSON file.

    Returns an empty list if the file is missing, empty, invalid JSON,
    or does not contain a JSON list at the top level.
    """
    file_path = Path(path)
    try:
        raw = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Transactions file not found: %s", file_path)
        return []
    except OSError:
        logger.error("Failed to read transactions file: %s", file_path)
        return []

    if not raw.strip():
        logger.error("Transactions file is empty: %s", file_path)
        return []

    try:
        data = json.loads(raw)
    except JSONDecodeError:
        logger.error("Invalid JSON in transactions file: %s", file_path)
        return []

    if not isinstance(data, list):
        logger.error("Transactions JSON top-level is not a list: %s", file_path)
        return []

    out = [item for item in data if isinstance(item, dict)]
    logger.debug("Loaded %d transactions from %s", len(out), file_path)
    return out
