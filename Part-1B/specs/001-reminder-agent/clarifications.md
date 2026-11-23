# Clarifications: Natural-Language Reminder Agent

| ID | Question | Decision | Affected requirement |
|---|---|---|---|
| CL-B-001 | Does the application execute reminders? | No. It parses and evaluates requests only; there are no scheduling side effects. | FR-B-003 |
| CL-B-002 | What time zone is emitted? | Normalize valid timestamps to UTC RFC 3339 with a trailing `Z`. | FR-B-001, FR-B-002 |
| CL-B-003 | What is mandatory to create a reminder? | A non-empty task title and an unambiguous future time. Missing values require clarification. | FR-B-002 |
| CL-B-004 | What is mandatory to reschedule or snooze? | A resolvable reminder ID and an unambiguous future due time. The agent must not invent an ID. | FR-B-002 |
| CL-B-005 | How is relative time made testable? | Each evaluation case supplies an explicit UTC `now` reference; date interpretation is relative to that value. | FR-B-002, FR-B-004 |
| CL-B-006 | How is semantic quality scored? | Use per-case required/prohibited term rubrics; report the lexical metric and its paraphrase limitation. | FR-B-004 |
| CL-B-007 | What is the repair/evaluation boundary? | The dataset, evaluator, properties, and threshold are protected inputs; application or prompt changes cannot modify them. | FR-B-004 |
| CL-B-008 | How are service retries handled? | No SDK auto-retry; report transient service errors separately so results are not silently masked. | FR-B-005 |
| CL-B-009 | Which model provider and configuration are used? | Use Gemini Developer API through `google-genai`; read `GEMINI_API_KEY`, default to `gemini-3.8-flash`, permit a `GEMINI_MODEL` override, and send non-stored interactions without retries or continuation. | FR-B-005 |
| CL-B-010 | How are live requests paced? | Formal evaluation waits at least five seconds after each valid-case process before starting the next valid-case request; expected-input-error cases do not call the provider. | FR-B-005 |
