"""OpenAPI drift detection.

Compares the freshly-generated spec against the committed baseline under
`docs/api/`. Exits non-zero when they differ so CI can fail the PR.

Usage:
    python scripts/check_openapi_drift.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "docs" / "api"
FILES = ("openapi.json", "openapi.yaml")


def _snapshot() -> dict[str, str]:
    return {f: (API_DIR / f).read_text() if (API_DIR / f).exists() else "" for f in FILES}


def main() -> int:
    before = _snapshot()
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "generate_openapi.py")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    after = _snapshot()
    drifted = [f for f in FILES if before[f] != after[f]]
    if drifted:
        sys.stderr.write("\nOpenAPI drift detected in: " + ", ".join(drifted) + "\n")
        sys.stderr.write(
            "The committed spec in docs/api/ does not match the code. "
            "Re-run `python scripts/generate_openapi.py` locally and commit the result.\n"
        )
        # Show first diff for context.
        for f in drifted:
            path = API_DIR / f
            diff = subprocess.run(
                ["git", "--no-pager", "diff", "--no-color", str(path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if diff.stdout:
                sys.stderr.write(f"\n--- diff {f} ---\n{diff.stdout}\n")
        return 1

    print("OpenAPI spec matches baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
