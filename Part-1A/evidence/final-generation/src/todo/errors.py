"""Application errors with stable user-facing messages."""


class TodoError(Exception):
    """Expected invalid operation or task data."""


class StorageError(Exception):
    """Invalid or unavailable persistent task store."""
