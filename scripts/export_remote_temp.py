"""Export the focused Senior ERP grid to the redirected local Temp folder."""

from __future__ import annotations

import time
from pathlib import Path

from seniorbot import SeniorBot, SeniorBotConfig
from seniorbot.export import configure_logging


def main() -> None:
    """Run a RemoteApp-only export test."""

    configure_logging()
    print()
    print("Antes de continuar:")
    print("1. Feche ou minimize o Explorer remoto.")
    print("2. Deixe a tela do Senior visivel, com a consulta aberta.")
    print("3. Deixe a grade dos dados visivel.")
    print()
    input("Pressione ENTER aqui e, em seguida, nao mexa no teclado/mouse...")
    print("Iniciando em 3 segundos...")
    time.sleep(3)

    bot = SeniorBot(
        SeniorBotConfig(
            context_menu_method="apps",
            grid_focus_keys=(),
            export_confirm_keys=("{DOWN}", "{ENTER}"),
            save_dialog_mode="remote_keyboard",
            remote_save_dialog_delay=5,
            remote_save_focus_keys=("%n",),
            create_parent_dirs=False,
            file_timeout=90,
        )
    )
    remote_path = Path(r"\\tsclient\C\Temp\teste_senior.xlsx")
    bot.export_xlsx(remote_path, wait=False)
    print(f"Comando de exportacao enviado para: {remote_path}")
    print(r"Confira no Windows local: C:\Temp\teste_senior.xlsx")


if __name__ == "__main__":
    main()
