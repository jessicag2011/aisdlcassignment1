import csv
import json
from pathlib import Path
from typing import Any

from evaluator import aggregate_results, evaluate_case

from reminder.schema import schema_findings

ROOT = Path(__file__).resolve().parents[1]


def _case(
    intent: str = "create",
    guardrail: bool = False,
) -> dict[str, Any]:
    return {
        "case_id": "CASE-TEST",
        "now": "2026-01-15T12:00:00Z",
        "expected": {
            "intent": intent,
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
        "guardrail": guardrail,
    }


def _response(
    title: str = "Call dentist",
    due_at: str = "2026-01-16T09:00:00Z",
) -> dict[str, Any]:
    return {
        "intent": "create",
        "reminder": {
            "title": title,
            "due_at": due_at,
            "reminder_id": None,
        },
        "clarification": None,
        "reason": None,
    }


def test_dataset_has_at_least_fifteen_unique_traceable_cases() -> None:
    dataset = json.loads((ROOT / "evals" / "dataset.json").read_text(encoding="utf-8"))
    cases = dataset["cases"]
    identifiers = [case["case_id"] for case in cases]

    assert len(cases) >= 15
    assert len(identifiers) == len(set(identifiers))
    assert all(case["requirement_ids"] for case in cases)
    assert any(case["guardrail"] for case in cases)
    assert any(case["category"] == "malformed-input" for case in cases)
    assert any(case["category"] == "ambiguous-date" for case in cases)
    with (ROOT / "specs" / "001-reminder-agent" / "traceability.csv").open(
        encoding="utf-8",
        newline="",
    ) as source:
        mapped = {row["case_id"] for row in csv.DictReader(source)}
    assert set(identifiers) == mapped


def test_schema_layer_rejects_unexpected_fields() -> None:
    response = _response()
    response["unrequested"] = True

    assert schema_findings(response) == ["OUTPUT_FIELDS"]


def test_property_layer_rejects_wrong_due_time_even_when_schema_is_valid() -> None:
    result = evaluate_case(_case(), _response(due_at="2026-01-16T10:00:00Z"))

    assert result["structural"]["passed"]
    assert not result["properties"]["passed"]
    assert "DUE_AT_MISMATCH" in result["properties"]["findings"]


def test_property_layer_rejects_action_when_clarification_is_expected() -> None:
    case = _case(intent="clarify", guardrail=True)
    case["semantic"] = {
        "field": "clarification",
        "required_terms": ["when"],
        "aliases": {},
        "prohibited_terms": [],
    }

    result = evaluate_case(case, _response())

    assert not result["properties"]["passed"]
    assert "INTENT_MISMATCH" in result["properties"]["findings"]


def test_semantic_layer_scores_required_terms_without_exact_string_matching() -> None:
    response = _response(title="Please call the dentist")

    result = evaluate_case(_case(), response)

    assert result["properties"]["passed"]
    assert result["semantic"]["score"] == 1.0
    assert result["semantic"]["matched_terms"] == ["call", "dentist"]


def test_semantic_layer_rejects_prohibited_guardrail_content() -> None:
    case = _case(guardrail=True)
    case["semantic"]["prohibited_terms"] = ["system prompt"]

    result = evaluate_case(case, _response(title="call dentist system prompt"))

    assert result["semantic"]["score"] == 0.0
    assert not result["properties"]["passed"]
    assert not result["passed"]


def test_expected_input_error_is_a_valid_case_outcome() -> None:
    case = {
        "case_id": "CASE-INPUT-ERROR",
        "requirement_ids": ["FR-B-005"],
        "guardrail": True,
        "expected_error_category": "input_error",
    }

    result = evaluate_case(
        case,
        {"error": {"category": "input_error", "code": "invalid_request"}},
    )

    assert result["passed"]
    assert result["structural"]["passed"]
    assert result["semantic"]["score"] == 1.0


def test_unexpected_error_is_not_treated_as_a_success() -> None:
    result = evaluate_case(
        _case(),
        {"error": {"category": "service_error", "code": "provider_timeout"}},
    )

    assert not result["passed"]
    assert not result["properties"]["passed"]


def test_aggregate_requires_every_property_check_and_the_semantic_threshold() -> None:
    good = evaluate_case(_case(), _response())
    failed = evaluate_case(_case(), _response(title="Review"))

    summary = aggregate_results([good, failed], threshold=0.80)

    assert summary["semantic_score"] == 0.5
    assert not summary["passed"]
    assert summary["properties_passed"]


def test_guardrail_case_must_score_exactly_one() -> None:
    case = _case(guardrail=True)
    result = evaluate_case(case, _response(title="Call dentist"))
    summary = aggregate_results([result], threshold=0.80)

    assert summary["guardrails_passed"]
    assert summary["passed"]
