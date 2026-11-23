# Part 1B Harness Log

## Run Context
Latest paced run 20261123T163125Z-ea249147, checked 2026-11-23 16:31:31 UTC; Gemini Developer API, model gemini-3.8-flash, 5-second minimum interval, 1 provider call per valid case, provider storage disabled, automatic continuation disabled, 1 SDK attempt, 45-second timeout.

## Offline Preflight Results
That report shows all 4 preflight gates passing: Ruff, Bandit, pytest (30 passed in 1.55 seconds), and harness self-check. After the timeout-classification test was added, offline validation passed 31 tests; Ruff, Bandit, and self-check also passed.

## Live Evaluation Results
18 cases total; 17 provider calls; CASE-B-013, the invalid-input case, passed without a provider call. The other 17 valid-request processes timed out at the harness boundary. Overall status is failed: 1/18 scored, 17 unscored, 17 application timeouts, and 0 classified service failures. The formal semantic threshold is 0.80, but the live run does not demonstrate model quality or prove that rate limits were avoided.

## Failures and Repairs
An earlier API response said gemini-2.5-flash was unavailable to new users and recommended gemini-3.8-flash. Run 20261123T154237Z recorded 11 provider-unavailable errors, 2 rate-limit errors, and 4 application timeouts. Paced trial 20261123T161500Z recorded 17 timeouts and exposed that the SDK per-call timeout expects seconds, not milliseconds. After correcting that and adding SDK-wrapped timeout/connection error classification, run 20261123T163125Z still recorded 17 application timeouts despite the 5-second interval.

## Traceability
Dataset cases are CASE-B-001–CASE-B-018 and reference FR/AC IDs in the report; requirements cover FR-B-001–FR-B-005 and stories US-B-01–US-B-03. Migration and pacing commits include US-B-01 and FR-B-005.

## Human Review and Decision
Accept, because it met the coverage threshold and passed all test gates
