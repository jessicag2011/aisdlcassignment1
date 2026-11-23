"""Entry point for the single, preflighted evaluation pipeline."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
environment = os.environ.copy()
source_path = str(ROOT / "src")
environment["PYTHONPATH"] = (
    source_path
    if not environment.get("PYTHONPATH")
    else source_path + os.pathsep + environment["PYTHONPATH"]
)

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, str(ROOT / ".harness" / "evaluate.py"), *sys.argv[1:]],
        cwd=ROOT,
        check=False,
        env=environment,
    )
    raise SystemExit(result.returncode)
