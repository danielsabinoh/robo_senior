"""Keyboard input abstractions."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Protocol

from seniorbot.exceptions import KeyboardInputError


class KeyboardDriver(Protocol):
    """Contract for keyboard backends."""

    def send(self, keys: str) -> None:
        """Send a pywinauto-compatible key sequence."""

    def hotkey(self, *keys: str) -> None:
        """Send a key combination."""

    def write_text(self, text: str) -> None:
        """Type text into the focused target."""


class PywinautoKeyboardDriver:
    """Keyboard backend based on pywinauto's SendInput support."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        try:
            from pywinauto import keyboard as pywinauto_keyboard
        except ImportError as exc:
            raise KeyboardInputError(
                "pywinauto is required for real Windows keyboard input. "
                'Install with: pip install "seniorbot[windows]"'
            ) from exc

        self._keyboard = pywinauto_keyboard

    def send(self, keys: str) -> None:
        """Send a pywinauto key sequence to the focused window."""

        self._logger.debug("Sending keys: %s", keys)
        self._keyboard.send_keys(keys)

    def hotkey(self, *keys: str) -> None:
        """Send a key combination such as shift+f10 or ctrl+v."""

        sequence = _hotkey_to_pywinauto(*keys)
        self.send(sequence)

    def write_text(self, text: str) -> None:
        """Type text literally into the focused window."""

        self.send(text)


class Keyboard:
    """High-level keyboard commands used by Senior automation flows."""

    def __init__(self, driver: KeyboardDriver) -> None:
        self._driver = driver

    def shift_f10(self) -> None:
        """Open the focused control's context menu."""

        self._driver.hotkey("shift", "f10")

    def context_menu_key(self) -> None:
        """Press the dedicated Windows context-menu key."""

        self._driver.send("{VK_APPS}")

    def enter(self) -> None:
        """Press Enter."""

        self._driver.send("{ENTER}")

    def tab(self) -> None:
        """Press Tab."""

        self._driver.send("{TAB}")

    def shift_tab(self) -> None:
        """Press Shift+Tab."""

        self._driver.hotkey("shift", "tab")

    def ctrl_a(self) -> None:
        """Select all text in the current field."""

        self._driver.hotkey("ctrl", "a")

    def ctrl_v(self) -> None:
        """Paste clipboard content into the current field."""

        self._driver.hotkey("ctrl", "v")

    def alt_tab(self) -> None:
        """Switch to the next window."""

        self._driver.hotkey("alt", "tab")

    def write_text(self, text: str) -> None:
        """Type literal text."""

        self._driver.write_text(text)

    def send_keys(self, keys: str) -> None:
        """Send a raw pywinauto key sequence."""

        self._driver.send(keys)

    def send_sequence(self, sequence: Iterable[str]) -> None:
        """Send a sequence of raw pywinauto key strings."""

        for keys in sequence:
            self.send_keys(keys)

    def repeat(self, keys: str, count: int) -> None:
        """Send the same key sequence a fixed number of times."""

        for _ in range(count):
            self.send_keys(keys)


def _hotkey_to_pywinauto(*keys: str) -> str:
    modifiers = {
        "shift": "+",
        "ctrl": "^",
        "control": "^",
        "alt": "%",
    }
    special_keys = {
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
        "tab",
        "enter",
    }

    prefix = ""
    regular: list[str] = []

    for key in keys:
        normalized = key.lower()
        if normalized in modifiers:
            prefix += modifiers[normalized]
        elif normalized in special_keys:
            regular.append(f"{{{normalized.upper()}}}")
        else:
            regular.append(normalized)

    return prefix + "".join(regular)
