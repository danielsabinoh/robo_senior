"""Command-line interface for seniorbot."""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from seniorbot import F141CISFilters, F141CISScreen, SeniorBot, SeniorBotConfig
from seniorbot.keyboard import Keyboard, PywinautoKeyboardDriver
from seniorbot.logging import configure_run_logging, shutdown_logging
from seniorbot.remote_desktop import (
    RemoteDesktopLauncher,
    load_remote_desktop_config,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the seniorbot command-line parser."""

    parser = argparse.ArgumentParser(
        prog="seniorbot",
        description="Keyboard-first automation for Senior ERP over RemoteApp.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    f141cis = subparsers.add_parser(
        "f141cis",
        help="Open F141CIS, fill filters, show data, and export XLSX.",
    )
    f141cis.add_argument("--serie", default="036", help="Internal NF series.")
    f141cis.add_argument(
        "--cfops",
        nargs="+",
        default=["5101", "5102", "6101", "6102", "5910", "6910"],
        help="CFOP codes to filter.",
    )
    f141cis.add_argument(
        "--output",
        default=None,
        help=(
            "Local output path, or a RemoteApp-visible path. "
            "When omitted, uses the monthly F141CIS folder."
        ),
    )
    f141cis.add_argument(
        "--base-dir",
        default=None,
        help=(
            "Base folder for automatic F141CIS exports. "
            "Default: C:\\exportacoes."
        ),
    )
    f141cis.add_argument(
        "--date",
        default=None,
        help="Export date in YYYY-MM-DD, DD/MM/YYYY, or DD.MM.YYYY format.",
    )
    f141cis.add_argument(
        "--start-date",
        default=None,
        help="Initial F141CIS filter date in DD/MM/YYYY. Default: today.",
    )
    f141cis.add_argument(
        "--end-date",
        default=None,
        help="Final F141CIS filter date in DD/MM/YYYY. Default: today.",
    )
    f141cis.add_argument(
        "--use-today",
        action="store_true",
        help="Use today's date for F141CIS filters without prompting.",
    )
    f141cis.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Seconds to wait after the initial prompt before automation starts.",
    )
    f141cis.add_argument(
        "--save-delay",
        type=float,
        default=5,
        help="Seconds to wait for the remote Save As dialog.",
    )
    f141cis.add_argument(
        "--yes",
        action="store_true",
        help="Start without the initial confirmation prompt.",
    )
    f141cis.add_argument(
        "--no-wait",
        action="store_true",
        help="Do not wait for the exported local file.",
    )
    f141cis.add_argument(
        "--log-dir",
        default=None,
        help="Directory where execution logs are written.",
    )
    f141cis.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and show the resolved save paths without automation.",
    )
    f141cis.add_argument(
        "--open-rdp",
        action="store_true",
        help="Open Remote Desktop, start Senior, then run F141CIS.",
    )
    f141cis.add_argument(
        "--rdp-save-remote",
        action="store_true",
        help="When using --open-rdp, save on the remote desktop C: drive instead of \\\\tsclient.",
    )
    f141cis.add_argument(
        "--keep-rdp-open",
        action="store_true",
        help="Keep the Remote Desktop session open after a successful export.",
    )
    f141cis.add_argument(
        "--rdp-env",
        default=None,
        help="Local env file with RDP and Senior credentials.",
    )
    f141cis.add_argument(
        "--senior-startup-delay",
        type=float,
        default=10.0,
        help="Seconds to wait before confirming Senior's startup dialog.",
    )
    return parser


def output_paths(output: str, *, use_tsclient: bool = True) -> tuple[Path, Path | None]:
    """Return the RemoteApp save path and optional local wait path."""

    drive_match = re.match(r"^([A-Za-z]):\\(.+)$", output)
    if drive_match and use_tsclient:
        drive = drive_match.group(1).upper()
        rest = drive_match.group(2)
        return Path(rf"\\tsclient\{drive}\{rest}"), Path(output)

    return Path(output), None


def parse_export_date(value: str | None) -> date:
    """Parse the requested export date, defaulting to today."""

    if value is None:
        return date.today()

    normalized = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            pass

    raise ValueError("Data invalida. Use YYYY-MM-DD, DD/MM/YYYY ou DD.MM.YYYY.")


def format_screen_date(value: date) -> str:
    """Format a date exactly as typed in Senior date fields."""

    return value.strftime("%d/%m/%Y")


def parse_screen_date(value: str | None, *, default: date) -> date:
    """Parse an optional Senior screen date in DD/MM/YYYY format."""

    if value is None or not value.strip():
        return default

    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError("Data invalida. Use DD/MM/AAAA.") from exc


def ask_screen_date(label: str, *, default: date) -> date:
    """Ask the user for a F141CIS filter date, defaulting on Enter."""

    default_text = format_screen_date(default)
    value = input(f"{label} [{default_text}]: ")
    return parse_screen_date(value, default=default)


def default_f141cis_base_dir() -> Path:
    """Return the default base folder for daily F141CIS exports."""

    return Path(r"C:\exportacoes")


def f141cis_output_path(*, base_dir: str | Path | None, export_date: date) -> Path:
    """Build the monthly F141CIS export path for a given date."""

    root = Path(base_dir) if base_dir is not None else default_f141cis_base_dir()
    month_folder = export_date.strftime("%m %Y")
    file_name = export_date.strftime("%d.%m.xlsx")
    return root / month_folder / file_name


def resolve_f141cis_output(args: argparse.Namespace) -> Path:
    """Resolve the explicit or automatic F141CIS output path."""

    if args.output:
        return Path(args.output)
    export_date = parse_export_date(args.date)
    return f141cis_output_path(base_dir=args.base_dir, export_date=export_date)


def backup_existing_file(path: Path) -> Path | None:
    """Move an existing export file to the monthly backup folder."""

    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"O destino existe, mas nao e um arquivo: {path}")

    backup_dir = path.parent / "_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}.backup-{timestamp}{path.suffix}"
    shutil.move(str(path), str(backup_path))
    return backup_path


def format_file_size(path: Path | None) -> str:
    """Return a readable file size for export summaries."""

    if path is None or not path.exists() or not path.is_file():
        return "nao disponivel"

    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def print_export_summary(path: Path, *, backup_path: Path | None) -> None:
    """Print a concise post-export summary for manual and scheduled runs."""

    finished_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print("Resumo da exportacao")
    print(f"Arquivo: {path.name}")
    print(f"Pasta: {path.parent}")
    print(f"Tamanho: {format_file_size(path)}")
    print(f"Horario: {finished_at}")
    if backup_path is not None:
        print(f"Backup anterior: {backup_path}")


def close_rdp_session(keyboard: Keyboard, *, step_delay: float = 1.0) -> None:
    """Confirm the final save message and close Senior/RDP after a successful run."""

    print("Confirmando arquivo salvo e fechando a sessao remota...")
    time.sleep(5.0)
    keyboard.enter()
    time.sleep(step_delay)
    subprocess.run(
        ["taskkill", "/IM", "mstsc.exe", "/T", "/F"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    keyboard.alt_f4()
    time.sleep(step_delay)
    keyboard.enter()
    time.sleep(3.0)
    keyboard.alt_f4()
    time.sleep(step_delay)
    keyboard.enter()
    time.sleep(step_delay)


def validate_f141cis_args(args: argparse.Namespace) -> F141CISFilters:
    """Validate and normalize F141CIS business filters from CLI arguments."""

    serie = args.serie.strip()
    if not serie:
        raise ValueError("A serie da NF nao pode ficar vazia.")

    cfops = tuple(cfop.strip() for cfop in args.cfops if cfop.strip())
    if not cfops:
        raise ValueError("Informe pelo menos um CFOP.")

    invalid_cfops = [cfop for cfop in cfops if not cfop.isdigit()]
    if invalid_cfops:
        raise ValueError(
            "CFOP deve conter apenas numeros: " + ", ".join(invalid_cfops)
        )

    default_filter_date = parse_export_date(getattr(args, "date", None))
    start_date = parse_screen_date(
        getattr(args, "start_date", None),
        default=default_filter_date,
    )
    end_date = parse_screen_date(
        getattr(args, "end_date", None),
        default=default_filter_date,
    )
    if end_date < start_date:
        raise ValueError("A data final nao pode ser menor que a data inicial.")

    return F141CISFilters(
        data_inicial=format_screen_date(start_date),
        data_final=format_screen_date(end_date),
        serie_nf=serie,
        cfops=cfops,
    )


def ask_f141cis_filter_dates(args: argparse.Namespace) -> None:
    """Prompt for screen date filters when running interactively."""

    if args.dry_run or getattr(args, "use_today", False):
        return
    if args.start_date or args.end_date:
        return
    if getattr(args, "date", None):
        return

    default_filter_date = parse_export_date(getattr(args, "date", None))
    print()
    print("Informe as datas do filtro da F141CIS.")
    print("Pressione ENTER para usar a data de hoje.")
    start_date = ask_screen_date("Data inicial", default=default_filter_date)
    end_date = ask_screen_date("Data final", default=default_filter_date)
    if end_date < start_date:
        raise ValueError("A data final nao pode ser menor que a data inicial.")

    args.start_date = format_screen_date(start_date)
    args.end_date = format_screen_date(end_date)


def run_f141cis(args: argparse.Namespace) -> Path | None:
    """Run the F141CIS export command."""

    logger = logging.getLogger("seniorbot")
    ask_f141cis_filter_dates(args)
    filters = validate_f141cis_args(args)
    output = resolve_f141cis_output(args)
    use_tsclient = not (args.open_rdp and args.rdp_save_remote)
    remote_path, local_path = output_paths(str(output), use_tsclient=use_tsclient)
    logger.info(
        "Iniciando F141CIS: data_inicial=%s data_final=%s serie=%s cfops=%s output=%s remote_path=%s",
        filters.data_inicial,
        filters.data_final,
        filters.serie_nf,
        ",".join(filters.cfops),
        output,
        remote_path,
    )

    if args.dry_run:
        print("Simulacao F141CIS")
        print(f"Data inicial: {filters.data_inicial}")
        print(f"Data final: {filters.data_final}")
        print(f"Serie NF: {filters.serie_nf}")
        print(f"CFOPs: {', '.join(filters.cfops)}")
        print(f"Arquivo de saida: {output}")
        print(f"Caminho usado no RemoteApp: {remote_path}")
        if local_path is not None:
            print(f"Arquivo local aguardado: {local_path}")
        else:
            print("Arquivo local aguardado: nao aplicavel; arquivo salvo no ambiente remoto")
        logger.info("Simulacao F141CIS concluida")
        return local_path or remote_path

    if not args.yes:
        print()
        print("Deixe o Senior aberto na tela inicial.")
        print("Depois de continuar, nao use o mouse/teclado ate terminar.")
        input("Pressione ENTER para iniciar...")

    if args.delay > 0:
        print(f"Iniciando em {args.delay} segundos...")
        time.sleep(args.delay)

    if local_path is not None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup_existing_file(local_path) if local_path is not None else None
    if backup_path is not None:
        logger.info("Arquivo existente movido para backup: %s", backup_path)

    rdp_keyboard: Keyboard | None = None
    if args.open_rdp:
        print("Preparando abertura do Senior pela Area de Trabalho Remota...")
        rdp_keyboard = Keyboard(PywinautoKeyboardDriver(logger))
        rdp_config = load_remote_desktop_config(args.rdp_env)
        RemoteDesktopLauncher(rdp_keyboard, rdp_config).open_senior()

    print("Conectando ao controle de janelas do Windows...")
    bot = SeniorBot(
        SeniorBotConfig(
            focus_before_export=not args.open_rdp,
            context_menu_method="shift_f10",
            grid_focus_keys=(),
            export_confirm_keys=("{DOWN}", "{ENTER}"),
            save_dialog_mode="remote_keyboard",
            remote_save_dialog_delay=args.save_delay,
            remote_save_focus_keys=("%n",),
            create_parent_dirs=False,
            file_timeout=120,
        ),
        keyboard=rdp_keyboard,
    )
    if args.open_rdp:
        print("Usando a sessao remota ja aberta; sem procurar janela do Senior.")
    else:
        print("Procurando e focando a janela do Senior...")
    screen = F141CISScreen(
        bot,
        filters=filters,
        focus_before_open=not args.open_rdp,
        startup_dialog_delay=args.senior_startup_delay if args.open_rdp else 0,
        startup_dialog_tabs=4 if args.open_rdp else 0,
    )

    print("Executando roteiro F141CIS e exportando a grade...")
    result = screen.export_xlsx(
        remote_path,
        wait_path=local_path,
        wait=not args.no_wait and local_path is not None,
    )
    if args.open_rdp and rdp_keyboard is not None and not args.keep_rdp_open:
        close_rdp_session(rdp_keyboard)
    logger.info("F141CIS concluida com sucesso: %s", local_path or remote_path)
    summary_path = local_path or result or remote_path
    print(f"OK: arquivo exportado em {summary_path}")
    print_export_summary(Path(summary_path), backup_path=backup_path)
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the seniorbot CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    log_path: Path | None = None

    exit_code = 2
    try:
        log_path = configure_run_logging(log_dir=getattr(args, "log_dir", None))

        if args.command == "f141cis":
            run_f141cis(args)
            print(f"Log: {log_path}")
            exit_code = 0
            return exit_code
    except KeyboardInterrupt:
        logging.getLogger("seniorbot").warning("Execucao cancelada pelo usuario")
        print("Execucao cancelada pelo usuario.", file=sys.stderr)
        if log_path is not None:
            print(f"Log: {log_path}", file=sys.stderr)
        exit_code = 130
        return exit_code
    except Exception as exc:
        logging.getLogger("seniorbot").exception("Falha na execucao")
        print(f"ERRO: {exc}", file=sys.stderr)
        if log_path is not None:
            print(f"Veja detalhes no log: {log_path}", file=sys.stderr)
        exit_code = 1
        return exit_code
    finally:
        shutdown_logging()

    parser.error(f"Unsupported command: {args.command}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
