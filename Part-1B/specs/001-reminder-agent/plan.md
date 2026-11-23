# Implementation Plan: Natural-Language Reminder Agent

## Design

- **Runtime:** Python 3.11+ with Anthropic SDK behind a small model-call adapter.
- **Interface:** one JSON request per process invocation; input includes synthetic user text and an explicit `now` reference.
- **Output:** exactly the schema in `spec.md`; validate independently before returning it.
- **Safety:** fixed system prompt, no tools, no side effects, bounded input size, secrets only from environment.
- **Evaluation:** external-process invocation over `evals/dataset.json`, followed by schema validation, property/guardrail checks, semantic rubric scoring, and a single aggregate decision.
- **Offline testing:** use injected fake model responses; these tests verify code paths and evaluator behavior, not live model quality.

## Key decisions

1. Use a structured decision with no external action so model output remains reviewable (US-B-01, US-B-03).
2. Supply `now` per case so relative-date checks are reproducible (FR-B-002).
3. Keep the dataset/evaluator/threshold outside the application package and report service errors separately (FR-B-004, FR-B-005).
4. Use a deterministic lexical rubric for semantic scoring and disclose its paraphrase limitations (FR-B-004).

## Component map

- `src/reminder/agent.py`: prompt assembly, model adapter, and validated response.
- `src/reminder/cli.py`: process boundary and JSON protocol.
- `evals/dataset.json`: synthetic evaluation cases and expected rubrics.
- `.harness/evaluate.py`: one three-layer evaluator and aggregate decision.
- `tests/`: offline application and independent evaluator tests.
