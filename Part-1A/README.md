# Part 1A: Smart Todo CLI

A deterministic, single-user task manager backed by a local JSON file. It supports add, list, show, update, complete, reopen, delete, tag filtering, and priority sorting.

## Requirements

- Python 3.11 or newer
- Install development checks in a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Run

From `Part-1A`, use `PYTHONPATH=src` or install the package in editable mode. In PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m todo --db .\tasks.json add --title "Submit report" --priority high --tag school
python -m todo --db .\tasks.json list --tag school --sort-priority
python -m todo --db .\tasks.json complete 1
```

Use `python -m todo --help` for the full command contract. The database path is explicit and defaults to `tasks.json` in the current directory. Do not store private data in a submitted evidence file.

## Checks

```powershell
python .harness\run.py
```

The runner executes Ruff, Bandit, and pytest as independent gates and saves a JSON report under `evidence/harness-results/`. It returns non-zero unless all gates pass. Tests are driven by the acceptance criteria in `specs/001-smart-todo/spec.md`.

## Traceability

- Specification and IDs: [`specs/001-smart-todo/spec.md`](./specs/001-smart-todo/spec.md)
- Clarifications: [`specs/001-smart-todo/clarifications.md`](./specs/001-smart-todo/clarifications.md)
- Manual consistency review: [`specs/001-smart-todo/analysis.md`](./specs/001-smart-todo/analysis.md); this is not a Spec Kit CLI output.
- Plan and task links: [`specs/001-smart-todo/plan.md`](./specs/001-smart-todo/plan.md), [`specs/001-smart-todo/tasks.md`](./specs/001-smart-todo/tasks.md)
- Criterion-to-test map: [`specs/001-smart-todo/traceability.csv`](./specs/001-smart-todo/traceability.csv)
- Final source copy: [`evidence/final-generation/`](./evidence/final-generation/). The initial-generation copy was not captured before the first local harness run.

## Limitations

This is a local, single-user program. Concurrent writers, backup/restore, synchronization, authentication, and due-date reminders are out of scope.

The harness log at `evidence/harness-log.md` is intentionally reserved for the student to complete from actual runs and their own review.

The fresh-clone report is [`evidence/harness-results/fresh-clone-20261123T145647Z-3cbaf93c/report.json`](./evidence/harness-results/fresh-clone-20261123T145647Z-3cbaf93c/report.json).
