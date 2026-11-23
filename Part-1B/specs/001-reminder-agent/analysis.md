# Artifact Consistency Review

Status: manual consistency review of the current files, not a GitHub Spec Kit `/speckit.analyze` result and not a student approval.

## Consistency findings

- The dataset has 18 unique `CASE-B-*` IDs, each with at least one requirement ID and a matching row in `traceability.csv`.
- Cases include representative create/reschedule/snooze behavior, missing information, ambiguous or past times, malformed input, unsupported requests, and prompt-injection/secret guardrails.
- The declared 0.80 semantic threshold and 1.0 guardrail requirement agree across the specification, evaluator, and offline threshold tests.
- Structural schema validation, deterministic property/guardrail checks, and semantic term scoring are separate stages in one evaluator pipeline.
- Provider service errors are reported as `service_error` and are not scored as successful model outputs.

## Open items

- The Spec Kit CLI workflow and student review checkpoint were not performed.
- The live model evaluation is blocked until a model and API key are configured locally.
- No provider-specific behavior or output quality claim is supported yet.
- The student must review the model results, write the harness log, and make the human decision after a real evaluation.
