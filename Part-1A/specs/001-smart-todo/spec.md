# Feature Specification: Smart Todo CLI

## Problem and scope

An individual user needs a reliable local command-line task list for creating, viewing, editing, completing, reopening, filtering, sorting, and deleting tasks. The application stores tasks in a JSON file. It has no account system, synchronization, collaboration, reminders, recurrence, or HTTP service.

## User stories

### US-A-01: Maintain a task list

As an individual user, I want to create, inspect, edit, and delete tasks so that I can keep a local record of work.

### US-A-02: Organize and transition tasks

As an individual user, I want to set priorities and tags, filter and sort tasks, and change task status so that I can focus on the right work.

### US-A-03: Keep task data across runs

As an individual user, I want valid changes saved to a JSON file so that tasks remain available after the command exits.

## Functional requirements

- **FR-A-001 — Task lifecycle:** accept a non-empty title; assign positive integer IDs; support list, show, update, and delete; reject unknown IDs and invalid fields with a non-zero exit status.
- **FR-A-002 — Organization and status:** support `low`, `medium`, and `high` priority; string tags; `open` and `completed` states; exact tag filtering; and deterministic priority sorting.
- **FR-A-003 — Persistence:** use a versioned JSON document with `next_id`; validate it before use; preserve it across invocations; atomically replace it only after a valid mutation.
- **FR-A-004 — CLI contract:** expose documented subcommands, machine-readable JSON output, and errors on stderr without traceback for expected user errors.

## Acceptance criteria

| ID | Given / When / Then | Covers |
|---|---|---|
| AC-A-001 | Given an empty store, when a task is added with a non-empty title, then it is stored with ID 1, priority `medium`, and status `open`. | FR-A-001, FR-A-003 |
| AC-A-002 | Given an existing task, when it is listed, then the JSON output includes that task and its persisted fields. | FR-A-001, FR-A-004 |
| AC-A-003 | Given a title containing only whitespace, when a task is added, then the command fails and the store remains unchanged. | FR-A-001 |
| AC-A-004 | Given an existing task, when its title, description, priority, or tags are updated with valid values, then the requested values are persisted. | FR-A-001, FR-A-003 |
| AC-A-005 | Given an invalid priority, when a task is created or updated, then the command fails without changing the store. | FR-A-001, FR-A-002 |
| AC-A-006 | Given an unknown task ID, when it is shown, updated, completed, reopened, or deleted, then the command fails with a stable user-facing error. | FR-A-001, FR-A-004 |
| AC-A-007 | Given an open task, when it is completed, then its status becomes `completed`. | FR-A-002 |
| AC-A-008 | Given a completed task, when it is reopened, then its status becomes `open`. | FR-A-002 |
| AC-A-009 | Given tasks with and without a requested tag, when filtered by that tag, then only tasks containing the exact tag are returned. | FR-A-002 |
| AC-A-010 | Given tasks with priorities `high`, `medium`, and `low`, when sorted by priority, then output order is high, medium, low, with IDs ascending within each priority. | FR-A-002 |
| AC-A-011 | Given a deleted task, when the store is read again, then that task is absent and existing IDs are not reused. | FR-A-001, FR-A-003 |
| AC-A-012 | Given a valid mutation, when the process exits and a new process reads the same file, then the mutation is present. | FR-A-003 |
| AC-A-013 | Given malformed or unsupported-version JSON, when a command reads the store, then the command fails and does not overwrite the file. | FR-A-003 |
| AC-A-014 | Given a mutation whose replacement cannot be completed, when persistence fails, then the previous store remains intact and the command reports failure. | FR-A-003 |
| AC-A-015 | Given a successful command, when output is captured, then stdout is valid JSON and expected user errors are emitted on stderr with a non-zero exit code. | FR-A-004 |

## Data contract

The persisted document is exactly `{"version": 1, "next_id": <positive integer>, "tasks": [<task>, ...]}`. A task has `id` (positive integer), `title` (non-empty string), `description` (string), `priority` (`low|medium|high`), `tags` (array of strings), and `status` (`open|completed`). Task IDs are unique, and `next_id` is greater than every existing ID.

## Non-functional constraints

- Runtime uses only the standard library.
- The application must not expose secrets or read outside the explicitly selected store path.
- Harness expectations are specification-derived and do not import harness code into the application.
- A corrupt store is surfaced, not silently repaired or reset.
