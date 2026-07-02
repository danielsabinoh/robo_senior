import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from seniorbot.remote_desktop import (
    RemoteDesktopConfig,
    RemoteDesktopLauncher,
    load_remote_desktop_config,
)


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def win_r(self) -> None:
        self.events.append("win_r")

    def write_text(self, text: str) -> None:
        self.events.append(text)

    def enter(self) -> None:
        self.events.append("{ENTER}")

    def tab(self) -> None:
        self.events.append("{TAB}")

    def send_keys(self, keys: str) -> None:
        self.events.append(keys)


class RemoteDesktopTests(unittest.TestCase):
    def test_load_remote_desktop_config_from_env_file(self) -> None:
        with TemporaryDirectory() as directory:
            env_path = Path(directory) / "remoteapp.env"
            env_path.write_text(
                "\n".join(
                    [
                        "RDP_HOST=10.15.1.130",
                        "RDP_PASSWORD=rdp-secret",
                        r"SENIOR_SHORTCUT_PATH=\\SRVAPP01\SapiensProducao\Sapiens\Gestao Empresarial.lnk",
                        "SENIOR_USER=senior-user",
                        "SENIOR_PASSWORD=senior-secret",
                        "RDP_LOAD_DELAY=1",
                        "SENIOR_LOAD_DELAY=2",
                        "MSTSC_READY_DELAY=4",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_remote_desktop_config(env_path)

            self.assertEqual(config.rdp_host, "10.15.1.130")
            self.assertEqual(config.rdp_password, "rdp-secret")
            self.assertEqual(config.senior_user, "senior-user")
            self.assertEqual(config.rdp_load_delay, 1)
            self.assertEqual(config.senior_load_delay, 2)
            self.assertEqual(config.mstsc_ready_delay, 4)

    def test_launcher_runs_rdp_shortcut_and_senior_login_route(self) -> None:
        keyboard = FakeKeyboard()
        config = RemoteDesktopConfig(
            rdp_host="10.15.1.130",
            rdp_password="rdp-secret",
            senior_shortcut_path=r"\\SRVAPP01\SapiensProducao\Sapiens\Gestao Empresarial.lnk",
            senior_user="senior-user",
            senior_password="senior-secret",
            confirm_certificate=True,
            rdp_load_delay=0,
            senior_load_delay=0,
            run_dialog_delay=0,
            mstsc_ready_delay=0,
            connect_delay=0,
        )
        launcher = RemoteDesktopLauncher(keyboard, config)  # type: ignore[arg-type]

        with patch("seniorbot.remote_desktop.time.sleep"):
            launcher.open_senior()

        self.assertEqual(
            keyboard.events,
            [
                "win_r",
                "mstsc",
                "{ENTER}",
                "10.15.1.130",
                "{ENTER}",
                "rdp-secret",
                "{ENTER}",
                "{LEFT}",
                "{ENTER}",
                "win_r",
                r"\\SRVAPP01\SapiensProducao\Sapiens\Gestao Empresarial.lnk",
                "{ENTER}",
                "senior-user",
                "{TAB}",
                "senior-secret",
                "{ENTER}",
            ],
        )


if __name__ == "__main__":
    unittest.main()
