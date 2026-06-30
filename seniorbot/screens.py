"""Screen-level workflows for Senior ERP."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from seniorbot.export import SeniorBot


@dataclass(frozen=True, slots=True)
class F141CISFilters:
    """Filters used by the F141CIS consultation."""

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
        logger: logging.Logger | None = None,
    ) -> None:
        self.bot = bot
        self.filters = filters or F141CISFilters()
        self.logger = logger or logging.getLogger("seniorbot")

    def open_from_home(self) -> None:
        """Open F141CIS from Senior's initial screen using F11."""

        self.bot.focus_remoteapp()
        self.bot.keyboard.send_keys("{F11}")
        self.bot.keyboard.write_text("F141CIS")
        self.bot.keyboard.enter()
        self.logger.info("Tela F141CIS solicitada")

    def fill_filters(self) -> None:
        """Fill the known F141CIS filters using the mapped keyboard route."""

        keyboard = self.bot.keyboard

        keyboard.repeat("{TAB}", 9)
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
