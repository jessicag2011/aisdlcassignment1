# Artifact Consistency Review

Status: manual consistency review of the current files, not a GitHub Spec Kit `/speckit.analyze` result. The student evaluated the specs and directed the project to proceed; this review does not add a separate ACCEPT/REJECT label.

## Consistency findings

- The dataset has 18 unique `CASE-B-*` IDs, each with at least one requirement ID and a matching row in `traceability.csv`.
- Cases include representative create/reschedule/snooze behavior, missing information, ambiguous or past times, malformed input, unsupported requests, and prompt-injection/secret guardrails.
- The declared 0.80 semantic threshold and 1.0 guardrail requirement agree across the specification, evaluator, and offline threshold tests.
- Structural schema validation, deterministic property/guardrail checks, and semantic term scoring are separate stages in one evaluator pipeline.
- Gemini provider service errors are reported as `service_error` and are not scored as successful model outputs.
- Gemini API credentials are loaded only from `GEMINI_API_KEY`; the model defaults to `gemini-3.8-flash` and can be overridden with `GEMINI_MODEL`.
- Gemini interactions are non-stored; SDK retries and automatic continuation are disabled to preserve the one-call evaluation limit.
- The formal evaluator waits at least five seconds after each valid-case process before starting the next valid-case request and records the configured interval.
- The first paced trial passed preflight but timed out all 17 valid-case processes because the Interactions SDK per-call timeout was supplied in milliseconds instead of seconds; this was corrected.
- The subsequent paced run passed all preflight gates but still timed out all 17 valid-case processes at the harness boundary. It only scored the invalid-input case, does not establish model quality, and cannot confirm rate-limit behavior.

## Open items

- The first Gemini probe completed all preflight gates but confirmed that `gemini-2.5-flash` is unavailable to this account; the model was changed to Google's suggested `gemini-3.8-flash`.
- The full `gemini-3.8-flash` run also completed all four preflight gates, but the live evaluation did not pass: only the invalid-input case was scored; the 17 valid-request cases encountered provider-unavailable/rate-limit errors or application timeouts. This is not a model-quality result.
- A complete live evaluation with available service capacity and without request timeouts is still needed before claiming model quality.
- The student must write the harness log and record the human decision from actual evaluation evidence.
