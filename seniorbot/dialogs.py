"""Automation for native Windows dialogs."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Protocol

from seniorbot.config import SeniorBotConfig
from seniorbot.exceptions import DialogError
from seniorbot.keyboard import Keyboard
from seniorbot.windows import WindowManager


class Clipboard(Protocol):
    """Contract for clipboard implementations."""

    def set_text(self, text: str) -> None:
        """Place text on the system clipboard."""


class TkClipboard:
    """Clipboard implementation backed by the tkinter standard library."""

    def set_text(self, text: str) -> None:
        """Place text on the Windows clipboard."""

        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
        finally:
            root.destroy()


class SaveAsDialog:
    """Keyboard-first automation for the Windows Save As dialog."""

    def __init__(
        self,
        config: SeniorBotConfig,
        window_manager: WindowManager,
        keyboard: Keyboard,
        *,
        clipboard: Clipboard | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._window_manager = window_manager
        self._keyboard = keyboard
        self._clipboard = clipboard or TkClipboard()
        self._logger = logger or logging.getLogger(__name__)

    def save_file(self, path: str | Path) -> Path:
        """Save the current dialog to a full file path."""

        target = Path(path)
        if self._config.create_parent_dirs:
            target.parent.mkdir(parents=True, exist_ok=True)

        if self._config.save_dialog_mode == "remote_keyboard":
            return self._save_remote_keyboard_only(target)

        dialog = self._window_manager.wait_save_dialog()
        self._logger.debug("Save dialog focused: %s", self._window_manager.describe(dialog))
        dialog.set_focus()

        try:
            self._clipboard.set_text(str(target))
            self._keyboard.ctrl_a()
            self._keyboard.ctrl_v()
            self._keyboard.enter()
            self._confirm_overwrite_if_needed()
        except Exception as exc:
            raise DialogError(f"Could not save file through Save As dialog: {target}") from exc

        return target

    def _save_remote_keyboard_only(self, target: Path) -> Path:
        """Save through a RemoteApp dialog that is invisible to local UIA."""

        try:
            time.sleep(self._config.remote_save_dialog_delay)
            self._clipboard.set_text(str(target))
            self._keyboard.send_sequence(self._config.remote_save_focus_keys)
            self._keyboard.ctrl_a()
            self._keyboard.ctrl_v()
            self._keyboard.enter()
        except Exception as exc:
            raise DialogError(
                f"Could not save file through RemoteApp Save As dialog: {target}"
            ) from exc

        return target

    def _confirm_overwrite_if_needed(self) -> None:
        if not self._config.confirm_overwrite:
            return

        overwrite_dialog = self._window_manager.wait_overwrite_dialog()
        if overwrite_dialog is None:
            return

        self._logger.debug(
            "Confirming overwrite dialog: %s",
            self._window_manager.describe(overwrite_dialog),
        )
        overwrite_dialog.set_focus()
        self._keyboard.enter()
