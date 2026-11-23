import json
from subprocess import CompletedProcess
from typing import Any

import evaluate
import pytest


def test_provider_failure_is_reported_as_a_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {"error": {"category": "service_error", "code": "provider_timeout"}}

    def fake_run(*_arguments: Any, **_options: Any) -> CompletedProcess[str]:
        return CompletedProcess(
            args=["python", "-m", "reminder"],
            returncode=3,
            stdout=json.dumps(response),
            stderr="",
        )

    monkeypatch.setattr(evaluate.subprocess, "run", fake_run)

    actual, failure_class = evaluate._invoke_app(
        {
            "input": "A synthetic reminder request",
            "now": "2026-01-15T12:00:00Z",
        }
    )

    assert actual == response
    assert failure_class == "service_error"


def test_report_redacts_common_provider_secret_formats() -> None:
    source = {"reason": "Observed sk-ant-abcdefghijklmnopqrstuvwxyz0123456789"}

    redacted, was_redacted = evaluate._redact_output(source)

    assert was_redacted
    assert "sk-ant-" not in redacted["reason"]
    assert "[REDACTED]" in redacted["reason"]
