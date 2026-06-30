"""Public API for the seniorbot package."""

from seniorbot.config import SeniorBotConfig
from seniorbot.exceptions import (
    DialogError,
    ExportError,
    KeyboardInputError,
    SeniorBotError,
    SeniorBotTimeoutError,
    WindowNotFoundError,
)
from seniorbot.export import SeniorBot
from seniorbot.screens import F141CISFilters, F141CISScreen

__all__ = [
    "DialogError",
    "ExportError",
    "KeyboardInputError",
    "SeniorBot",
    "SeniorBotConfig",
    "SeniorBotError",
    "SeniorBotTimeoutError",
    "F141CISFilters",
    "F141CISScreen",
    "WindowNotFoundError",
]
