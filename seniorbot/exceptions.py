"""Custom exceptions raised by seniorbot."""


class SeniorBotError(RuntimeError):
    """Base class for all seniorbot errors."""


class SeniorBotTimeoutError(SeniorBotError):
    """Raised when an expected condition is not reached in time."""


class WindowNotFoundError(SeniorBotError):
    """Raised when a required Windows top-level window cannot be found."""


class KeyboardInputError(SeniorBotError):
    """Raised when keyboard input cannot be sent."""


class DialogError(SeniorBotError):
    """Raised when a native dialog cannot be automated."""


class ExportError(SeniorBotError):
    """Raised when an ERP export workflow fails."""
