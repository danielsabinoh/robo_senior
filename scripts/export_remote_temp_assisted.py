"""Assisted export test for Senior ERP RemoteApp."""

from __future__ import annotations

import time
from pathlib import Path

from seniorbot import SeniorBot, SeniorBotConfig
from seniorbot.export import configure_logging


def countdown(seconds: int, message: str) -> None:
    """Show a short countdown without requiring keyboard focus changes."""

    for remaining in range(seconds, 0, -1):
        print(f"{message} {remaining}s...")
        time.sleep(1)


def main() -> None:
    """Run the export workflow with confirmation checkpoints."""

    configure_logging()
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

    print()
    print("Deixe o Senior na tela da consulta, com a grade visivel.")
    print("Depois de pressionar ENTER aqui, nao use o mouse/teclado ate terminar.")
    input("Pressione ENTER para iniciar...")
    countdown(3, "Comecando em")

    bot.focus_remoteapp()
    bot.focus_grid()
    bot.open_context_menu("apps")
    countdown(2, "Menu aberto, confirmando exportacao em")
    bot.keyboard.send_sequence(("{DOWN}", "{ENTER}"))
    countdown(5, "Aguardando Salvar como remoto em")
    bot.save_file(remote_path)

    print()
    print("Comando de salvar enviado.")
    print(r"Confira no Windows local: C:\Temp\teste_senior.xlsx")
    print(r"Ou no remoto pela pasta redirecionada: \\tsclient\C\Temp")


if __name__ == "__main__":
    main()
