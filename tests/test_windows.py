import unittest

from seniorbot.config import SeniorBotConfig
from seniorbot.exceptions import SeniorBotTimeoutError
from seniorbot.windows import WindowManager


class FakeWindow:
    def __init__(self, handle: int, title: str, class_name: str) -> None:
        self.handle = handle
        self._title = title
        self._class_name = class_name
        self.focused = False

    def set_focus(self) -> None:
        self.focused = True

    def window_text(self) -> str:
        return self._title

    def class_name(self) -> str:
        return self._class_name


class FakeDesktop:
    def __init__(self, active: FakeWindow, windows: list[FakeWindow]) -> None:
        self._active = active
        self._windows = windows

    def get_active(self) -> FakeWindow:
        return self._active

    def windows(self) -> list[FakeWindow]:
        return self._windows


class WindowManagerTests(unittest.TestCase):
    def test_focus_remoteapp_can_continue_when_active_handle_differs(self) -> None:
        remoteapp = FakeWindow(
            100,
            "Senior | Gestão Empresarial (ERP) 5.10.4.100 (Remoto)",
            "RAIL_WINDOW",
        )
        intermediate = FakeWindow(200, "Intermediate", "Other")
        manager = WindowManager(
            SeniorBotConfig(focus_timeout=0.01, poll_interval=0.01),
            desktop=FakeDesktop(intermediate, [remoteapp]),
        )

        self.assertIs(manager.focus_remoteapp(), remoteapp)
        self.assertTrue(remoteapp.focused)

    def test_focus_remoteapp_can_require_exact_active_handle(self) -> None:
        remoteapp = FakeWindow(
            100,
            "Senior | Gestão Empresarial (ERP) 5.10.4.100 (Remoto)",
            "RAIL_WINDOW",
        )
        intermediate = FakeWindow(200, "Intermediate", "Other")
        manager = WindowManager(
            SeniorBotConfig(
                focus_timeout=0.01,
                poll_interval=0.01,
                require_focus_confirmation=True,
            ),
            desktop=FakeDesktop(intermediate, [remoteapp]),
        )

        with self.assertRaises(SeniorBotTimeoutError):
            manager.focus_remoteapp()

    def test_find_remoteapp_ignores_printer_tool_and_accepts_generic_remote_app(self) -> None:
        printer = FakeWindow(
            100,
            "Virtual Printer Tool - Select your default local printer (Remoto)",
            "RAIL_WINDOW",
        )
        remoteapp = FakeWindow(200, "Remote App (Remoto)", "RAIL_WINDOW")
        manager = WindowManager(
            SeniorBotConfig(focus_timeout=0.01, poll_interval=0.01),
            desktop=FakeDesktop(remoteapp, [printer, remoteapp]),
        )

        self.assertIs(manager.find_remoteapp(), remoteapp)

    def test_find_remoteapp_prefers_senior_title_over_generic_remote_app(self) -> None:
        generic = FakeWindow(100, "Remote App (Remoto)", "RAIL_WINDOW")
        senior = FakeWindow(
            200,
            "Senior | Gestão Empresarial (ERP) 5.10.4.100 (Remoto)",
            "RAIL_WINDOW",
        )
        manager = WindowManager(
            SeniorBotConfig(focus_timeout=0.01, poll_interval=0.01),
            desktop=FakeDesktop(generic, [generic, senior]),
        )

        self.assertIs(manager.find_remoteapp(), senior)


if __name__ == "__main__":
    unittest.main()
