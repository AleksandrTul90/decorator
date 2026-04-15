"""Logging decorator implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar, overload

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class _LogConfig:
    filename: str | None


def _format_call(func_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    return f"{func_name} args={args} kwargs={kwargs}"


def _write_line(config: _LogConfig, line: str) -> None:
    if config.filename:
        with open(config.filename, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    else:
        print(line)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@overload
def log(func: Callable[P, R], /) -> Callable[P, R]: ...


@overload
def log(
    *, filename: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def log(
    func: Callable[P, R] | None = None, /, *, filename: str | None = None
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that logs function calls/results to console or a file.

    Args:
        func: Function to wrap when decorator is used without parentheses: ``@log``.
        filename: If provided, logs are appended to this file; otherwise printed to
            console.

    Returns:
        Wrapped function (or a decorator factory when called with arguments).
    """

    config = _LogConfig(filename=filename)

    def decorator(inner: Callable[P, R]) -> Callable[P, R]:
        @wraps(inner)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_ts = _now_iso()
            call_details = _format_call(inner.__name__, args, kwargs)
            _write_line(config, f"[{start_ts}] CALL {call_details}")
            try:
                result = inner(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - must log any exception
                err_ts = _now_iso()
                _write_line(
                    config,
                    f"[{err_ts}] ERROR {inner.__name__} {type(exc).__name__} "
                    f"{call_details}",
                )
                raise
            end_ts = _now_iso()
            _write_line(config, f"[{end_ts}] RESULT {inner.__name__} -> {result!r}")
            return result

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
