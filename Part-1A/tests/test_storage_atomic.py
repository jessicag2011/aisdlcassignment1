from pathlib import Path

import pytest

from todo import storage
from todo.errors import StorageError
from todo.service import TodoService


def test_failed_atomic_replace_preserves_the_previous_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "todo.json"
    service = TodoService(database)
    service.add("Existing task")
    original = database.read_bytes()

    def fail_replace(_source: str, _destination: Path) -> None:
        raise OSError("replacement failed")

    monkeypatch.setattr(storage.os, "replace", fail_replace)

    with pytest.raises(StorageError, match="cannot write task store"):
        service.add("New task")

    assert database.read_bytes() == original
    assert list(tmp_path.glob(".todo.json.*.tmp")) == []
