"""Remote Desktop startup workflow for Senior automation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from seniorbot.keyboard import Keyboard
from seniorbot.logging import project_root


@dataclass(frozen=True, slots=True)
class RemoteDesktopConfig:
    """Local-only settings for opening Senior through Remote Desktop."""

    rdp_host: str
    rdp_password: str
    senior_shortcut_path: str
    senior_user: str
    senior_password: str
    confirm_certificate: bool = True
    rdp_load_delay: float = 20.0
    senior_load_delay: float = 20.0
    run_dialog_delay: float = 1.0
    mstsc_ready_delay: float = 3.0
    connect_delay: float = 3.0


def default_remote_desktop_env_path() -> Path:
    """Return the local env file path used for RDP credentials."""

    return project_root() / ".local" / "remoteapp.env"


def load_env_file(path: str | Path) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a local env file."""

    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais nao encontrado: {target}. "
            "Crie esse arquivo local antes de usar --open-rdp."
        )

    values: dict[str, str] = {}
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_remote_desktop_config(path: str | Path | None = None) -> RemoteDesktopConfig:
    """Load Remote Desktop settings from the local env file."""

    env_path = Path(path) if path is not None else default_remote_desktop_env_path()
    values = load_env_file(env_path)
    required = (
        "RDP_HOST",
        "RDP_PASSWORD",
        "SENIOR_SHORTCUT_PATH",
        "SENIOR_USER",
        "SENIOR_PASSWORD",
    )
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ValueError(
            "Credenciais incompletas em "
            f"{env_path}: faltando {', '.join(missing)}."
        )

    return RemoteDesktopConfig(
        rdp_host=values["RDP_HOST"],
        rdp_password=values["RDP_PASSWORD"],
        senior_shortcut_path=values["SENIOR_SHORTCUT_PATH"],
        senior_user=values["SENIOR_USER"],
        senior_password=values["SENIOR_PASSWORD"],
        confirm_certificate=values.get("RDP_CONFIRM_CERTIFICATE", "true").lower()
        not in ("0", "false", "no", "nao", "não"),
        rdp_load_delay=float(values.get("RDP_LOAD_DELAY", "20")),
        senior_load_delay=float(values.get("SENIOR_LOAD_DELAY", "20")),
        run_dialog_delay=float(values.get("RUN_DIALOG_DELAY", "1")),
        mstsc_ready_delay=float(values.get("MSTSC_READY_DELAY", "3")),
        connect_delay=float(values.get("RDP_CONNECT_DELAY", "3")),
    )


class RemoteDesktopLauncher:
    """Keyboard route that opens Senior through a full Remote Desktop session."""

    def __init__(self, keyboard: Keyboard, config: RemoteDesktopConfig) -> None:
        self.keyboard = keyboard
        self.config = config

    def open_senior(self) -> None:
        """Open RDP, log in, run the Senior shortcut, and log in to Senior."""

        self.open_remote_desktop()
        self.open_senior_shortcut()
        self.login_senior()

    def open_remote_desktop(self) -> None:
        """Open mstsc and connect to the configured host."""

        print("Abrindo Area de Trabalho Remota...")
        self._run_command("mstsc")
        print("Aguardando a janela da Area de Trabalho Remota ficar pronta...")
        time.sleep(self.config.mstsc_ready_delay)
        self.keyboard.write_text(self.config.rdp_host)
        self.keyboard.enter()
        time.sleep(self.config.connect_delay)

        print("Enviando senha da Area de Trabalho Remota...")
        self.keyboard.write_text(self.config.rdp_password)
        self.keyboard.enter()

        if self.config.confirm_certificate:
            time.sleep(1)
            self.keyboard.send_keys("{LEFT}")
            self.keyboard.enter()

        print("Aguardando a sessao remota carregar...")
        time.sleep(self.config.rdp_load_delay)

    def open_senior_shortcut(self) -> None:
        """Run the Senior shortcut inside the remote session."""

        print("Abrindo atalho do Senior dentro da sessao remota...")
        self._run_command(self.config.senior_shortcut_path)
        print("Aguardando tela de login do Senior...")
        time.sleep(self.config.senior_load_delay)

    def login_senior(self) -> None:
        """Fill the Senior login screen."""

        print("Enviando login do Senior...")
        self.keyboard.write_text(self.config.senior_user)
        self.keyboard.tab()
        self.keyboard.write_text(self.config.senior_password)
        self.keyboard.enter()

    def _run_command(self, command: str) -> None:
        self.keyboard.win_r()
        time.sleep(self.config.run_dialog_delay)
        self.keyboard.write_text(command)
        self.keyboard.enter()
