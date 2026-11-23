# Assignment 1: Spec-Driven Development and Harness Engineering

This repository contains two small Python applications based on the project recommendations in the supplied assignment materials:

| Part | Project | Validation focus |
|---|---|---|
| 1A | Smart Todo CLI | Deterministic task behavior, persistence, static checks, security scanning, and contract tests |
| 1B | Natural-Language Reminder Agent | Structured model output, deterministic invariants, guardrails, and a traceable evaluation dataset |

## Repository map

- [`Part-1A/`](./Part-1A/) contains the deterministic application and its specification-derived harness.
- [`Part-1B/`](./Part-1B/) contains the reminder agent, evaluation dataset, and unified evaluation runner.

Both projects use Python 3.11 or newer. Development checks use pytest, Ruff, and Bandit. Part 1B uses Google's `google-genai` SDK for optional Gemini API calls; no API key is stored in this repository.

## Verification status

The Part 1A deterministic harness has recorded local runs, including an actual lint failure followed by a passing run. The initial-generation snapshot was not preserved before the first local check, so do not claim that it was. Part 1B now uses the Gemini Developer API with its local `GEMINI_API_KEY`; its live evaluation status is recorded in the Part 1B evidence. Do not treat generated source or harness artifacts as student-reviewed or accepted without the student's review.

Both project folders are initialized with Spec Kit 1.4.3, the GitHub Copilot integration, and PowerShell scripts. Initialization installed the shared templates and `/speckit-*` skills; it did not execute those skills to regenerate or analyze the existing specifications. The student reports evaluating the spec files and directs the workflow to proceed; no formal ACCEPT/REJECT label is inferred from that direction.

Fresh-clone verification is preserved under each part's `evidence/`: Part 1A passed all gates; at fresh-clone time, Part 1B passed preflight and safely stopped before any model calls because configuration was absent.

The two `evidence/harness-log.md` files are intentionally left for the student to complete from actual runs. The assignment reflection, template problem statements, and submission identity fields are also student-authored.

## Traceability and AI-use note

Requirements, acceptance criteria, tests, and implementation tasks use stable `US-*`, `FR-*`, `AC-*`, `TASK-*`, and `CASE-*` identifiers. Commit subjects cite the relevant user-story and functional-requirement IDs so the Git history can be followed alongside the specifications.

AI assistance (Copilot SDK in VS Code) is being used under the student's direction to draft specifications, source code, tests, harnesses, and technical documentation. The student must review the changes and ensure this statement accurately reflects the final work. Harness-log entries and reflection prose are not generated here.

## Before submission

1. Review and approve both specifications, harnesses, datasets, and generated code.
2. Run each documented check and preserve its real output.
3. Write each harness log from actual evidence and record the human decision.
4. Confirm the GitHub repository visibility, scan files and history for secrets, and fill in the submission template yourself.
