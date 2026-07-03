"""Remote Desktop startup workflow for Senior automation."""

from __future__ import annotations

import time
import subprocess
from dataclasses import dataclass
from pathlib import Path

from seniorbot.dialogs import Clipboard, TkClipboard
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
    certificate_ready_delay: float = 2.0
    password_ready_delay: float = 2.0
    password_prompt_timeout: float = 5.0
    senior_login_ready_delay: float = 2.0
    use_clipboard_input: bool = False
    senior_run_reuse_last: bool = True
    redirect_drives: bool = True


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
        certificate_ready_delay=float(values.get("RDP_CERTIFICATE_READY_DELAY", "2")),
        password_ready_delay=float(values.get("RDP_PASSWORD_READY_DELAY", "2")),
        password_prompt_timeout=float(values.get("RDP_PASSWORD_PROMPT_TIMEOUT", "5")),
        senior_login_ready_delay=float(values.get("SENIOR_LOGIN_READY_DELAY", "2")),
        use_clipboard_input=values.get("RDP_USE_CLIPBOARD", "false").lower()
        in ("1", "true", "yes", "sim"),
        senior_run_reuse_last=values.get("SENIOR_RUN_REUSE_LAST", "true").lower()
        not in ("0", "false", "no", "nao", "não"),
        redirect_drives=values.get("RDP_REDIRECT_DRIVES", "true").lower()
        not in ("0", "false", "no", "nao", "não"),
    )


class RemoteDesktopLauncher:
    """Keyboard route that opens Senior through a full Remote Desktop session."""

    def __init__(
        self,
        keyboard: Keyboard,
        config: RemoteDesktopConfig,
        *,
        clipboard: Clipboard | None = None,
    ) -> None:
        self.keyboard = keyboard
        self.config = config
        self.clipboard = clipboard or TkClipboard()

    def open_senior(self) -> None:
        """Open RDP, log in, run the Senior shortcut, and log in to Senior."""

        self.open_remote_desktop()
        self.open_senior_shortcut()
        self.login_senior()

    def open_remote_desktop(self) -> None:
        """Open mstsc and connect to the configured host."""

        print("Abrindo Area de Trabalho Remota...")
        self._open_mstsc()
        print("Aguardando conexao da Area de Trabalho Remota...")
        time.sleep(self.config.mstsc_ready_delay)
        time.sleep(self.config.connect_delay)

        password_sent = self._send_rdp_password_if_prompt_visible()

        if self.config.confirm_certificate:
            time.sleep(self.config.certificate_ready_delay)
            print("Confirmando aviso de certificado da Area de Trabalho Remota...")
            self.keyboard.send_keys("{LEFT}")
            self.keyboard.enter()
            time.sleep(self.config.password_ready_delay)

        if not password_sent:
            self._send_rdp_password_if_prompt_visible()

        print("Aguardando a sessao remota carregar...")
        time.sleep(self.config.rdp_load_delay)

    def open_senior_shortcut(self) -> None:
        """Run the Senior shortcut inside the remote session."""

        print("Abrindo atalho do Senior dentro da sessao remota...")
        if self.config.senior_run_reuse_last:
            self._run_last_command()
        else:
            self._run_command(self.config.senior_shortcut_path)
        print("Aguardando tela de login do Senior...")
        time.sleep(self.config.senior_load_delay)

    def login_senior(self) -> None:
        """Fill the Senior login screen."""

        time.sleep(self.config.senior_login_ready_delay)
        print("Enviando login do Senior...")
        self._input_text(self.config.senior_user)
        self.keyboard.tab()
        self._input_text(self.config.senior_password)
        self.keyboard.enter()

    def _run_command(self, command: str) -> None:
        self.keyboard.win_r()
        time.sleep(self.config.run_dialog_delay)
        self._input_text(command)
        self.keyboard.enter()

    def _run_last_command(self) -> None:
        self.keyboard.win_r()
        time.sleep(self.config.run_dialog_delay)
        self.keyboard.tab()
        self.keyboard.enter()

    def _open_mstsc(self) -> None:
        rdp_file = self._write_rdp_file()
        subprocess.Popen(["mstsc.exe", str(rdp_file)])

    def _write_rdp_file(self) -> Path:
        rdp_dir = project_root() / ".local"
        rdp_dir.mkdir(parents=True, exist_ok=True)
        rdp_file = rdp_dir / "seniorbot-rdp.rdp"
        redirect_drives = 1 if self.config.redirect_drives else 0
        drive_store = "*" if self.config.redirect_drives else ""
        rdp_file.write_text(
            "\n".join(
                [
                    f"full address:s:{self.config.rdp_host}",
                    "prompt for credentials:i:1",
                    "redirectclipboard:i:1",
                    f"redirectdrives:i:{redirect_drives}",
                    f"drivestoredirect:s:{drive_store}",
                    "authentication level:i:0",
                    "screen mode id:i:2",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return rdp_file

    def _send_rdp_password_if_prompt_visible(self) -> bool:
        print("Verificando se a tela de senha da Area de Trabalho Remota apareceu...")
        prompt_title = self._wait_for_rdp_password_prompt()
        if prompt_title is None:
            print("Tela de senha nao detectada agora.")
            return False

        print(f"Tela de senha detectada: {prompt_title}")
        print("Enviando senha da Area de Trabalho Remota...")
        self._input_text(self.config.rdp_password)
        self.keyboard.enter()
        return True

    def _input_text(self, text: str) -> None:
        if self.config.use_clipboard_input:
            self.clipboard.set_text(text)
            self.keyboard.ctrl_v()
            return

        self.keyboard.write_text(text)

    def _wait_for_rdp_password_prompt(self) -> str | None:
        deadline = time.monotonic() + self.config.password_prompt_timeout
        while time.monotonic() < deadline:
            prompt_title = self._rdp_password_prompt_title()
            if prompt_title is not None:
                return prompt_title
            time.sleep(0.2)
        return None

    def _rdp_password_prompt_title(self) -> str | None:
        for title in self._visible_window_titles():
            if self._looks_like_rdp_password_prompt(title):
                return title
        return None

    @staticmethod
    def _looks_like_rdp_password_prompt(title: str) -> bool:
        normalized = title.lower()
        return any(
            fragment in normalized
            for fragment in (
                "seguran",
                "security",
                "credencial",
                "credential",
            )
        )

    @staticmethod
    def _visible_window_titles() -> list[str]:
        titles: list[str] = []
        try:
            from pywinauto import Desktop
        except Exception:
            return titles

        for backend in ("win32", "uia"):
            try:
                desktop = Desktop(backend=backend)
                for window in desktop.windows():
                    try:
                        if not window.is_visible():
                            continue
                    except Exception:
                        continue
                    try:
                        title = str(window.window_text())
                    except Exception:
                        continue
                    if title:
                        titles.append(title)
            except Exception:
                continue
        return titles
