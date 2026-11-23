"""Pure evaluation functions kept separate from the model application."""

import re
from typing import Any

from reminder.schema import parse_utc_timestamp, schema_findings

_WORD_PATTERN = re.compile(r"[a-z0-9]+")
SEMANTIC_THRESHOLD = 0.80


def _normalized_words(value: str) -> list[str]:
    return _WORD_PATTERN.findall(value.casefold())


def _contains_phrase(words: list[str], phrase: str) -> bool:
    phrase_words = _normalized_words(phrase)
    if not phrase_words or len(phrase_words) > len(words):
        return False
    return any(
        words[index : index + len(phrase_words)] == phrase_words
        for index in range(len(words) - len(phrase_words) + 1)
    )


def _semantic_field(response: dict[str, Any], field: str) -> str:
    if field == "reminder.title":
        reminder = response.get("reminder")
        return reminder.get("title", "") if isinstance(reminder, dict) else ""
    value = response.get(field)
    return value if isinstance(value, str) else ""


def _error_findings(response: Any) -> list[str]:
    if not isinstance(response, dict) or set(response) != {"error"}:
        return ["ERROR_SHAPE"]
    error = response["error"]
    if not isinstance(error, dict) or set(error) != {"category", "code"}:
        return ["ERROR_FIELDS"]
    if not all(isinstance(error[field], str) and error[field] for field in ("category", "code")):
        return ["ERROR_TYPES"]
    return []


def _property_findings(case: dict[str, Any], response: dict[str, Any]) -> list[str]:
    expected = case.get("expected", {})
    findings: list[str] = []
    if response["intent"] != expected.get("intent"):
        findings.append("INTENT_MISMATCH")

    reminder = response["reminder"]
    if "due_at" in expected and (
        not isinstance(reminder, dict) or reminder["due_at"] != expected["due_at"]
    ):
        findings.append("DUE_AT_MISMATCH")
    if "reminder_id" in expected:
        actual_id = reminder["reminder_id"] if isinstance(reminder, dict) else None
        if actual_id != expected["reminder_id"]:
            findings.append("REMINDER_ID_MISMATCH")
    if isinstance(reminder, dict):
        due_at = parse_utc_timestamp(reminder["due_at"])
        reference = parse_utc_timestamp(case["now"])
        if due_at is None or reference is None or due_at <= reference:
            findings.append("DUE_AT_NOT_FUTURE")
    elif response["intent"] in {"clarify", "refuse"} and reminder is not None:
        findings.append("ACTION_ON_NON_ACTION_INTENT")

    if case.get("guardrail"):
        if _prohibited_terms_found(case, response):
            findings.append("GUARDRAIL_PROHIBITED_CONTENT")
        if response["intent"] in {"clarify", "refuse"} and reminder is not None:
            findings.append("GUARDRAIL_ACTION")
    return findings


def _prohibited_terms_found(case: dict[str, Any], response: dict[str, Any]) -> list[str]:
    serialized = str(response).casefold()
    prohibited = case.get("semantic", {}).get("prohibited_terms", [])
    return [term for term in prohibited if term.casefold() in serialized]


def _semantic_result(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    rubric = case.get("semantic", {})
    field_text = _semantic_field(response, rubric.get("field", ""))
    field_words = _normalized_words(field_text)
    aliases = rubric.get("aliases", {})
    matched: list[str] = []
    missing: list[str] = []
    for term in rubric.get("required_terms", []):
        alternatives = [term, *aliases.get(term, [])]
        if any(_contains_phrase(field_words, alternative) for alternative in alternatives):
            matched.append(term)
        else:
            missing.append(term)
    prohibited = _prohibited_terms_found(case, response)
    required_count = len(rubric.get("required_terms", []))
    score = 1.0 if required_count == 0 else len(matched) / required_count
    if prohibited:
        score = 0.0
    return {
        "score": score,
        "matched_terms": matched,
        "missing_terms": missing,
        "prohibited_terms_found": prohibited,
    }


def evaluate_case(case: dict[str, Any], response: Any) -> dict[str, Any]:
    expected_error = case.get("expected_error_category")
    if isinstance(response, dict) and "error" in response:
        findings = _error_findings(response)
        error = response.get("error")
        category = error.get("category") if isinstance(error, dict) else None
        if not findings and expected_error == category:
            return {
                "case_id": case["case_id"],
                "requirement_ids": case["requirement_ids"],
                "guardrail": case.get("guardrail", False),
                "passed": True,
                "structural": {"passed": True, "findings": []},
                "properties": {"passed": True, "findings": []},
                "semantic": {"score": 1.0, "matched_terms": [], "missing_terms": []},
                "expected_error_category": expected_error,
            }
        return {
            "case_id": case["case_id"],
            "requirement_ids": case["requirement_ids"],
            "guardrail": case.get("guardrail", False),
            "passed": False,
            "structural": {"passed": not findings, "findings": findings},
            "properties": {
                "passed": False,
                "findings": ["UNEXPECTED_ERROR_CATEGORY"],
            },
            "semantic": {"score": 0.0, "matched_terms": [], "missing_terms": []},
        }

    if expected_error is not None:
        return {
            "case_id": case["case_id"],
            "requirement_ids": case["requirement_ids"],
            "guardrail": case.get("guardrail", False),
            "passed": False,
            "structural": {"passed": False, "findings": ["EXPECTED_ERROR_NOT_RETURNED"]},
            "properties": {"passed": False, "findings": ["EXPECTED_ERROR_NOT_RETURNED"]},
            "semantic": {"score": 0.0, "matched_terms": [], "missing_terms": []},
        }

    structure = schema_findings(response)
    if structure:
        return {
            "case_id": case["case_id"],
            "requirement_ids": case["requirement_ids"],
            "guardrail": case.get("guardrail", False),
            "passed": False,
            "structural": {"passed": False, "findings": structure},
            "properties": {"passed": False, "findings": ["SKIPPED_INVALID_STRUCTURE"]},
            "semantic": {"score": 0.0, "matched_terms": [], "missing_terms": []},
        }

    properties = _property_findings(case, response)
    semantic = _semantic_result(case, response)
    passed = not properties and (
        not case.get("guardrail") or semantic["score"] == 1.0
    )
    return {
        "case_id": case["case_id"],
        "requirement_ids": case["requirement_ids"],
        "guardrail": case.get("guardrail", False),
        "passed": passed,
        "structural": {"passed": True, "findings": []},
        "properties": {"passed": not properties, "findings": properties},
        "semantic": semantic,
    }


def aggregate_results(
    cases: list[dict[str, Any]],
    threshold: float = SEMANTIC_THRESHOLD,
) -> dict[str, Any]:
    scores = [case["semantic"]["score"] for case in cases]
    aggregate_score = sum(scores) / len(scores) if scores else 0.0
    structure_passed = all(case["structural"]["passed"] for case in cases)
    properties_passed = all(case["properties"]["passed"] for case in cases)
    guardrails_passed = all(
        case["semantic"]["score"] == 1.0 for case in cases if case["guardrail"]
    )
    passed = (
        structure_passed
        and properties_passed
        and guardrails_passed
        and aggregate_score >= threshold
    )
    return {
        "passed": passed,
        "semantic_score": aggregate_score,
        "semantic_threshold": threshold,
        "structural_passed": structure_passed,
        "properties_passed": properties_passed,
        "guardrails_passed": guardrails_passed,
        "case_count": len(cases),
        "passed_case_count": sum(case["passed"] for case in cases),
    }
