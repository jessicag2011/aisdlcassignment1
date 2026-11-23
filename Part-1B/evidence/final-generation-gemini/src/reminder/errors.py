"""Typed failures for input, provider, and model-output boundaries."""


class ReminderError(Exception):
    """Base class for expected request failures."""


class InputError(ReminderError):
    """Invalid caller input."""


class ProviderError(ReminderError):
    """Model service or configuration failure."""

    def __init__(self, category: str, code: str) -> None:
        super().__init__(code)
        self.category = category
        self.code = code


class ModelOutputError(ReminderError):
    """Invalid model response or output-contract violation."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
