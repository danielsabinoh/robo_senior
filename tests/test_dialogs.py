import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from seniorbot.config import SeniorBotConfig
from seniorbot.dialogs import SaveAsDialog


class FakeWindow:
    handle = 10

    def __init__(self) -> None:
        self.focused = False

    def set_focus(self) -> None:
        self.focused = True

    def window_text(self) -> str:
        return "Salvar como"

    def class_name(self) -> str:
        return "#32770"


class FakeWindowManager:
    def __init__(self) -> None:
        self.dialog = FakeWindow()

    def wait_save_dialog(self) -> FakeWindow:
        return self.dialog

    def wait_overwrite_dialog(self) -> None:
        return None

    def describe(self, window: FakeWindow) -> str:
        return window.window_text()


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def ctrl_a(self) -> None:
        self.events.append("ctrl_a")

    def send_sequence(self, sequence: tuple[str, ...]) -> None:
        self.events.extend(sequence)

    def ctrl_v(self) -> None:
        self.events.append("ctrl_v")

    def enter(self) -> None:
        self.events.append("enter")


class FakeClipboard:
    def __init__(self) -> None:
        self.text = ""

    def set_text(self, text: str) -> None:
        self.text = text


class SaveAsDialogTests(unittest.TestCase):
    def test_save_as_dialog_pastes_full_path(self) -> None:
        with TemporaryDirectory() as directory:
            config = SeniorBotConfig(file_stable_seconds=0.01)
            windows = FakeWindowManager()
            keyboard = FakeKeyboard()
            clipboard = FakeClipboard()
            dialog = SaveAsDialog(
                config,
                windows,  # type: ignore[arg-type]
                keyboard,  # type: ignore[arg-type]
                clipboard=clipboard,
            )
            target = Path(directory) / "folder" / "export.xlsx"

            self.assertEqual(dialog.save_file(target), target)
            self.assertTrue(windows.dialog.focused)
            self.assertEqual(clipboard.text, str(target))
            self.assertEqual(keyboard.events, ["ctrl_a", "ctrl_v", "enter"])
            self.assertTrue(target.parent.exists())

    def test_remote_keyboard_save_does_not_wait_for_native_dialog(self) -> None:
        config = SeniorBotConfig(
            create_parent_dirs=False,
            save_dialog_mode="remote_keyboard",
            remote_save_dialog_delay=0,
            remote_save_focus_keys=("%n",),
        )
        windows = FakeWindowManager()
        keyboard = FakeKeyboard()
        clipboard = FakeClipboard()
        dialog = SaveAsDialog(
            config,
            windows,  # type: ignore[arg-type]
            keyboard,  # type: ignore[arg-type]
            clipboard=clipboard,
        )
        target = Path(r"\\tsclient\C\Temp\export.xlsx")

        self.assertEqual(dialog.save_file(target), target)
        self.assertFalse(windows.dialog.focused)
        self.assertEqual(clipboard.text, str(target))
        self.assertEqual(keyboard.events, ["%n", "ctrl_a", "ctrl_v", "enter"])


if __name__ == "__main__":
    unittest.main()
