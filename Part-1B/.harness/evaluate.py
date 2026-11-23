"""Preflight and evaluate the reminder app as a separate process per case."""

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from evaluator import aggregate_results, evaluate_case

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "dataset.json"
DEFAULT_MODEL = "gemini-3.8-flash"
_SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)
_CLASSIFIED_FAILURES = {
    "application_error",
    "application_timeout",
    "configuration_error",
    "invalid_application_output",
    "model_output_error",
    "service_error",
}


def _load_cases(path: Path) -> list[dict[str, Any]]:
    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load evaluation dataset: {error}") from error
    cases = dataset.get("cases") if isinstance(dataset, dict) else None
    if not isinstance(cases, list) or len(cases) < 15:
        raise ValueError("evaluation dataset must contain at least 15 cases")
    identifiers = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(set(identifiers)) != len(identifiers):
        raise ValueError("evaluation case IDs must be present and unique")
    for case in cases:
        if not case.get("requirement_ids"):
            raise ValueError(f"{case['case_id']} has no requirement traceability")
    return cases


def _preflight() -> list[dict[str, Any]]:
    commands = [
        (
            "ruff",
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--no-cache",
                "src",
                "tests",
                ".harness",
                "evals",
            ],
        ),
        ("bandit", [sys.executable, "-m", "bandit", "-q", "-r", "src"]),
    ]
    results: list[dict[str, Any]] = []
    for name, command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "name": name,
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    if all(result["passed"] for result in results):
        dynamic_commands = [
            (
                "pytest",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "-q",
                    "tests",
                ],
            ),
            ("harness-self-check", [sys.executable, ".harness/self_check.py"]),
        ]
        for name, command in dynamic_commands:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            results.append(
                {
                    "name": name,
                    "passed": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
    else:
        for name in ("pytest", "harness-self-check"):
            results.append(
                {
                    "name": name,
                    "passed": False,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "Skipped because a static gate failed.",
                    "status": "skipped",
                }
            )
    return results


def _invoke_app(case: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    environment["PYTHONPATH"] = (
        source_path
        if not environment.get("PYTHONPATH")
        else source_path + os.pathsep + environment["PYTHONPATH"]
    )
    request = json.dumps(
        {"request": case["input"], "now": case["now"]},
        ensure_ascii=False,
    )
    try:
        result = subprocess.run(
            [sys.executable, "-m", "reminder"],
            cwd=ROOT,
            input=request,
            capture_output=True,
            text=True,
            timeout=50,
            check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return None, "application_timeout"
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, "invalid_application_output"
    if not isinstance(response, dict):
        return None, "invalid_application_output"
    if result.returncode == 0:
        return response, None
    error = response.get("error")
    if isinstance(error, dict) and error.get("category") == "service_error":
        return response, "service_error"
    if isinstance(error, dict) and error.get("category") == "configuration_error":
        return response, "configuration_error"
    if isinstance(error, dict) and error.get("category") == "input_error":
        return response, None
    if isinstance(error, dict) and error.get("category") == "model_output_error":
        return response, "model_output_error"
    return response, "application_error"


def _report_path(output_dir: Path, run_id: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / run_id
    target.mkdir(parents=True, exist_ok=False)
    return target / "eval-results.json"


def _redact_output(value: Any) -> tuple[Any, bool]:
    if isinstance(value, str):
        redacted = value
        for pattern in _SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted, redacted != value
    if isinstance(value, list):
        results = [_redact_output(item) for item in value]
        return [item for item, _ in results], any(changed for _, changed in results)
    if isinstance(value, dict):
        results = {key: _redact_output(item) for key, item in value.items()}
        return (
            {key: item for key, (item, _) in results.items()},
            any(changed for _, changed in results.values()),
        )
    return value, False


def run_evaluation(dataset_path: Path, output_dir: Path) -> tuple[dict[str, Any], int]:
    load_dotenv(dotenv_path=ROOT / ".env", override=False)
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    cases = _load_cases(dataset_path)
    preflight = _preflight()
    report: dict[str, Any] = {
        "run_id": run_id,
        "checked_at": datetime.now(UTC).isoformat(),
        "target": "Part-1B",
        "provider": "Gemini Developer API",
        "model": os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL,
        "temperature": 0,
        "stored_by_provider": False,
        "automatic_continuation": False,
        "sdk_retry_attempts": 1,
        "max_tokens": 512,
        "timeout_seconds": 45,
        "max_provider_calls_per_valid_case": 1,
        "threshold": {
            "semantic": 0.80,
            "all_structural_and_properties_pass": True,
            "all_guardrails_score_1": True,
        },
        "preflight": preflight,
        "results": [],
    }
    if not all(result["passed"] for result in preflight):
        report["status"] = "blocked_preflight"
        report["summary"] = {
            "passed": False,
            "model_calls": 0,
            "message": "Evaluation stopped before model calls because a preflight gate failed.",
        }
        report_path = _report_path(output_dir, run_id)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report, 1
    if not os.environ.get("GEMINI_API_KEY"):
        report["status"] = "blocked_configuration"
        report["summary"] = {
            "passed": False,
            "model_calls": 0,
            "message": "Set GEMINI_API_KEY locally before evaluation.",
        }
        report_path = _report_path(output_dir, run_id)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report, 2

    service_failures = 0
    for case in cases:
        response, failure_class = _invoke_app(case)
        if failure_class is not None:
            service_failures += failure_class == "service_error"
            safe_response, was_redacted = _redact_output(response)
            report["results"].append({
                "case_id": case["case_id"],
                "requirement_ids": case["requirement_ids"],
                "failure_class": failure_class,
                "passed": False,
                "provider_calls": 1,
                "output": safe_response,
                "output_redacted": was_redacted,
            })
            continue
        evaluated = evaluate_case(case, response)
        evaluated["provider_calls"] = 0 if case.get("expected_error_category") else 1
        evaluated["output"], evaluated["output_redacted"] = _redact_output(response)
        report["results"].append(evaluated)

    evaluated_cases = [
        result
        for result in report["results"]
        if "structural" in result and "properties" in result
    ]
    aggregate = aggregate_results(evaluated_cases)
    aggregate["model_calls"] = len(cases) - sum(
        1 for result in report["results"] if result.get("provider_calls") == 0
    )
    aggregate["service_failures"] = service_failures
    aggregate["case_count"] = len(cases)
    aggregate["passed_case_count"] = sum(
        result.get("passed") is True for result in report["results"]
    )
    aggregate["evaluated_case_count"] = len(evaluated_cases)
    aggregate["unscored_case_count"] = len(cases) - len(evaluated_cases)
    aggregate["application_timeouts"] = sum(
        result.get("failure_class") == "application_timeout"
        for result in report["results"]
    )
    aggregate["unclassified_failures"] = sum(
        result.get("failure_class") not in _CLASSIFIED_FAILURES
        for result in report["results"]
        if "structural" not in result
    )
    aggregate["passed"] = (
        aggregate["passed"]
        and not service_failures
        and len(evaluated_cases) == len(cases)
    )
    report["summary"] = aggregate
    report["status"] = "passed" if aggregate["passed"] else "failed"
    report_path = _report_path(output_dir, run_id)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report, 0 if aggregate["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "evidence" / "eval-results",
    )
    arguments = parser.parse_args()
    try:
        report, exit_code = run_evaluation(arguments.dataset, arguments.output_dir)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
