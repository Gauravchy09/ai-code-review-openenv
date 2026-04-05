from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: List[str], env: dict | None = None) -> Tuple[int, str, str]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _check_files_exist() -> list[str]:
    required = [
        ROOT / "openenv.yaml",
        ROOT / "Dockerfile",
        ROOT / "inference.py",
        ROOT / "app.py",
        ROOT / "env" / "environment.py",
        ROOT / "env" / "grader.py",
        ROOT / "env" / "tasks.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    return missing


def main() -> None:
    failures: list[str] = []

    missing_files = _check_files_exist()
    if missing_files:
        failures.append(f"Missing required files: {', '.join(missing_files)}")

    rc, _, stderr = _run([sys.executable, "-m", "compileall", "."])
    if rc != 0:
        failures.append(f"compileall failed: {stderr.strip()}")

    rc, stdout, stderr = _run([sys.executable, "scripts/pre_validate.py"])
    if rc != 0:
        failures.append(f"pre_validate failed: {(stdout + stderr).strip()}")

    env = os.environ.copy()
    env["MOCK_INFERENCE"] = "1"
    rc, stdout, stderr = _run([sys.executable, "inference.py"], env=env)
    if rc != 0:
        failures.append(f"mock inference failed: {(stdout + stderr).strip()}")
    else:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if len(lines) < 5:
            failures.append("mock inference output too short; expected [START], 3x[STEP], [END]")
        else:
            if not lines[0].startswith("[START] "):
                failures.append("first inference line must start with [START]")
            if not all(lines[i].startswith("[STEP] ") for i in [1, 2, 3]):
                failures.append("middle inference lines must start with [STEP]")
            if not lines[4].startswith("[END] "):
                failures.append("last inference line must start with [END]")

            end_payload = lines[4].split(" ", 1)[1] if " " in lines[4] else "{}"
            try:
                end_obj = json.loads(end_payload)
                avg = float(end_obj.get("average_score", -1))
                if not (0.0 <= avg <= 1.0):
                    failures.append("[END] average_score must be in [0.0, 1.0]")
            except Exception as exc:
                failures.append(f"failed to parse [END] payload: {exc}")

    if failures:
        print("pre_submit: FAIL")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("pre_submit: PASS")


if __name__ == "__main__":
    main()
