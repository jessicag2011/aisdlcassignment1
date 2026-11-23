"""Independent structural validation for model responses."""

import re
from datetime import datetime
from typing import Any

_INTENTS = {"create", "reschedule", "snooze", "clarify", "refuse"}
_TOP_LEVEL_FIELDS = {"intent", "reminder", "clarification", "reason"}
_REMINDER_FIELDS = {"title", "due_at", "reminder_id"}
_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not _UTC_TIMESTAMP.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed


def schema_findings(response: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(response, dict) or set(response) != _TOP_LEVEL_FIELDS:
        return ["OUTPUT_FIELDS"]
    intent = response["intent"]
    if not isinstance(intent, str) or intent not in _INTENTS:
        findings.append("INTENT_ENUM")
        return findings
    reminder = response["reminder"]
    clarification = response["clarification"]
    reason = response["reason"]

    if intent in {"create", "reschedule", "snooze"}:
        if not isinstance(reminder, dict) or set(reminder) != _REMINDER_FIELDS:
            findings.append("REMINDER_SHAPE")
        else:
            if not isinstance(reminder["title"], str) or not reminder["title"].strip():
                findings.append("REMINDER_TITLE")
            if parse_utc_timestamp(reminder["due_at"]) is None:
                findings.append("REMINDER_DUE_AT")
            reminder_id = reminder["reminder_id"]
            if reminder_id is not None and (
                not isinstance(reminder_id, str) or not reminder_id.strip()
            ):
                findings.append("REMINDER_ID")
            if intent == "create" and reminder_id is not None:
                findings.append("CREATE_ID_MUST_BE_NULL")
            if intent in {"reschedule", "snooze"} and reminder_id is None:
                findings.append("EXISTING_ID_REQUIRED")
        if clarification is not None or reason is not None:
            findings.append("ACTION_FIELDS")
    elif intent == "clarify":
        if reminder is not None:
            findings.append("CLARIFY_HAS_ACTION")
        if not isinstance(clarification, str) or not clarification.strip():
            findings.append("CLARIFICATION_REQUIRED")
        if reason is not None:
            findings.append("CLARIFY_REASON")
    elif intent == "refuse":
        if reminder is not None:
            findings.append("REFUSAL_HAS_ACTION")
        if clarification is not None:
            findings.append("REFUSAL_CLARIFICATION")
        if not isinstance(reason, str) or not reason.strip():
            findings.append("REFUSAL_REASON_REQUIRED")
    return findings
