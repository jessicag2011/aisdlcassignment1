"""Contract tests derived from the Smart Todo acceptance criteria."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(database: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(_ROOT / "src")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "todo",
            "--db",
            str(database),
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=_ROOT,
    )


def _json_output(result: subprocess.CompletedProcess[str]) -> Any:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout)


def _add(database: Path, title: str, *extra: str) -> dict[str, Any]:
    result = _run_cli(database, "add", "--title", title, *extra)
    return _json_output(result)


def test_add_has_specified_defaults_and_starts_ids_at_one(tmp_path: Path) -> None:
    task = _add(tmp_path / "todo.json", "Submit report")

    assert task == {
        "description": "",
        "id": 1,
        "priority": "medium",
        "status": "open",
        "tags": [],
        "title": "Submit report",
    }


def test_list_returns_persisted_tasks_in_json(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Submit report")

    result = _run_cli(database, "list")

    assert _json_output(result)["tasks"][0]["title"] == "Submit report"


def test_whitespace_title_fails_without_creating_store(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"

    result = _run_cli(database, "add", "--title", "   ")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "error: title must not be empty" in result.stderr
    assert not database.exists()


def test_update_persists_all_supported_fields(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Draft", "--tag", "work")

    result = _run_cli(
        database,
        "update",
        "1",
        "--title",
        "Review draft",
        "--description",
        "First pass",
        "--priority",
        "high",
        "--tag",
        "review",
    )

    assert _json_output(result) == {
        "description": "First pass",
        "id": 1,
        "priority": "high",
        "status": "open",
        "tags": ["review"],
        "title": "Review draft",
    }


def test_invalid_priority_is_rejected_by_cli(tmp_path: Path) -> None:
    result = _run_cli(tmp_path / "todo.json", "add", "--title", "Draft", "--priority", "urgent")

    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_unknown_task_id_has_stable_error(tmp_path: Path) -> None:
    result = _run_cli(tmp_path / "todo.json", "show", "42")

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() == "error: task not found: 42"


def test_complete_and_reopen_transition_status(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Draft")

    complete = _run_cli(database, "complete", "1")
    reopen = _run_cli(database, "reopen", "1")

    assert _json_output(complete)["status"] == "completed"
    assert _json_output(reopen)["status"] == "open"


def test_tag_filter_uses_exact_tag_membership(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Work", "--tag", "work")
    _add(database, "Workout", "--tag", "workout")

    result = _run_cli(database, "list", "--tag", "work")

    assert [task["title"] for task in _json_output(result)["tasks"]] == ["Work"]


def test_priority_sort_is_high_to_low_with_id_tie_break(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "First medium")
    _add(database, "Low", "--priority", "low")
    _add(database, "High", "--priority", "high")
    _add(database, "Second medium")

    result = _run_cli(database, "list", "--sort-priority")

    assert [task["title"] for task in _json_output(result)["tasks"]] == [
        "High",
        "First medium",
        "Second medium",
        "Low",
    ]


def test_delete_does_not_reuse_task_ids(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Keep")
    _add(database, "Remove")
    _json_output(_run_cli(database, "delete", "2"))

    created = _add(database, "New")

    assert created["id"] == 3


def test_mutation_survives_a_new_process(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Persisted")

    result = _run_cli(database, "show", "1")

    assert _json_output(result)["title"] == "Persisted"


def test_corrupt_json_is_not_overwritten(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    database.write_text("{broken", encoding="utf-8")

    result = _run_cli(database, "list")

    assert result.returncode == 2
    assert result.stderr.strip() == "error: invalid task store: malformed JSON"
    assert database.read_text(encoding="utf-8") == "{broken"


def test_invalid_next_id_is_rejected_without_rewrite(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    invalid = {
        "version": 1,
        "next_id": 1,
        "tasks": [
            {
                "id": 1,
                "title": "Existing",
                "description": "",
                "priority": "medium",
                "tags": [],
                "status": "open",
            }
        ],
    }
    original = json.dumps(invalid)
    database.write_text(original, encoding="utf-8")

    result = _run_cli(database, "list")

    assert result.returncode == 2
    assert result.stderr.strip() == "error: invalid task store: next_id must exceed all task IDs"
    assert database.read_text(encoding="utf-8") == original


def test_failed_update_does_not_change_store(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    _add(database, "Original")
    original = database.read_text(encoding="utf-8")

    result = _run_cli(database, "update", "1", "--title", "   ")

    assert result.returncode == 2
    assert result.stderr.strip() == "error: title must not be empty"
    assert database.read_text(encoding="utf-8") == original


def test_success_json_is_stdout_and_expected_errors_use_stderr(tmp_path: Path) -> None:
    database = tmp_path / "todo.json"
    success = _run_cli(database, "add", "--title", "Task")
    failure = _run_cli(database, "show", "9")

    assert json.loads(success.stdout)["id"] == 1
    assert success.stderr == ""
    assert failure.stdout == ""
    assert failure.stderr.startswith("error: ")
