import unittest
from argparse import Namespace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from seniorbot.cli import (
    ask_f141cis_filter_dates,
    backup_existing_file,
    build_parser,
    close_rdp_session,
    default_f141cis_base_dir,
    f141cis_output_path,
    format_file_size,
    format_screen_date,
    main,
    output_paths,
    parse_export_date,
    parse_screen_date,
    resolve_f141cis_output,
    validate_f141cis_args,
)


class FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[str] = []

    def enter(self) -> None:
        self.events.append("{ENTER}")

    def alt_f4(self) -> None:
        self.events.append("alt_f4")


class CliTests(unittest.TestCase):
    def test_output_paths_maps_local_drive_to_tsclient(self) -> None:
        remote_path, local_path = output_paths(r"C:\Temp\f141cis.xlsx")

        self.assertEqual(remote_path, Path(r"\\tsclient\C\Temp\f141cis.xlsx"))
        self.assertEqual(local_path, Path(r"C:\Temp\f141cis.xlsx"))

    def test_output_paths_can_keep_local_drive_for_full_rdp(self) -> None:
        remote_path, local_path = output_paths(
            r"C:\Temp\f141cis.xlsx",
            use_tsclient=False,
        )

        self.assertEqual(remote_path, Path(r"C:\Temp\f141cis.xlsx"))
        self.assertIsNone(local_path)

    def test_output_paths_keeps_unc_path_as_remote_only(self) -> None:
        remote_path, local_path = output_paths(r"\\server\share\f141cis.xlsx")

        self.assertEqual(remote_path, Path(r"\\server\share\f141cis.xlsx"))
        self.assertIsNone(local_path)

    def test_parse_export_date_accepts_common_formats(self) -> None:
        self.assertEqual(parse_export_date("2026-07-01"), date(2026, 7, 1))
        self.assertEqual(parse_export_date("01/07/2026"), date(2026, 7, 1))
        self.assertEqual(parse_export_date("01.07.2026"), date(2026, 7, 1))

    def test_parse_screen_date_accepts_dd_mm_yyyy_or_default(self) -> None:
        default = date(2026, 7, 1)

        self.assertEqual(parse_screen_date(None, default=default), default)
        self.assertEqual(parse_screen_date("", default=default), default)
        self.assertEqual(parse_screen_date("02/07/2026", default=default), date(2026, 7, 2))

    def test_format_screen_date_uses_senior_date_format(self) -> None:
        self.assertEqual(format_screen_date(date(2026, 7, 1)), "01/07/2026")

    def test_f141cis_output_path_uses_month_folder_and_day_file(self) -> None:
        path = f141cis_output_path(
            base_dir=r"C:\Faturamento",
            export_date=date(2026, 7, 1),
        )

        self.assertEqual(path, Path(r"C:\Faturamento\07 2026\01.07.xlsx"))

    def test_resolve_f141cis_output_uses_automatic_monthly_path(self) -> None:
        args = Namespace(
            output=None,
            base_dir=r"C:\Faturamento",
            date="02/07/2026",
        )

        self.assertEqual(
            resolve_f141cis_output(args),
            Path(r"C:\Faturamento\07 2026\02.07.xlsx"),
        )

    def test_resolve_f141cis_output_keeps_explicit_output(self) -> None:
        args = Namespace(
            output=r"C:\Temp\f141cis.xlsx",
            base_dir=r"C:\Faturamento",
            date="02/07/2026",
        )

        self.assertEqual(resolve_f141cis_output(args), Path(r"C:\Temp\f141cis.xlsx"))

    def test_default_f141cis_base_dir_is_c_exportacoes(self) -> None:
        self.assertEqual(default_f141cis_base_dir(), Path(r"C:\exportacoes"))

    def test_backup_existing_file_moves_file_to_monthly_backup_folder(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "07 2026" / "01.07.xlsx"
            target.parent.mkdir()
            target.write_bytes(b"old")

            backup = backup_existing_file(target)

            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertFalse(target.exists())
            self.assertEqual(backup.read_bytes(), b"old")
            self.assertEqual(backup.parent, target.parent / "_backups")
            self.assertRegex(backup.name, r"01\.07\.backup-\d{8}-\d{6}\.xlsx")

    def test_backup_existing_file_returns_none_when_file_does_not_exist(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "missing.xlsx"

            self.assertIsNone(backup_existing_file(target))

    def test_format_file_size_returns_readable_size(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "export.xlsx"
            target.write_bytes(b"x" * 2048)

            self.assertEqual(format_file_size(target), "2.0 KB")

    def test_close_rdp_session_sends_expected_shutdown_sequence(self) -> None:
        keyboard = FakeKeyboard()

        with (
            patch("seniorbot.cli.time.sleep"),
            patch("seniorbot.cli.subprocess.run") as run_mock,
        ):
            close_rdp_session(keyboard)  # type: ignore[arg-type]

        self.assertEqual(
            keyboard.events,
            ["{ENTER}", "alt_f4", "{ENTER}", "alt_f4", "{ENTER}"],
        )
        run_mock.assert_called_once()
        self.assertEqual(
            run_mock.call_args.args[0],
            ["taskkill", "/IM", "mstsc.exe", "/T", "/F"],
        )

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
        args = Namespace(
            serie=" 036 ",
            cfops=[" 5101 ", "6102"],
            start_date="01/07/2026",
            end_date="02/07/2026",
        )

        filters = validate_f141cis_args(args)

        self.assertEqual(filters.data_inicial, "01/07/2026")
        self.assertEqual(filters.data_final, "02/07/2026")
        self.assertEqual(filters.serie_nf, "036")
        self.assertEqual(filters.cfops, ("5101", "6102"))

    def test_validate_f141cis_args_uses_export_date_as_default_filter_date(self) -> None:
        args = Namespace(
            serie="036",
            cfops=["5101"],
            date="02/07/2026",
            start_date=None,
            end_date=None,
        )

        filters = validate_f141cis_args(args)

        self.assertEqual(filters.data_inicial, "02/07/2026")
        self.assertEqual(filters.data_final, "02/07/2026")

    def test_validate_f141cis_args_rejects_end_date_before_start_date(self) -> None:
        args = Namespace(
            serie="036",
            cfops=["5101"],
            start_date="02/07/2026",
            end_date="01/07/2026",
        )

        with self.assertRaisesRegex(ValueError, "data final"):
            validate_f141cis_args(args)

    def test_ask_f141cis_filter_dates_uses_today_when_user_presses_enter(self) -> None:
        args = Namespace(
            yes=True,
            dry_run=False,
            use_today=False,
            date=None,
            start_date=None,
            end_date=None,
        )

        with patch("builtins.input", side_effect=["", ""]):
            ask_f141cis_filter_dates(args)

        today = format_screen_date(date.today())
        self.assertEqual(args.start_date, today)
        self.assertEqual(args.end_date, today)

    def test_ask_f141cis_filter_dates_skips_when_use_today_is_set(self) -> None:
        args = Namespace(
            yes=True,
            dry_run=False,
            use_today=True,
            date=None,
            start_date=None,
            end_date=None,
        )

        with patch("builtins.input") as input_mock:
            ask_f141cis_filter_dates(args)

        input_mock.assert_not_called()
        self.assertIsNone(args.start_date)

    def test_ask_f141cis_filter_dates_skips_when_export_date_is_set(self) -> None:
        args = Namespace(
            yes=True,
            dry_run=False,
            use_today=False,
            date="2026-07-02",
            start_date=None,
            end_date=None,
        )

        with patch("builtins.input") as input_mock:
            ask_f141cis_filter_dates(args)

        input_mock.assert_not_called()
        self.assertIsNone(args.start_date)

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
