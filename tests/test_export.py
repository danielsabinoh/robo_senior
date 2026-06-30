import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from seniorbot.config import SeniorBotConfig
from seniorbot.export import SeniorBot


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def send_sequence(self, sequence: tuple[str, ...]) -> None:
        self.events.extend(sequence)

    def shift_f10(self) -> None:
        self.events.append("shift_f10")

    def context_menu_key(self) -> None:
        self.events.append("context_menu_key")

    def enter(self) -> None:
        self.events.append("enter")


class FakeWindowManager:
    def __init__(self) -> None:
        self.focused = False

    def focus_remoteapp(self) -> None:
        self.focused = True


class FakeSaveDialog:
    def __init__(self, *, write_files: bool = True) -> None:
        self.saved: Path | None = None
        self.write_files = write_files

    def save_file(self, path: str | Path) -> Path:
        self.saved = Path(path)
        if self.write_files:
            self.saved.write_bytes(b"xlsx")
        return self.saved


class SeniorBotExportTests(unittest.TestCase):
    def test_export_xlsx_runs_keyboard_first_flow(self) -> None:
        with TemporaryDirectory() as directory:
            keyboard = FakeKeyboard()
            windows = FakeWindowManager()
            save_dialog = FakeSaveDialog()
            bot = SeniorBot(
                SeniorBotConfig(poll_interval=0.01, file_stable_seconds=0.01),
                keyboard=keyboard,  # type: ignore[arg-type]
                window_manager=windows,  # type: ignore[arg-type]
                save_dialog=save_dialog,  # type: ignore[arg-type]
            )
            target = Path(directory) / "export.xlsx"

            self.assertEqual(bot.export_xlsx(target), target)
            self.assertTrue(windows.focused)
            self.assertEqual(keyboard.events, ["shift_f10", "{ENTER}"])
            self.assertEqual(save_dialog.saved, target)

    def test_export_xlsx_can_use_configured_grid_focus_and_apps_key(self) -> None:
        with TemporaryDirectory() as directory:
            keyboard = FakeKeyboard()
            windows = FakeWindowManager()
            save_dialog = FakeSaveDialog()
            bot = SeniorBot(
                SeniorBotConfig(
                    context_menu_method="apps",
                    grid_focus_keys=("{TAB}", "{TAB}"),
                    poll_interval=0.01,
                    file_stable_seconds=0.01,
                ),
                keyboard=keyboard,  # type: ignore[arg-type]
                window_manager=windows,  # type: ignore[arg-type]
                save_dialog=save_dialog,  # type: ignore[arg-type]
            )
            target = Path(directory) / "export.xlsx"

            self.assertEqual(bot.export_xlsx(target), target)
            self.assertEqual(
                keyboard.events,
                ["{TAB}", "{TAB}", "context_menu_key", "{ENTER}"],
            )

    def test_export_xlsx_can_customize_menu_confirmation_keys(self) -> None:
        with TemporaryDirectory() as directory:
            keyboard = FakeKeyboard()
            windows = FakeWindowManager()
            save_dialog = FakeSaveDialog()
            bot = SeniorBot(
                SeniorBotConfig(
                    export_confirm_keys=("{HOME}", "{ENTER}"),
                    poll_interval=0.01,
                    file_stable_seconds=0.01,
                ),
                keyboard=keyboard,  # type: ignore[arg-type]
                window_manager=windows,  # type: ignore[arg-type]
                save_dialog=save_dialog,  # type: ignore[arg-type]
            )
            target = Path(directory) / "export.xlsx"

            self.assertEqual(bot.export_xlsx(target), target)
            self.assertEqual(keyboard.events, ["shift_f10", "{HOME}", "{ENTER}"])

    def test_export_xlsx_can_wait_for_a_different_local_path(self) -> None:
        with TemporaryDirectory() as directory:
            keyboard = FakeKeyboard()
            windows = FakeWindowManager()
            save_dialog = FakeSaveDialog(write_files=False)
            bot = SeniorBot(
                SeniorBotConfig(poll_interval=0.01, file_stable_seconds=0.01),
                keyboard=keyboard,  # type: ignore[arg-type]
                window_manager=windows,  # type: ignore[arg-type]
                save_dialog=save_dialog,  # type: ignore[arg-type]
            )
            remote_target = Path(r"\\tsclient\C\Temp\export.xlsx")
            local_target = Path(directory) / "export.xlsx"
            local_target.write_bytes(b"xlsx")

            self.assertEqual(
                bot.export_xlsx(remote_target, wait_path=local_target),
                local_target,
            )
            self.assertEqual(save_dialog.saved, remote_target)

    def test_export_xlsx_can_skip_file_wait_for_remote_only_path(self) -> None:
        keyboard = FakeKeyboard()
        windows = FakeWindowManager()
        save_dialog = FakeSaveDialog(write_files=False)
        bot = SeniorBot(
            SeniorBotConfig(poll_interval=0.01, file_stable_seconds=0.01),
            keyboard=keyboard,  # type: ignore[arg-type]
            window_manager=windows,  # type: ignore[arg-type]
            save_dialog=save_dialog,  # type: ignore[arg-type]
        )
        remote_target = Path(r"C:\Temp\export.xlsx")

        self.assertEqual(bot.export_xlsx(remote_target, wait=False), remote_target)
        self.assertEqual(save_dialog.saved, remote_target)


if __name__ == "__main__":
    unittest.main()
