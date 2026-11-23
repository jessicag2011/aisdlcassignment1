# Smart Todo Constitution

## Purpose and scope

Build a small, single-user command-line task manager. The program manages tasks in a local JSON file and does not provide authentication, collaboration, reminders, recurring tasks, or a network API.

## Technical constraints

1. Use Python 3.11 or newer and the Python standard library for runtime code.
2. Keep the application usable through `python -m todo`; do not bind a fixed network port.
3. Persist one versioned JSON object with a monotonically increasing `next_id` and a list of tasks. Write updates atomically using a temporary file in the same directory and `os.replace`.
4. Validate loaded data and user input. Report malformed data and invalid operations as non-zero command failures; never silently replace a corrupt store.
5. Keep task behavior deterministic: do not infer timestamps or sort ties from wall-clock time.

## Quality gates

1. Acceptance criteria in `specs/001-smart-todo/spec.md` are the source of truth for tests.
2. Run pytest, Ruff, and Bandit as separate, explicit harness gates.
3. Do not modify tests, specification-derived expected values, harness checks, or scanner settings to make a failing run pass.
4. Do not commit credentials, user data, or local environment files.
5. Keep source modules focused and provide stable, actionable error messages.

## Traceability

Every implementation task cites its user-story or functional-requirement ID. Every acceptance criterion maps to at least one test or a documented reason it is not directly executable.
