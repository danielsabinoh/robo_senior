"""Command-line interface for seniorbot."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path

from seniorbot import F141CISFilters, F141CISScreen, SeniorBot, SeniorBotConfig
from seniorbot.logging import configure_run_logging, shutdown_logging


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
        default=r"C:\Temp\f141cis.xlsx",
        help="Local output path, or a RemoteApp-visible path.",
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
    return parser


def output_paths(output: str) -> tuple[Path, Path | None]:
    """Return the RemoteApp save path and optional local wait path."""

    drive_match = re.match(r"^([A-Za-z]):\\(.+)$", output)
    if drive_match:
        drive = drive_match.group(1).upper()
        rest = drive_match.group(2)
        return Path(rf"\\tsclient\{drive}\{rest}"), Path(output)

    return Path(output), None


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

    return F141CISFilters(serie_nf=serie, cfops=cfops)


def run_f141cis(args: argparse.Namespace) -> Path | None:
    """Run the F141CIS export command."""

    logger = logging.getLogger("seniorbot")
    filters = validate_f141cis_args(args)
    remote_path, local_path = output_paths(args.output)
    logger.info(
        "Iniciando F141CIS: serie=%s cfops=%s output=%s remote_path=%s",
        filters.serie_nf,
        ",".join(filters.cfops),
        args.output,
        remote_path,
    )

    if args.dry_run:
        print("Simulacao F141CIS")
        print(f"Serie NF: {filters.serie_nf}")
        print(f"CFOPs: {', '.join(filters.cfops)}")
        print(f"Caminho usado no RemoteApp: {remote_path}")
        if local_path is not None:
            print(f"Arquivo local aguardado: {local_path}")
        else:
            print("Arquivo local aguardado: nao aplicavel")
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

    bot = SeniorBot(
        SeniorBotConfig(
            context_menu_method="apps",
            grid_focus_keys=(),
            export_confirm_keys=("{DOWN}", "{ENTER}"),
            save_dialog_mode="remote_keyboard",
            remote_save_dialog_delay=args.save_delay,
            remote_save_focus_keys=("%n",),
            create_parent_dirs=False,
            file_timeout=120,
        )
    )
    screen = F141CISScreen(
        bot,
        filters=filters,
    )

    result = screen.export_xlsx(
        remote_path,
        wait_path=local_path,
        wait=not args.no_wait,
    )
    logger.info("F141CIS concluida com sucesso: %s", local_path or remote_path)
    print(f"OK: arquivo exportado em {local_path or remote_path}")
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
