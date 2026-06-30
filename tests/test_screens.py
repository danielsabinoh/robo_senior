import unittest

from seniorbot.screens import F141CISFilters, F141CISScreen


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def send_keys(self, keys: str) -> None:
        self.events.append(keys)

    def write_text(self, text: str) -> None:
        self.events.append(text)

    def repeat(self, keys: str, count: int) -> None:
        self.events.extend([keys] * count)

    def enter(self) -> None:
        self.events.append("{ENTER}")


class FakeBot:
    def __init__(self) -> None:
        self.keyboard = FakeKeyboard()
        self.focused = False

    def focus_remoteapp(self) -> None:
        self.focused = True


class F141CISScreenTests(unittest.TestCase):
    def test_filter_legacy_filial_alias_returns_invoice_series(self) -> None:
        filters = F141CISFilters(serie_nf="035")

        self.assertEqual(filters.filial, "035")

    def test_filter_cfop_text(self) -> None:
        filters = F141CISFilters(cfops=("5101", "5102"))

        self.assertEqual(filters.cfop_text, '"5101","5102"')

    def test_prepare_grid_uses_mapped_keyboard_route(self) -> None:
        bot = FakeBot()
        screen = F141CISScreen(bot)  # type: ignore[arg-type]

        screen.prepare_grid()

        self.assertTrue(bot.focused)
        self.assertEqual(bot.keyboard.events[0:4], ["{F11}", "F141CIS", "{ENTER}", "{TAB}"])
        self.assertIn("036", bot.keyboard.events)
        self.assertIn('"5101","5102","6101","6102","5910","6910"', bot.keyboard.events)
        self.assertEqual(bot.keyboard.events.count("{UP}"), 2)
        self.assertGreaterEqual(bot.keyboard.events.count("{TAB}"), 77)


if __name__ == "__main__":
    unittest.main()
