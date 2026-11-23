# Implementation Plan: Smart Todo CLI

## Design

- **Runtime:** Python 3.11+, standard library only.
- **CLI:** `argparse` subcommands; JSON success output to stdout and expected errors to stderr.
- **Domain/persistence:** a small service module validates task values and a versioned JSON store. Mutations serialize to a same-directory temporary file and replace the old file atomically.
- **Testing:** pytest uses temporary directories and invokes the public CLI contract; no test oracle is copied from implementation output.
- **Quality/security gates:** Ruff, Bandit, and pytest run independently through `.harness/run.py`.

## Key decisions

1. Use JSON and a single-user local store to keep the project small and inspectable (US-A-03, FR-A-003).
2. Avoid implicit timestamps so ordering and expected values stay deterministic (US-A-02, FR-A-002).
3. Keep the app standard-library-only; test tools are development dependencies only (FR-A-004).

## Component map

- `src/todo/cli.py`: argument parsing and command output.
- `src/todo/service.py`: task validation, lifecycle, filtering, and sorting.
- `src/todo/storage.py`: JSON validation and atomic persistence.
- `tests/`: specification-derived CLI contract cases.
- `.harness/`: independent quality-gate runner and machine-readable reports.
