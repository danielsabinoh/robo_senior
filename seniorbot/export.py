"""Senior ERP workflow orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from seniorbot.config import ContextMenuMethod, SeniorBotConfig
from seniorbot.dialogs import SaveAsDialog
from seniorbot.exceptions import ExportError
from seniorbot.keyboard import Keyboard, KeyboardDriver, PywinautoKeyboardDriver
from seniorbot.utils import wait_for_file
from seniorbot.windows import WindowManager


class SeniorBot:
    """Facade for automating Senior ERP workflows through RemoteApp."""

    def __init__(
        self,
        config: SeniorBotConfig | None = None,
        *,
        keyboard_driver: KeyboardDriver | None = None,
        keyboard: Keyboard | None = None,
        window_manager: WindowManager | None = None,
        save_dialog: SaveAsDialog | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config or SeniorBotConfig()
        self.logger = logger or logging.getLogger("seniorbot")
        self.keyboard = keyboard or Keyboard(
            keyboard_driver or PywinautoKeyboardDriver(self.logger)
        )
        self.windows = window_manager or WindowManager(self.config, logger=self.logger)
        self.dialogs = save_dialog or SaveAsDialog(
            self.config,
            self.windows,
            self.keyboard,
            logger=self.logger,
        )

    def focus_remoteapp(self) -> None:
        """Bring the Senior RemoteApp window to the foreground."""

        self.windows.focus_remoteapp()
        self.logger.info("RemoteApp focado")

    def focus_grid(self, keys: tuple[str, ...] | None = None) -> None:
        """Move focus to the ERP grid using a configurable keyboard sequence."""

        focus_keys = self.config.grid_focus_keys if keys is None else keys
        if not focus_keys:
            self.logger.info("Sequência de foco da grade vazia")
            return

        self.keyboard.send_sequence(focus_keys)
        self.logger.info("Sequência de foco da grade enviada")

    def open_context_menu(
        self,
        method: ContextMenuMethod | None = None,
    ) -> None:
        """Open the focused grid's context menu."""

        selected_method = method or self.config.context_menu_method
        if selected_method == "shift_f10":
            self.keyboard.shift_f10()
        elif selected_method == "apps":
            self.keyboard.context_menu_key()
        else:
            raise ValueError(f"Unsupported context menu method: {selected_method}")

        self.logger.info("Comando de menu enviado: %s", selected_method)

    def export_xlsx(
        self,
        path: str | Path | None = None,
        *,
        wait_path: str | Path | None = None,
        wait: bool = True,
    ) -> Path | None:
        """Trigger the first context-menu item, optionally saving the XLSX."""

        try:
            self.focus_remoteapp()
            self.focus_grid()
            self.open_context_menu()
            self.logger.info("Exportando XLSX")
            self.keyboard.send_sequence(self.config.export_confirm_keys)

            if path is None:
                return None

            saved_path = self.save_file(path)
            if not wait:
                return saved_path
            return self.wait_file(wait_path or saved_path)
        except Exception as exc:
            if isinstance(exc, ExportError):
                raise
            raise ExportError("XLSX export workflow failed.") from exc

    def save_file(self, path: str | Path) -> Path:
        """Save the current native Save As dialog to a path."""

        saved_path = self.dialogs.save_file(path)
        if self.config.save_dialog_mode == "remote_keyboard":
            self.logger.info("Comando de salvar enviado")
        else:
            self.logger.info("Arquivo salvo")
        return saved_path

    def wait_file(self, path: str | Path) -> Path:
        """Wait for an exported file to exist and stop changing size."""

        return wait_for_file(
            path,
            timeout=self.config.file_timeout,
            poll_interval=self.config.poll_interval,
            stable_seconds=self.config.file_stable_seconds,
        )


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a simple timestamped logger for command-line use."""

    if logging.getLogger().handlers:
        logging.getLogger().setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
