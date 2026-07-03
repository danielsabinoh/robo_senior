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

    def ctrl_v(self) -> None:
        self.events.append("ctrl_v")


class FakeClipboard:
    def __init__(self) -> None:
        self.values: list[str] = []

    def set_text(self, text: str) -> None:
        self.values.append(text)


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
                        "RDP_CERTIFICATE_READY_DELAY=7",
                        "RDP_PASSWORD_READY_DELAY=5",
                        "RDP_PASSWORD_PROMPT_TIMEOUT=6",
                        "SENIOR_LOGIN_READY_DELAY=8",
                        "RDP_USE_CLIPBOARD=true",
                        "SENIOR_RUN_REUSE_LAST=false",
                        "RDP_REDIRECT_DRIVES=true",
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
            self.assertEqual(config.certificate_ready_delay, 7)
            self.assertEqual(config.password_ready_delay, 5)
            self.assertEqual(config.password_prompt_timeout, 6)
            self.assertEqual(config.senior_login_ready_delay, 8)
            self.assertTrue(config.use_clipboard_input)
            self.assertFalse(config.senior_run_reuse_last)
            self.assertTrue(config.redirect_drives)

    def test_launcher_sends_rdp_password_before_certificate_when_prompt_appears(self) -> None:
        keyboard = FakeKeyboard()
        config = self._config()
        launcher = PromptAwareRemoteDesktopLauncher(
            keyboard,  # type: ignore[arg-type]
            config,
            prompt_results=["SeguranÃ§a do Windows"],
        )

        with (
            patch("seniorbot.remote_desktop.time.sleep"),
            patch("seniorbot.remote_desktop.subprocess.Popen") as popen_mock,
        ):
            launcher.open_senior()

        popen_args = popen_mock.call_args.args[0]
        self.assertEqual(popen_args[0], "mstsc.exe")
        self.assertTrue(str(popen_args[1]).endswith("seniorbot-rdp.rdp"))
        self.assertEqual(
            keyboard.events,
            [
                "rdp-secret",
                "{ENTER}",
                "{LEFT}",
                "{ENTER}",
                "win_r",
                "{TAB}",
                "{ENTER}",
                "senior-user",
                "{TAB}",
                "senior-secret",
                "{ENTER}",
            ],
        )

    def test_launcher_sends_rdp_password_after_certificate_when_prompt_appears_later(self) -> None:
        keyboard = FakeKeyboard()
        config = self._config()
        launcher = PromptAwareRemoteDesktopLauncher(
            keyboard,  # type: ignore[arg-type]
            config,
            prompt_results=[None, "SeguranÃ§a do Windows"],
        )

        with (
            patch("seniorbot.remote_desktop.time.sleep"),
            patch("seniorbot.remote_desktop.subprocess.Popen") as popen_mock,
        ):
            launcher.open_senior()

        popen_args = popen_mock.call_args.args[0]
        self.assertEqual(popen_args[0], "mstsc.exe")
        self.assertTrue(str(popen_args[1]).endswith("seniorbot-rdp.rdp"))
        self.assertEqual(
            keyboard.events,
            [
                "{LEFT}",
                "{ENTER}",
                "rdp-secret",
                "{ENTER}",
                "win_r",
                "{TAB}",
                "{ENTER}",
                "senior-user",
                "{TAB}",
                "senior-secret",
                "{ENTER}",
            ],
        )

    def test_clipboard_input_can_be_enabled_for_special_text(self) -> None:
        keyboard = FakeKeyboard()
        clipboard = FakeClipboard()
        config = self._config(
            senior_shortcut_path='"C:\\Users\\Public\\Desktop\\Senior ProduÃ§Ã£o\\Sapiens\\GestÃ£o Empresarial (ERP).lnk"',
            use_clipboard_input=True,
            senior_run_reuse_last=False,
        )
        launcher = PromptAwareRemoteDesktopLauncher(
            keyboard,  # type: ignore[arg-type]
            config,
            clipboard=clipboard,
            prompt_results=[None, None],
        )

        with (
            patch("seniorbot.remote_desktop.time.sleep"),
            patch("seniorbot.remote_desktop.subprocess.Popen"),
        ):
            launcher.open_senior()

        self.assertIn(config.senior_shortcut_path, clipboard.values)
        self.assertIn("ctrl_v", keyboard.events)

    def test_rdp_file_enables_local_drive_redirection(self) -> None:
        keyboard = FakeKeyboard()
        launcher = RemoteDesktopLauncher(
            keyboard,  # type: ignore[arg-type]
            self._config(),
        )

        rdp_file = launcher._write_rdp_file()
        content = rdp_file.read_text(encoding="utf-8")

        self.assertIn("full address:s:10.15.1.130", content)
        self.assertIn("redirectdrives:i:1", content)
        self.assertIn("drivestoredirect:s:*", content)

    def test_password_prompt_detection_accepts_windows_security_title(self) -> None:
        self.assertTrue(
            RemoteDesktopLauncher._looks_like_rdp_password_prompt(
                "SeguranÃ§a do Windows"
            )
        )
        self.assertTrue(
            RemoteDesktopLauncher._looks_like_rdp_password_prompt(
                "Windows Security"
            )
        )
        self.assertFalse(
            RemoteDesktopLauncher._looks_like_rdp_password_prompt(
                "Conexao de Area de Trabalho Remota"
            )
        )
        self.assertFalse(
            RemoteDesktopLauncher._looks_like_rdp_password_prompt(
                "Windows PowerShell"
            )
        )

    def _config(
        self,
        *,
        senior_shortcut_path: str = r"\\SRVAPP01\SapiensProducao\Sapiens\Gestao Empresarial.lnk",
        use_clipboard_input: bool = False,
        senior_run_reuse_last: bool = True,
    ) -> RemoteDesktopConfig:
        return RemoteDesktopConfig(
            rdp_host="10.15.1.130",
            rdp_password="rdp-secret",
            senior_shortcut_path=senior_shortcut_path,
            senior_user="senior-user",
            senior_password="senior-secret",
            confirm_certificate=True,
            rdp_load_delay=0,
            senior_load_delay=0,
            run_dialog_delay=0,
            mstsc_ready_delay=0,
            connect_delay=0,
            certificate_ready_delay=0,
            password_ready_delay=0,
            password_prompt_timeout=0,
            senior_login_ready_delay=0,
            use_clipboard_input=use_clipboard_input,
            senior_run_reuse_last=senior_run_reuse_last,
        )


class PromptAwareRemoteDesktopLauncher(RemoteDesktopLauncher):
    def __init__(
        self,
        keyboard: FakeKeyboard,
        config: RemoteDesktopConfig,
        *,
        prompt_results: list[str | None],
        clipboard: FakeClipboard | None = None,
    ) -> None:
        super().__init__(keyboard, config, clipboard=clipboard)  # type: ignore[arg-type]
        self._prompt_results = prompt_results

    def _wait_for_rdp_password_prompt(self) -> str | None:
        if not self._prompt_results:
            return None
        return self._prompt_results.pop(0)


if __name__ == "__main__":
    unittest.main()
