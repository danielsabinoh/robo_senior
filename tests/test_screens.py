import unittest

from seniorbot.screens import F141CISFilters, F141CISScreen


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def send_keys(self, keys: str) -> None:
        self.events.append(keys)

    def write_text(self, text: str) -> None:
        self.events.append(text)

    def ctrl_a(self) -> None:
        self.events.append("ctrl_a")

    def repeat(self, keys: str, count: int) -> None:
        self.events.extend([keys] * count)

    def tab(self) -> None:
        self.events.append("{TAB}")

    def enter(self) -> None:
        self.events.append("{ENTER}")

    def f11(self) -> None:
        self.events.append("{F11}")


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

    def test_prepare_grid_types_screen_date_range_before_series(self) -> None:
        bot = FakeBot()
        screen = F141CISScreen(
            bot,  # type: ignore[arg-type]
            filters=F141CISFilters(
                data_inicial="01/07/2026",
                data_final="02/07/2026",
            ),
        )

        screen.fill_filters()

        self.assertEqual(
            bot.keyboard.events[:14],
            [
                "ctrl_a",
                "01/07/2026",
                "{TAB}",
                "ctrl_a",
                "02/07/2026",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "{TAB}",
                "036",
            ],
        )

    def test_prepare_grid_uses_mapped_keyboard_route(self) -> None:
        bot = FakeBot()
        screen = F141CISScreen(bot)  # type: ignore[arg-type]

        screen.prepare_grid()

        self.assertTrue(bot.focused)
        self.assertEqual(bot.keyboard.events[0:4], ["{F11}", "F141CIS", "{ENTER}", "ctrl_a"])
        self.assertRegex(bot.keyboard.events[4], r"\d{2}/\d{2}/\d{4}")
        self.assertEqual(bot.keyboard.events[5], "{TAB}")
        self.assertIn("036", bot.keyboard.events)
        self.assertIn('"5101","5102","6101","6102","5910","6910"', bot.keyboard.events)
        self.assertEqual(bot.keyboard.events.count("{UP}"), 2)
        self.assertGreaterEqual(bot.keyboard.events.count("{TAB}"), 77)

    def test_open_from_home_can_skip_focus_and_confirm_startup_dialog(self) -> None:
        bot = FakeBot()
        screen = F141CISScreen(
            bot,  # type: ignore[arg-type]
            focus_before_open=False,
            startup_dialog_tabs=4,
        )

        screen.open_from_home()

        self.assertFalse(bot.focused)
        self.assertEqual(
            bot.keyboard.events[:8],
            ["{TAB}", "{TAB}", "{TAB}", "{TAB}", "{ENTER}", "{F11}", "F141CIS", "{ENTER}"],
        )


if __name__ == "__main__":
    unittest.main()
