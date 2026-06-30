"""Top-level Windows automation helpers."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from seniorbot.config import SeniorBotConfig
from seniorbot.exceptions import SeniorBotTimeoutError, WindowNotFoundError
from seniorbot.utils import wait_until


@dataclass(frozen=True, slots=True)
class WindowInfo:
    """Small immutable description of a top-level window."""

    handle: int
    title: str
    class_name: str


class WindowManager:
    """Find, focus, and wait for top-level Windows windows."""

    def __init__(
        self,
        config: SeniorBotConfig,
        *,
        desktop: Any | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._desktop = desktop or self._create_desktop()

    def focus_remoteapp(self) -> Any:
        """Focus the Senior RemoteApp window and wait until it is active."""

        window = self.find_remoteapp()
        self._logger.debug("Focusing RemoteApp: %s", self.describe(window))
        window.set_focus()
        handle = self._handle(window)

        try:
            wait_until(
                lambda: self.active_handle() == handle,
                timeout=self._config.focus_timeout,
                poll_interval=self._config.poll_interval,
                message="RemoteApp window did not become active.",
            )
        except SeniorBotTimeoutError:
            if self._config.require_focus_confirmation:
                raise
            self._logger.warning(
                "RemoteApp focus was requested, but Windows did not report "
                "the RAIL_WINDOW handle as active. Continuing because "
                "RemoteApp can expose an intermediate active handle."
            )
        return window

    def find_remoteapp(self) -> Any:
        """Find the Senior RemoteApp top-level RAIL window."""

        title_re = re.compile(self._config.remoteapp_title_pattern)
        preferred_res = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self._config.remoteapp_preferred_title_patterns
        ]
        ignored_res = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self._config.remoteapp_ignored_title_patterns
        ]

        def locate() -> Any | None:
            candidates: list[Any] = []
            for window in self._windows():
                if self._class_name(window) != self._config.remoteapp_class_name:
                    continue
                title = self._title(window)
                if any(pattern.search(title) for pattern in ignored_res):
                    continue
                if title_re.search(title):
                    candidates.append(window)
            return self._best_remoteapp_candidate(candidates, preferred_res)

        try:
            return wait_until(
                locate,
                timeout=self._config.default_timeout,
                poll_interval=self._config.poll_interval,
                message="Senior RemoteApp window was not found.",
            )
        except Exception as exc:
            if isinstance(exc, WindowNotFoundError):
                raise
            raise WindowNotFoundError("Senior RemoteApp window was not found.") from exc

    def _best_remoteapp_candidate(
        self,
        candidates: list[Any],
        preferred_res: list[re.Pattern[str]],
    ) -> Any | None:
        if not candidates:
            return None

        for window in candidates:
            title = self._title(window)
            if any(pattern.search(title) for pattern in preferred_res):
                return window

        return candidates[0]

    def wait_save_dialog(self) -> Any:
        """Wait until the native Save As dialog appears."""

        return self.wait_window(
            self._config.save_dialog_title_pattern,
            timeout=self._config.dialog_timeout,
            message="Save As dialog was not found.",
        )

    def wait_overwrite_dialog(self, *, timeout: float = 2.0) -> Any | None:
        """Wait briefly for an overwrite confirmation dialog."""

        try:
            return self.wait_window(
                self._config.overwrite_dialog_title_pattern,
                timeout=timeout,
                message="Overwrite dialog was not found.",
            )
        except WindowNotFoundError:
            return None

    def wait_window(self, title_pattern: str, *, timeout: float, message: str) -> Any:
        """Wait for a top-level window whose title matches a regex."""

        title_re = re.compile(title_pattern)

        def locate() -> Any | None:
            for window in self._windows():
                if title_re.search(self._title(window)):
                    return window
            return None

        try:
            return wait_until(
                locate,
                timeout=timeout,
                poll_interval=self._config.poll_interval,
                message=message,
            )
        except Exception as exc:
            raise WindowNotFoundError(message) from exc

    def active_handle(self) -> int | None:
        """Return the handle of the currently active top-level window."""

        try:
            active = self._desktop.get_active()
        except Exception:
            return None
        return self._handle(active)

    def describe(self, window: Any) -> WindowInfo:
        """Return a stable summary for logging and diagnostics."""

        return WindowInfo(
            handle=self._handle(window),
            title=self._title(window),
            class_name=self._class_name(window),
        )

    def _windows(self) -> list[Any]:
        return list(self._desktop.windows())

    @staticmethod
    def _handle(window: Any) -> int:
        return int(getattr(window, "handle", 0))

    @staticmethod
    def _title(window: Any) -> str:
        return str(window.window_text())

    @staticmethod
    def _class_name(window: Any) -> str:
        return str(window.class_name())

    @staticmethod
    def _create_desktop() -> Any:
        try:
            from pywinauto import Desktop
        except ImportError as exc:
            raise WindowNotFoundError(
                "pywinauto is required for real Windows window discovery. "
                'Install with: pip install "seniorbot[windows]"'
            ) from exc
        return Desktop(backend="uia")
