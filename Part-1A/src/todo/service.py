"""Specification-driven task operations."""

from pathlib import Path
from typing import Any

from todo.errors import TodoError
from todo.storage import load_document, save_document

_PRIORITIES = {"low", "medium", "high"}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class TodoService:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> dict[str, Any]:
        return load_document(self._path)

    def _write(self, document: dict[str, Any]) -> None:
        save_document(self._path, document)

    @staticmethod
    def _find_task(document: dict[str, Any], task_id: int) -> dict[str, Any]:
        for task in document["tasks"]:
            if task["id"] == task_id:
                return task
        raise TodoError(f"task not found: {task_id}")

    @staticmethod
    def _validated_title(title: str) -> str:
        if not isinstance(title, str) or not title.strip():
            raise TodoError("title must not be empty")
        return title.strip()

    @staticmethod
    def _validated_priority(priority: str) -> str:
        if priority not in _PRIORITIES:
            raise TodoError("priority must be low, medium, or high")
        return priority

    @staticmethod
    def _validated_tags(tags: list[str]) -> list[str]:
        if not isinstance(tags, list):
            raise TodoError("tags must be a list of non-empty strings")
        cleaned: list[str] = []
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                raise TodoError("tags must be a list of non-empty strings")
            value = tag.strip()
            if value not in cleaned:
                cleaned.append(value)
        return cleaned

    def add(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        document = self._read()
        task = {
            "id": document["next_id"],
            "title": self._validated_title(title),
            "description": description,
            "priority": self._validated_priority(priority),
            "tags": self._validated_tags(tags or []),
            "status": "open",
        }
        if not isinstance(description, str):
            raise TodoError("description must be a string")
        document["tasks"].append(task)
        document["next_id"] += 1
        self._write(document)
        return task

    def list_tasks(
        self,
        tag: str | None = None,
        status: str | None = None,
        sort_priority: bool = False,
    ) -> list[dict[str, Any]]:
        document = self._read()
        tasks = [
            task
            for task in document["tasks"]
            if (tag is None or tag in task["tags"])
            and (status is None or status == task["status"])
        ]
        if status is not None and status not in {"open", "completed"}:
            raise TodoError("status must be open or completed")
        if sort_priority:
            tasks.sort(key=lambda task: (_PRIORITY_ORDER[task["priority"]], task["id"]))
        else:
            tasks.sort(key=lambda task: task["id"])
        return tasks

    def show(self, task_id: int) -> dict[str, Any]:
        return self._find_task(self._read(), task_id)

    def update(
        self,
        task_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        changes = {
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags,
        }
        if all(value is None for value in changes.values()):
            raise TodoError("at least one field must be provided")
        document = self._read()
        task = self._find_task(document, task_id)
        if title is not None:
            task["title"] = self._validated_title(title)
        if description is not None:
            if not isinstance(description, str):
                raise TodoError("description must be a string")
            task["description"] = description
        if priority is not None:
            task["priority"] = self._validated_priority(priority)
        if tags is not None:
            task["tags"] = self._validated_tags(tags)
        self._write(document)
        return task

    def set_status(self, task_id: int, status: str) -> dict[str, Any]:
        if status not in {"open", "completed"}:
            raise TodoError("status must be open or completed")
        document = self._read()
        task = self._find_task(document, task_id)
        task["status"] = status
        self._write(document)
        return task

    def delete(self, task_id: int) -> dict[str, int]:
        document = self._read()
        self._find_task(document, task_id)
        document["tasks"] = [task for task in document["tasks"] if task["id"] != task_id]
        self._write(document)
        return {"deleted_id": task_id}
