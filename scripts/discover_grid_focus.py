"""Discover a keyboard-only route to focus the Senior ERP grid."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from seniorbot import SeniorBot, SeniorBotConfig
from seniorbot.export import configure_logging


@dataclass(frozen=True, slots=True)
class Candidate:
    """A possible keyboard route from RemoteApp focus to the ERP grid."""

    name: str
    keys: tuple[str, ...]


def build_candidates() -> Iterable[Candidate]:
    """Yield conservative keyboard focus candidates."""

    yield Candidate("sem teclas extras", ())
    yield Candidate("Esc", ("{ESC}",))

    for count in range(1, 9):
        yield Candidate(f"{count} Tab", ("{TAB}",) * count)

    for count in range(1, 7):
        yield Candidate(f"{count} Shift+Tab", ("+{TAB}",) * count)

    yield Candidate("F6", ("{F6}",))
    yield Candidate("F6, Tab", ("{F6}", "{TAB}"))
    yield Candidate("F6, Tab, Tab", ("{F6}", "{TAB}", "{TAB}"))
    yield Candidate("Esc, Tab", ("{ESC}", "{TAB}"))
    yield Candidate("Esc, Tab, Tab", ("{ESC}", "{TAB}", "{TAB}"))
    yield Candidate("Esc, F6", ("{ESC}", "{F6}"))
    yield Candidate("Esc, F6, Tab", ("{ESC}", "{F6}", "{TAB}"))


def main() -> None:
    """Run an interactive grid-focus discovery session."""

    configure_logging()
    bot = SeniorBot(SeniorBotConfig(context_menu_method="apps"))

    print()
    print("Deixe o Senior aberto na consulta, com os dados ja carregados.")
    print("Este teste nao usa mouse. Ele vai tentar focar a grade por teclado.")
    print("Depois de cada tentativa, olhe o menu aberto no Senior.")
    print()

    input("Pressione ENTER aqui para comecar...")

    for candidate in build_candidates():
        print()
        print(f"Tentando: {candidate.name}")

        bot.focus_remoteapp()
        bot.keyboard.send_keys("{ESC}")
        bot.keyboard.send_sequence(candidate.keys)
        bot.open_context_menu("apps")

        answer = input("O menu correto da grade abriu? [s/N] ").strip().lower()
        bot.keyboard.send_keys("{ESC}")

        if answer in {"s", "sim", "y", "yes"}:
            print()
            print("Sequencia encontrada:")
            print(candidate.keys)
            print()
            print("Use assim:")
            print("SeniorBotConfig(")
            print('    context_menu_method="apps",')
            print(f"    grid_focus_keys={candidate.keys!r},")
            print(")")
            return

    print()
    print("Nenhuma sequencia padrao funcionou.")
    print("O proximo passo e mapear a tela com uma rota especifica do ERP.")


if __name__ == "__main__":
    main()
