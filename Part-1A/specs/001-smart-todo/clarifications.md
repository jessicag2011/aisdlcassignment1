# Clarifications: Smart Todo CLI

These decisions resolve behavior needed to make the specification testable.

| ID | Question | Decision | Affected requirement |
|---|---|---|---|
| CL-A-001 | What are initial status and priority? | New tasks use status `open` and priority `medium`. | FR-A-001, FR-A-002 |
| CL-A-002 | Can a deleted task ID be reused? | No. `next_id` only increases. | FR-A-003 |
| CL-A-003 | How are priority-sort ties resolved? | Task ID ascending within each priority. | FR-A-002 |
| CL-A-004 | How are tags compared? | Exact, case-sensitive string equality; duplicate tags are removed while retaining first occurrence. | FR-A-002 |
| CL-A-005 | What happens when stored JSON is invalid? | Fail with a data error and leave the file unchanged. No automatic reset or migration is performed. | FR-A-003 |
| CL-A-006 | Are dates or timestamps part of this version? | No. They are outside the feature scope. | FR-A-001 |
