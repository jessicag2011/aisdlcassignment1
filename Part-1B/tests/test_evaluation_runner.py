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
    source = {
        "anthropic": "sk-ant-abcdefghijklmnopqrstuvwxyz0123456789",
        "gemini": "AIzaSyDUMMYKEY012345678901234567890123456789",
    }

    redacted, was_redacted = evaluate._redact_output(source)

    assert was_redacted
    assert redacted == {"anthropic": "[REDACTED]", "gemini": "[REDACTED]"}


def test_missing_gemini_key_blocks_before_model_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(evaluate, "load_dotenv", lambda **_kwargs: None)
    monkeypatch.setattr(evaluate, "_preflight", lambda: [{"passed": True}])
    monkeypatch.setattr(
        evaluate,
        "_invoke_app",
        lambda _case: pytest.fail("model must not be called without a Gemini key"),
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    report, exit_code = evaluate.run_evaluation(evaluate.DATASET_PATH, tmp_path)

    assert exit_code == 2
    assert report["status"] == "blocked_configuration"
    assert report["model"] == evaluate.DEFAULT_MODEL
    assert report["summary"]["model_calls"] == 0
    assert "GEMINI_API_KEY" in report["summary"]["message"]


def test_report_counts_unscored_provider_failures_in_dataset_totals(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    cases = [
        {
            "case_id": "CASE-B-001",
            "requirement_ids": ["FR-B-001"],
            "input": "",
            "now": "2026-01-15T12:00:00Z",
            "expected_error_category": "input_error",
        },
        {
            "case_id": "CASE-B-002",
            "requirement_ids": ["FR-B-001"],
            "input": "",
            "now": "2026-01-15T12:00:00Z",
            "expected_error_category": "input_error",
        },
    ]
    results = iter(
        [
            (None, "service_error"),
            ({"error": {"category": "input_error", "code": "invalid_request"}}, None),
        ]
    )
    monkeypatch.setattr(evaluate, "load_dotenv", lambda **_kwargs: None)
    monkeypatch.setattr(evaluate, "_load_cases", lambda _path: cases)
    monkeypatch.setattr(evaluate, "_preflight", lambda: [{"passed": True}])
    monkeypatch.setattr(evaluate, "_invoke_app", lambda _case: next(results))
    monkeypatch.setenv("GEMINI_API_KEY", "not-a-real-test-key")

    report, exit_code = evaluate.run_evaluation(evaluate.DATASET_PATH, tmp_path)

    assert exit_code == 1
    assert report["summary"]["case_count"] == 2
    assert report["summary"]["passed_case_count"] == 1
    assert report["summary"]["evaluated_case_count"] == 1
    assert report["summary"]["unscored_case_count"] == 1
    assert report["summary"]["service_failures"] == 1
    assert report["summary"]["unclassified_failures"] == 0
