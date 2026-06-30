"""Synchronization helpers used by automation workflows."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, TypeVar

from seniorbot.exceptions import SeniorBotTimeoutError

T = TypeVar("T")


def wait_until(
    predicate: Callable[[], T | None | bool],
    *,
    timeout: float,
    poll_interval: float = 0.2,
    message: str = "Timed out waiting for condition.",
) -> T:
    """Poll a predicate until it returns a truthy value or a timeout expires."""

    deadline = time.monotonic() + timeout
    last_value: T | None | bool = None

    while time.monotonic() < deadline:
        last_value = predicate()
        if last_value:
            return last_value  # type: ignore[return-value]
        time.sleep(poll_interval)

    last_value = predicate()
    if last_value:
        return last_value  # type: ignore[return-value]

    raise SeniorBotTimeoutError(message)


def wait_for_file(
    path: str | Path,
    *,
    timeout: float,
    poll_interval: float = 0.2,
    stable_seconds: float = 0.5,
) -> Path:
    """Wait until a file exists and its size is stable for a short period."""

    target = Path(path)
    deadline = time.monotonic() + timeout
    last_size: int | None = None
    stable_since: float | None = None

    while time.monotonic() < deadline:
        if target.exists() and target.is_file():
            size = target.stat().st_size
            now = time.monotonic()

            if size == last_size:
                stable_since = stable_since or now
                if now - stable_since >= stable_seconds:
                    return target
            else:
                last_size = size
                stable_since = now

        time.sleep(poll_interval)

    raise SeniorBotTimeoutError(f"Timed out waiting for file: {target}")
