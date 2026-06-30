import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from seniorbot.exceptions import SeniorBotTimeoutError
from seniorbot.utils import wait_for_file, wait_until


class UtilsTests(unittest.TestCase):
    def test_wait_until_returns_truthy_value(self) -> None:
        attempts = {"count": 0}

        def predicate() -> str | None:
            attempts["count"] += 1
            return "ready" if attempts["count"] >= 2 else None

        self.assertEqual(wait_until(predicate, timeout=1, poll_interval=0.01), "ready")

    def test_wait_until_times_out(self) -> None:
        with self.assertRaises(SeniorBotTimeoutError):
            wait_until(lambda: None, timeout=0.02, poll_interval=0.01)

    def test_wait_for_file_returns_when_file_is_stable(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "export.xlsx"
            target.write_bytes(b"content")

            self.assertEqual(
                wait_for_file(
                    target,
                    timeout=1,
                    poll_interval=0.01,
                    stable_seconds=0.01,
                ),
                target,
            )


if __name__ == "__main__":
    unittest.main()
