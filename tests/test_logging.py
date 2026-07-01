import unittest

from seniorbot.logging import default_log_dir, project_root


class LoggingTests(unittest.TestCase):
    def test_default_log_dir_is_inside_project_folder(self) -> None:
        self.assertEqual(default_log_dir(), project_root() / "logs")


if __name__ == "__main__":
    unittest.main()
