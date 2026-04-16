from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Any, Callable


def log(
    func: Callable[..., Any] | None = None, /, *, filename: str | None = None
) -> Callable[..., Any]:
    def decorator(inner: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(inner)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_line = (
                f"{datetime.now()} - {inner.__name__} - args: {args}, kwargs: {kwargs}"
            )
            if filename:
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(start_line + "\n")
            else:
                print(start_line)

            try:
                result = inner(*args, **kwargs)
            except Exception as exc:
                err_line = (
                    f"{datetime.now()} - {inner.__name__} - error: {type(exc).__name__}"
                )
                if filename:
                    with open(filename, "a", encoding="utf-8") as f:
                        f.write(err_line + "\n")
                else:
                    print(err_line)
                raise

            result_line = f"{datetime.now()} - {inner.__name__} - result: {result!r}"
            if filename:
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(result_line + "\n")
            else:
                print(result_line)
            return result

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator

