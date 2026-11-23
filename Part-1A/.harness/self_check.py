"""Verify that each Part 1A sensor rejects a deliberately broken fixture."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _gate_result(
    name: str,
    good: subprocess.CompletedProcess[str],
    bad: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "good_passed": good.returncode == 0,
        "broken_rejected": bad.returncode != 0,
        "good_exit_code": good.returncode,
        "broken_exit_code": bad.returncode,
    }


def run_self_check() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="todo-harness-check-") as directory:
        fixture = Path(directory)
        good_source = fixture / "good.py"
        bad_source = fixture / "bad.py"
        good_source.write_text("value = 1\n", encoding="utf-8")
        bad_source.write_text("value = 1\nif value == None:\n    pass\n", encoding="utf-8")

        ruff_good = _run(
            [sys.executable, "-m", "ruff", "check", "--no-cache", str(good_source)],
            ROOT,
        )
        ruff_bad = _run(
            [sys.executable, "-m", "ruff", "check", "--no-cache", str(bad_source)],
            ROOT,
        )

        good_security = fixture / "safe"
        bad_security = fixture / "unsafe"
        good_security.mkdir()
        bad_security.mkdir()
        (good_security / "sample.py").write_text("value = 1\n", encoding="utf-8")
        (bad_security / "sample.py").write_text(
            "import subprocess\nsubprocess.call('echo check', shell=True)\n",
            encoding="utf-8",
        )
        bandit_good = _run(
            [sys.executable, "-m", "bandit", "-q", "-r", str(good_security)],
            ROOT,
        )
        bandit_bad = _run(
            [sys.executable, "-m", "bandit", "-q", "-r", str(bad_security)],
            ROOT,
        )

        good_tests = fixture / "good_test.py"
        bad_tests = fixture / "bad_test.py"
        good_tests.write_text("def test_value():\n    assert 1 == 1\n", encoding="utf-8")
        bad_tests.write_text("def test_value():\n    assert 1 == 2\n", encoding="utf-8")
        pytest_good = _run(
            [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", str(good_tests)],
            ROOT,
        )
        pytest_bad = _run(
            [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", str(bad_tests)],
            ROOT,
        )

    gates = [
        _gate_result("ruff", ruff_good, ruff_bad),
        _gate_result("bandit", bandit_good, bandit_bad),
        _gate_result("pytest", pytest_good, pytest_bad),
    ]
    passed = all(
        gate["good_passed"] and gate["broken_rejected"]
        for gate in gates
    )
    return {"passed": passed, "gates": gates}


def main() -> int:
    report = run_self_check()
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
