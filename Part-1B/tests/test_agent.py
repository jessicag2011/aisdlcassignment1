import json
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai.errors import APIError

import reminder.agent as agent_module
from reminder.agent import DEFAULT_MODEL, ReminderAgent
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


def _interactions_api_error(status_code: int) -> Exception:
    response = httpx.Response(
        status_code,
        request=httpx.Request("POST", "https://example.test/interactions"),
    )
    return agent_module.InteractionsAPIError.generate(
        status_code,
        {"error": {"message": "provider request failed"}},
        "provider request failed",
        response,
    )


def _interactions_timeout_error() -> Exception:
    request = httpx.Request("POST", "https://example.test/interactions")
    return agent_module.InteractionsTimeoutError(request)


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


def test_gemini_configuration_uses_model_default_and_stateless_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeInteractions:
        def create(self, **kwargs: Any) -> SimpleNamespace:
            captured["request"] = kwargs
            return SimpleNamespace(output_text=_response())

    class FakeClient:
        def __init__(self, *, api_key: str, http_options: Any) -> None:
            captured["api_key"] = api_key
            captured["http_options"] = http_options
            self.interactions = FakeInteractions()

    monkeypatch.setattr(agent_module, "load_dotenv", lambda **_: None)
    monkeypatch.setattr(agent_module.genai, "Client", FakeClient)
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    agent = ReminderAgent.from_environment()
    parsed = agent.parse("Call the dentist tomorrow at 9am", "2026-01-15T12:00:00Z")

    request = captured["request"]
    http_options = captured["http_options"]
    assert parsed["intent"] == "create"
    assert captured["api_key"] == "not-a-real-test-key"
    assert request["model"] == DEFAULT_MODEL
    assert request["store"] is False
    assert request["automatic_continuation"] is False
    assert request["response_format"]["mime_type"] == "application/json"
    assert request["system_instruction"] == agent_module.SYSTEM_PROMPT
    assert request["timeout"] == agent_module.REQUEST_TIMEOUT_SECONDS
    assert http_options.timeout == int(agent_module.REQUEST_TIMEOUT_SECONDS * 1000)
    assert http_options.retry_options.attempts == 1


def test_missing_gemini_api_key_is_a_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_module, "load_dotenv", lambda **_: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ProviderError, match="missing_api_key") as error:
        ReminderAgent.from_environment()
    assert error.value.category == "configuration_error"


@pytest.mark.parametrize(
    ("exception", "category", "code"),
    [
        (APIError(429, {"message": "limited"}), "service_error", "provider_rate_limited"),
        (APIError(503, {"message": "unavailable"}), "service_error", "provider_unavailable"),
        (
            APIError(400, {"message": "invalid request"}),
            "provider_error",
            "provider_request_failed",
        ),
        (_interactions_api_error(404), "provider_error", "model_unavailable"),
        (httpx.TimeoutException("timed out"), "service_error", "provider_timeout"),
        (_interactions_timeout_error(), "service_error", "provider_timeout"),
        (httpx.ConnectError("connection failed"), "service_error", "provider_unavailable"),
    ],
)
def test_gemini_provider_failures_are_classified(
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    category: str,
    code: str,
) -> None:
    class FakeInteractions:
        def create(self, **_kwargs: Any) -> None:
            raise exception

    class FakeClient:
        def __init__(self, **_kwargs: Any) -> None:
            self.interactions = FakeInteractions()

    monkeypatch.setattr(agent_module, "load_dotenv", lambda **_: None)
    monkeypatch.setattr(agent_module.genai, "Client", FakeClient)
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-test-key")

    agent = ReminderAgent.from_environment()
    with pytest.raises(ProviderError, match=code) as error:
        agent.parse("Call the dentist tomorrow at 9am", "2026-01-15T12:00:00Z")
    assert error.value.category == category
