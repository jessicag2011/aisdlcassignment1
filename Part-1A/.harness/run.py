"""Run Part 1A quality gates and save an immutable per-run report."""

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_gate(name: str, command: list[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _skipped_gate(name: str) -> dict[str, object]:
    return {
        "name": name,
        "passed": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "Skipped because a static gate failed.",
        "status": "skipped",
    }


def main() -> int:
    gates = [
        _run_gate(
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
            ],
        ),
        _run_gate(
            "bandit",
            [sys.executable, "-m", "bandit", "-q", "-r", "src"],
        ),
    ]
    if all(gate["passed"] for gate in gates):
        gates.extend(
            [
                _run_gate(
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
                _run_gate(
                    "harness-self-check",
                    [sys.executable, ".harness/self_check.py"],
                ),
            ]
        )
    else:
        gates.extend([_skipped_gate("pytest"), _skipped_gate("harness-self-check")])
    passed = all(gate["passed"] for gate in gates)
    timestamp = datetime.now(UTC).isoformat()
    report = {
        "run_id": f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
        "checked_at": timestamp,
        "target": "Part-1A",
        "passed": passed,
        "gates": gates,
    }
    output_dir = ROOT / "evidence" / "harness-results" / report["run_id"]
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    print(f"Report: {output_dir.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
