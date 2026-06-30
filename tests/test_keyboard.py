import unittest

from seniorbot.keyboard import Keyboard, _hotkey_to_pywinauto


class FakeDriver:
    def __init__(self) -> None:
        self.events: list[str] = []

    def send(self, keys: str) -> None:
        self.events.append(keys)

    def hotkey(self, *keys: str) -> None:
        self.events.append(_hotkey_to_pywinauto(*keys))

    def write_text(self, text: str) -> None:
        self.events.append(text)


class KeyboardTests(unittest.TestCase):
    def test_hotkey_to_pywinauto(self) -> None:
        self.assertEqual(_hotkey_to_pywinauto("shift", "f10"), "+{F10}")
        self.assertEqual(_hotkey_to_pywinauto("ctrl", "v"), "^v")
        self.assertEqual(_hotkey_to_pywinauto("alt", "tab"), "%{TAB}")

    def test_keyboard_helpers_send_expected_sequences(self) -> None:
        driver = FakeDriver()
        keyboard = Keyboard(driver)

        keyboard.shift_f10()
        keyboard.context_menu_key()
        keyboard.enter()
        keyboard.ctrl_a()
        keyboard.ctrl_v()

        self.assertEqual(driver.events, ["+{F10}", "{VK_APPS}", "{ENTER}", "^a", "^v"])


if __name__ == "__main__":
    unittest.main()
