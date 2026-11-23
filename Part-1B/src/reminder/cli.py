"""One-request JSON process boundary for the reminder agent."""

import json
import sys
from typing import Any

from reminder.agent import ReminderAgent
from reminder.errors import InputError, ModelOutputError, ProviderError


def _error(category: str, code: str) -> dict[str, dict[str, str]]:
    return {"error": {"category": category, "code": code}}


def _read_request(raw: str) -> tuple[Any, Any]:
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as error:
        raise InputError("request must be valid JSON") from error
    if not isinstance(request, dict) or set(request) != {"request", "now"}:
        raise InputError("request must contain exactly request and now")
    return request["request"], request["now"]


def main() -> int:
    try:
        text, now = _read_request(sys.stdin.read())
        result = ReminderAgent.from_environment().parse(text, now)
        exit_code = 0
    except InputError:
        result = _error("input_error", "invalid_request")
        exit_code = 2
    except ProviderError as error:
        result = _error(error.category, error.code)
        exit_code = 3
    except ModelOutputError as error:
        result = _error("model_output_error", error.code)
        exit_code = 4
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code
