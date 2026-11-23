"""Command-line interface for Smart Todo."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from todo.errors import StorageError, TodoError
from todo.service import TodoService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo")
    parser.add_argument("--db", type=Path, default=Path("tasks.json"))
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--description", default="")
    add.add_argument("--priority", choices=("low", "medium", "high"), default="medium")
    add.add_argument("--tag", action="append", default=[])

    listing = commands.add_parser("list")
    listing.add_argument("--tag")
    listing.add_argument("--status", choices=("open", "completed"))
    listing.add_argument("--sort-priority", action="store_true")

    show = commands.add_parser("show")
    show.add_argument("task_id", type=int)

    update = commands.add_parser("update")
    update.add_argument("task_id", type=int)
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--priority", choices=("low", "medium", "high"))
    update.add_argument("--tag", action="append")

    for name in ("complete", "reopen", "delete"):
        command = commands.add_parser(name)
        command.add_argument("task_id", type=int)
    return parser


def _execute(service: TodoService, arguments: argparse.Namespace) -> Any:
    if arguments.command == "add":
        return service.add(
            arguments.title, arguments.description, arguments.priority, arguments.tag
        )
    if arguments.command == "list":
        return {
            "tasks": service.list_tasks(
                arguments.tag, arguments.status, arguments.sort_priority
            )
        }
    if arguments.command == "show":
        return service.show(arguments.task_id)
    if arguments.command == "update":
        return service.update(
            arguments.task_id,
            title=arguments.title,
            description=arguments.description,
            priority=arguments.priority,
            tags=arguments.tag,
        )
    if arguments.command == "complete":
        return service.set_status(arguments.task_id, "completed")
    if arguments.command == "reopen":
        return service.set_status(arguments.task_id, "open")
    if arguments.command == "delete":
        return service.delete(arguments.task_id)
    raise TodoError(f"unsupported command: {arguments.command}")


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result = _execute(TodoService(arguments.db), arguments)
    except (StorageError, TodoError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0
