# Implementation Tasks

- [ ] **TASK-B-001 — Implement the strict JSON contract** (`US-B-01`, `FR-B-001`, `AC-B-001`, `AC-B-015`): validate exact keys, types, enum, and intent-dependent fields.
- [ ] **TASK-B-002 — Add the Gemini model boundary and prompt** (`US-B-01`, `FR-B-001`, `FR-B-002`, `FR-B-005`): accept explicit reference time, treat user input as data, and expose a stateless, no-retry Gemini adapter.
- [ ] **TASK-B-003 — Add ambiguity and safety handling** (`US-B-02`, `US-B-03`, `FR-B-002`, `FR-B-003`): clarify missing or unsafe-to-guess details; refuse out-of-scope requests.
- [ ] **TASK-B-004 — Create the traceable evaluation dataset** (`FR-B-004`, `AC-B-001`–`AC-B-018`): include normal, boundary, ambiguous, malformed, and guardrail cases with expected properties and semantic rubrics.
- [ ] **TASK-B-005 — Implement the unified evaluator** (`FR-B-004`, `FR-B-005`): structural validation, property/guardrail checks, semantic scoring, error classification, and aggregate threshold.
- [ ] **TASK-B-006 — Add offline tests and self-checks** (`FR-B-001`–`FR-B-005`): use injected fake outputs to verify each evaluation layer can reject invalid behavior without calling a live model.
- [ ] **TASK-B-007 — Review live evaluation and record decision** (`US-B-01`–`US-B-03`): student reviews the actual provider report and writes the harness log and human decision.
- [x] **TASK-B-008 — Migrate provider to Gemini** (`US-B-01`, `FR-B-005`): use Gemini Interactions with `GEMINI_API_KEY`, stateless requests, and retries/continuation disabled.
