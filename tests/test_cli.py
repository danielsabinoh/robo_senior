import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from seniorbot.cli import build_parser, main, output_paths, validate_f141cis_args


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

    def test_validate_f141cis_args_strips_and_rejects_invalid_cfops(self) -> None:
        args = Namespace(serie=" 036 ", cfops=[" 5101 ", "ABC"])

        with self.assertRaisesRegex(ValueError, "CFOP"):
            validate_f141cis_args(args)

    def test_validate_f141cis_args_returns_normalized_filters(self) -> None:
        args = Namespace(serie=" 036 ", cfops=[" 5101 ", "6102"])

        filters = validate_f141cis_args(args)

        self.assertEqual(filters.serie_nf, "036")
        self.assertEqual(filters.cfops, ("5101", "6102"))

    def test_main_dry_run_returns_zero_without_automation(self) -> None:
        with TemporaryDirectory() as directory:
            exit_code = main(
                [
                    "f141cis",
                    "--dry-run",
                    "--serie",
                    "036",
                    "--cfops",
                    "5101",
                    "--output",
                    r"C:\Temp\f141cis.xlsx",
                    "--log-dir",
                    directory,
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(list(Path(directory).glob("seniorbot-*.log"))), 1)

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
