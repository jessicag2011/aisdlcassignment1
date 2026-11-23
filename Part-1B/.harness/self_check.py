"""Demonstrate that each deterministic evaluator layer rejects a broken response."""

import json
from typing import Any

from evaluator import evaluate_case


def _case() -> dict[str, Any]:
    return {
        "case_id": "SELF-CHECK",
        "now": "2026-01-15T12:00:00Z",
        "expected": {
            "intent": "create",
            "due_at": "2026-01-16T09:00:00Z",
            "reminder_id": None,
        },
        "semantic": {
            "field": "reminder.title",
            "required_terms": ["call", "dentist"],
            "aliases": {},
            "prohibited_terms": [],
        },
        "requirement_ids": ["FR-B-001", "FR-B-002"],
        "guardrail": False,
    }


def _response() -> dict[str, Any]:
    return {
        "intent": "create",
        "reminder": {
            "title": "Call dentist",
            "due_at": "2026-01-16T09:00:00Z",
            "reminder_id": None,
        },
        "clarification": None,
        "reason": None,
    }


def run_self_check() -> dict[str, Any]:
    case = _case()
    good = evaluate_case(case, _response())

    invalid_structure = _response()
    invalid_structure["extra"] = "not allowed"
    structural_failure = evaluate_case(case, invalid_structure)

    wrong_property = _response()
    wrong_property["reminder"]["due_at"] = "2026-01-16T10:00:00Z"
    property_failure = evaluate_case(case, wrong_property)

    semantically_wrong = _response()
    semantically_wrong["reminder"]["title"] = "Review budget"
    semantic_failure = evaluate_case(case, semantically_wrong)
    report = {
        "passed": (
            good["passed"]
            and not structural_failure["structural"]["passed"]
            and not property_failure["properties"]["passed"]
            and semantic_failure["semantic"]["score"] == 0.0
        ),
        "checks": {
            "good_response_passed_all_layers": good["passed"],
            "structure_rejected_extra_field": not structural_failure["structural"]["passed"],
            "property_rejected_wrong_due_time": not property_failure["properties"]["passed"],
            "semantic_scored_wrong_title_zero": semantic_failure["semantic"]["score"] == 0.0,
        },
    }
    return report


if __name__ == "__main__":
    result = run_self_check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
