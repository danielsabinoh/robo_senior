"""Configuration objects for SeniorBot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContextMenuMethod = Literal["shift_f10", "apps"]
SaveDialogMode = Literal["native", "remote_keyboard"]
WindowsBackend = Literal["win32", "uia"]


@dataclass(frozen=True, slots=True)
class SeniorBotConfig:
    """Runtime settings for Senior ERP automation."""

    remoteapp_title_pattern: str = r"(Senior|Gestão Empresarial|Remote App).*\(Remoto\)"
    remoteapp_preferred_title_patterns: tuple[str, ...] = (
        r"Senior",
        r"Gestão Empresarial",
    )
    remoteapp_ignored_title_patterns: tuple[str, ...] = (
        r"Virtual Printer Tool",
        r"Select your default local printer",
    )
    remoteapp_class_name: str = "RAIL_WINDOW"
    windows_backend: WindowsBackend = "win32"
    save_dialog_title_pattern: str = r"^(Salvar como|Save As)$"
    overwrite_dialog_title_pattern: str = (
        r"^(Confirmar Salvar como|Confirm Save As|Confirmar substituição)$"
    )
    default_timeout: float = 20.0
    focus_timeout: float = 2.0
    require_focus_confirmation: bool = False
    dialog_timeout: float = 30.0
    file_timeout: float = 60.0
    poll_interval: float = 0.2
    file_stable_seconds: float = 0.5
    create_parent_dirs: bool = True
    confirm_overwrite: bool = True
    focus_before_export: bool = True
    context_menu_method: ContextMenuMethod = "shift_f10"
    grid_focus_keys: tuple[str, ...] = ()
    export_confirm_keys: tuple[str, ...] = ("{ENTER}",)
    save_dialog_mode: SaveDialogMode = "native"
    remote_save_dialog_delay: float = 2.0
    remote_save_focus_keys: tuple[str, ...] = ()
