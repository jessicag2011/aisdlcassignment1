"""Versioned JSON storage with validation and atomic replacement."""

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from todo.errors import StorageError

_TASK_FIELDS = {"id", "title", "description", "priority", "tags", "status"}
_PRIORITIES = {"low", "medium", "high"}
_STATUSES = {"open", "completed"}


def _is_positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _validate_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict) or set(document) != {"version", "next_id", "tasks"}:
        raise StorageError("invalid task store: expected version, next_id, and tasks")
    if (
        not isinstance(document["version"], int)
        or isinstance(document["version"], bool)
        or document["version"] != 1
        or not _is_positive_integer(document["next_id"])
    ):
        raise StorageError("invalid task store: unsupported version or invalid next_id")
    tasks = document["tasks"]
    if not isinstance(tasks, list):
        raise StorageError("invalid task store: tasks must be an array")

    identifiers: set[int] = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) != _TASK_FIELDS:
            raise StorageError("invalid task store: task has unexpected fields")
        task_id = task["id"]
        if not _is_positive_integer(task_id) or task_id in identifiers:
            raise StorageError("invalid task store: task IDs must be unique positive integers")
        identifiers.add(task_id)
        if not isinstance(task["title"], str) or not task["title"].strip():
            raise StorageError("invalid task store: task title must be non-empty")
        if not isinstance(task["description"], str):
            raise StorageError("invalid task store: description must be a string")
        if not isinstance(task["priority"], str) or task["priority"] not in _PRIORITIES:
            raise StorageError("invalid task store: unsupported priority")
        if not isinstance(task["status"], str) or task["status"] not in _STATUSES:
            raise StorageError("invalid task store: unsupported status")
        if not isinstance(task["tags"], list) or any(
            not isinstance(tag, str) or not tag for tag in task["tags"]
        ):
            raise StorageError("invalid task store: tags must be non-empty strings")

    if identifiers and document["next_id"] <= max(identifiers):
        raise StorageError("invalid task store: next_id must exceed all task IDs")
    return document


def load_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "next_id": 1, "tasks": []}
    try:
        with path.open("r", encoding="utf-8") as source:
            return _validate_document(json.load(source))
    except json.JSONDecodeError as error:
        raise StorageError("invalid task store: malformed JSON") from error
    except OSError as error:
        raise StorageError(f"cannot read task store: {error.strerror}") from error


def save_document(path: Path, document: dict[str, Any]) -> None:
    validated = _validate_document(document)
    temporary_path: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as target:
            temporary_path = target.name
            json.dump(validated, target, ensure_ascii=False, indent=2)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path is not None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_path)
        raise StorageError(f"cannot write task store: {error.strerror}") from error
