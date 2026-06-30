import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from seniorbot.cli import build_parser, main, output_paths


class CliTests(unittest.TestCase):
    def test_output_paths_maps_local_drive_to_tsclient(self) -> None:
        remote_path, local_path = output_paths(r"C:\Temp\f141cis.xlsx")

        self.assertEqual(remote_path, Path(r"\\tsclient\C\Temp\f141cis.xlsx"))
        self.assertEqual(local_path, Path(r"C:\Temp\f141cis.xlsx"))

    def test_output_paths_keeps_unc_path_as_remote_only(self) -> None:
        remote_path, local_path = output_paths(r"\\server\share\f141cis.xlsx")

        self.assertEqual(remote_path, Path(r"\\server\share\f141cis.xlsx"))
        self.assertIsNone(local_path)

    def test_f141cis_parser_accepts_requested_command(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "f141cis",
                "--serie",
                "036",
                "--cfops",
                "5101",
                "5102",
                "--output",
                r"C:\Temp\f141cis.xlsx",
            ]
        )

        self.assertEqual(args.command, "f141cis")
        self.assertEqual(args.serie, "036")
        self.assertEqual(args.cfops, ["5101", "5102"])
        self.assertEqual(args.output, r"C:\Temp\f141cis.xlsx")

    def test_main_returns_error_and_writes_log_on_failure(self) -> None:
        with TemporaryDirectory() as directory:
            with patch("seniorbot.cli.run_f141cis", side_effect=RuntimeError("boom")):
                exit_code = main(["f141cis", "--yes", "--log-dir", directory])

            self.assertEqual(exit_code, 1)
            logs = list(Path(directory).glob("seniorbot-*.log"))
            self.assertEqual(len(logs), 1)
            self.assertIn("Falha na execucao", logs[0].read_text(encoding="utf-8"))

    def test_main_returns_zero_on_success(self) -> None:
        with TemporaryDirectory() as directory:
            with patch("seniorbot.cli.run_f141cis", return_value=Path("ok.xlsx")):
                exit_code = main(["f141cis", "--yes", "--log-dir", directory])

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(list(Path(directory).glob("seniorbot-*.log"))), 1)


if __name__ == "__main__":
    unittest.main()
