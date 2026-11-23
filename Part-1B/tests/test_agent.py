import json

import pytest

from reminder.agent import ReminderAgent
from reminder.errors import InputError, ModelOutputError, ProviderError


def _response(
    intent: str = "create",
    due_at: str = "2026-01-16T09:00:00Z",
) -> str:
    return json.dumps(
        {
            "intent": intent,
            "reminder": {
                "title": "Call dentist",
                "due_at": due_at,
                "reminder_id": None,
            },
            "clarification": None,
            "reason": None,
        }
    )


def test_agent_passes_fixed_reference_time_as_json_to_model() -> None:
    captured: dict[str, str] = {}

    def fake_model(system_prompt: str, user_message: str) -> str:
        captured["system"] = system_prompt
        captured["user"] = user_message
        return _response()

    agent = ReminderAgent(fake_model)
    parsed = agent.parse("Call the dentist tomorrow at 9am", "2026-01-15T12:00:00Z")

    assert parsed["reminder"]["due_at"] == "2026-01-16T09:00:00Z"
    assert json.loads(captured["user"]) == {
        "now": "2026-01-15T12:00:00Z",
        "request": "Call the dentist tomorrow at 9am",
    }
    assert "Do not call tools" in captured["system"]


def test_invalid_user_input_does_not_call_model() -> None:
    called = False

    def fake_model(system_prompt: str, user_message: str) -> str:
        nonlocal called
        called = True
        return _response()

    agent = ReminderAgent(fake_model)

    with pytest.raises(InputError, match="non-empty"):
        agent.parse(" ", "2026-01-15T12:00:00Z")
    assert not called


def test_invalid_reference_time_is_rejected_before_model_call() -> None:
    agent = ReminderAgent(lambda _system, _user: _response())

    with pytest.raises(InputError, match="UTC timestamp"):
        agent.parse("Call the dentist", "not-a-time")


def test_empty_model_text_is_reported_as_invalid_json() -> None:
    agent = ReminderAgent(lambda _system, _user: "not JSON")

    with pytest.raises(ModelOutputError, match="invalid_json"):
        agent.parse("Call the dentist tomorrow at 9am", "2026-01-15T12:00:00Z")


def test_model_output_with_extra_fields_is_rejected() -> None:
    malformed = json.loads(_response())
    malformed["extra"] = "not allowed"
    agent = ReminderAgent(lambda _system, _user: json.dumps(malformed))

    with pytest.raises(ModelOutputError, match="schema_violation"):
        agent.parse("Call the dentist tomorrow at 9am", "2026-01-15T12:00:00Z")


def test_past_model_due_time_is_rejected() -> None:
    agent = ReminderAgent(lambda _system, _user: _response(due_at="2026-01-15T11:00:00Z"))

    with pytest.raises(ModelOutputError, match="due_at_not_future"):
        agent.parse("Call the dentist yesterday", "2026-01-15T12:00:00Z")


def test_missing_api_key_is_a_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")

    with pytest.raises(ProviderError, match="missing_api_key") as error:
        ReminderAgent.from_environment()
    assert error.value.category == "configuration_error"


def test_missing_model_is_a_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-real-test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    with pytest.raises(ProviderError, match="missing_model") as error:
        ReminderAgent.from_environment()
    assert error.value.category == "configuration_error"
