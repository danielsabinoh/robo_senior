"""Screen-level workflows for Senior ERP."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from seniorbot.export import SeniorBot


def _today_screen_date() -> str:
    return date.today().strftime("%d/%m/%Y")


@dataclass(frozen=True, slots=True)
class F141CISFilters:
    """Filters used by the F141CIS consultation."""

    data_inicial: str = field(default_factory=_today_screen_date)
    data_final: str = field(default_factory=_today_screen_date)
    serie_nf: str = "036"
    cfops: tuple[str, ...] = ("5101", "5102", "6101", "6102", "5910", "6910")

    @property
    def filial(self) -> str:
        """Backward-compatible alias for the internal invoice series."""

        return self.serie_nf

    @property
    def cfop_text(self) -> str:
        """Return the CFOP text exactly as typed in the filter field."""

        return ",".join(f'"{cfop}"' for cfop in self.cfops)


class F141CISScreen:
    """Keyboard recipe for the F141CIS consultation."""

    def __init__(
        self,
        bot: SeniorBot,
        *,
        filters: F141CISFilters | None = None,
        focus_before_open: bool = True,
        startup_dialog_delay: float = 0.0,
        startup_dialog_tabs: int = 0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.bot = bot
        self.filters = filters or F141CISFilters()
        self.focus_before_open = focus_before_open
        self.startup_dialog_delay = startup_dialog_delay
        self.startup_dialog_tabs = startup_dialog_tabs
        self.logger = logger or logging.getLogger("seniorbot")

    def open_from_home(self) -> None:
        """Open F141CIS from Senior's initial screen using F11."""

        if self.focus_before_open:
            print("Focando janela do Senior...")
            self.bot.focus_remoteapp()
        self.confirm_startup_dialog()
        time.sleep(1.5)
        print("Abrindo busca de tela com F11...")
        self.bot.keyboard.f11()
        print("Digitando codigo F141CIS...")
        self.bot.keyboard.write_text("F141CIS")
        self.bot.keyboard.enter()
        self.logger.info("Tela F141CIS solicitada")

    def confirm_startup_dialog(self) -> None:
        """Confirm the optional Senior startup dialog before opening F141CIS."""

        if self.startup_dialog_delay > 0:
            print(f"Aguardando caixa inicial do Senior por {self.startup_dialog_delay:g} segundos...")
            time.sleep(self.startup_dialog_delay)
        if self.startup_dialog_tabs <= 0:
            return

        print("Confirmando caixa inicial do Senior...")
        for _ in range(self.startup_dialog_tabs):
            self.bot.keyboard.tab()
            time.sleep(0.2)
        self.bot.keyboard.enter()

    def fill_filters(self) -> None:
        """Fill the known F141CIS filters using the mapped keyboard route."""

        print("Preenchendo filtros da F141CIS...")
        keyboard = self.bot.keyboard

        keyboard.ctrl_a()
        keyboard.write_text(self.filters.data_inicial)

        keyboard.tab()
        keyboard.ctrl_a()
        keyboard.write_text(self.filters.data_final)

        keyboard.repeat("{TAB}", 8)
        keyboard.write_text(self.filters.serie_nf)

        keyboard.repeat("{TAB}", 11)
        keyboard.enter()

        keyboard.repeat("{TAB}", 4)
        keyboard.write_text(self.filters.cfop_text)

        keyboard.repeat("{TAB}", 2)
        keyboard.repeat("{UP}", 2)

        self.logger.info("Filtros da F141CIS preenchidos")

    def show_data_and_focus_grid(self) -> None:
        """Show the data and move focus into the result grid."""

        print("Exibindo dados e focando a grade...")
        keyboard = self.bot.keyboard
        keyboard.repeat("{TAB}", 45)
        keyboard.enter()
        keyboard.enter()
        keyboard.repeat("{TAB}", 8)
        self.logger.info("Grade da F141CIS focada")

    def prepare_grid(self) -> None:
        """Open the screen, fill filters, show data, and focus the grid."""

        self.open_from_home()
        self.fill_filters()
        self.show_data_and_focus_grid()

    def export_xlsx(
        self,
        path: str | Path,
        *,
        wait_path: str | Path | None = None,
        wait: bool = True,
    ) -> Path | None:
        """Run the full F141CIS flow and export the result grid."""

        self.prepare_grid()
        return self.bot.export_xlsx(path, wait_path=wait_path, wait=wait)
