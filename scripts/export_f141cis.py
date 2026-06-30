"""Run the F141CIS export workflow from Senior's initial screen."""

from __future__ import annotations

import time
from pathlib import Path

from seniorbot import F141CISFilters, F141CISScreen, SeniorBot, SeniorBotConfig
from seniorbot.export import configure_logging


def main() -> None:
    """Open F141CIS, fill filters, show data, and export the grid."""

    configure_logging()
    print()
    print("Deixe o Senior aberto na tela inicial.")
    print("Depois de pressionar ENTER, nao use o mouse/teclado ate terminar.")
    input("Pressione ENTER para iniciar...")
    print("Iniciando em 3 segundos...")
    time.sleep(3)

    remote_path = Path(r"\\tsclient\C\Temp\f141cis.xlsx")
    local_path = Path(r"C:\Temp\f141cis.xlsx")

    bot = SeniorBot(
        SeniorBotConfig(
            context_menu_method="apps",
            grid_focus_keys=(),
            export_confirm_keys=("{DOWN}", "{ENTER}"),
            save_dialog_mode="remote_keyboard",
            remote_save_dialog_delay=5,
            remote_save_focus_keys=("%n",),
            create_parent_dirs=False,
            file_timeout=120,
        )
    )
    screen = F141CISScreen(
        bot,
        filters=F141CISFilters(
            serie_nf="036",
            cfops=("5101", "5102", "6101", "6102", "5910", "6910"),
        ),
    )

    screen.export_xlsx(remote_path, wait_path=local_path)
    print(f"OK: arquivo exportado em {local_path}")


if __name__ == "__main__":
    main()
