"""Contract drift check — regenerates OpenAPI JSON/YAML and Postman collection
and fails if any committed baseline changed. Used by CI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "docs" / "api"
FILES = ("openapi.json", "openapi.yaml", "postman_collection.json")


def _snapshot() -> dict[str, str]:
    return {
        f: (API_DIR / f).read_text() if (API_DIR / f).exists() else "" for f in FILES
    }


def _run(*args: str) -> None:
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(r.returncode)


def main() -> int:
    before = _snapshot()
    _run(str(REPO_ROOT / "scripts" / "generate_openapi.py"))
    _run(str(REPO_ROOT / "scripts" / "generate_postman.py"))
    after = _snapshot()

    drifted = [f for f in FILES if before[f] != after[f]]
    if drifted:
        sys.stderr.write(
            "\nAPI contract drift detected in: " + ", ".join(drifted) + "\n"
        )
        sys.stderr.write(
            "Re-run `python scripts/generate_openapi.py && python scripts/generate_postman.py` "
            "locally and commit the resulting files.\n"
        )
        for f in drifted:
            diff = subprocess.run(
                ["git", "--no-pager", "diff", "--no-color", str(API_DIR / f)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if diff.stdout:
                sys.stderr.write(f"\n--- diff {f} ---\n{diff.stdout}\n")
        return 1
    print(
        "API contracts match baseline (openapi.json, openapi.yaml, postman_collection.json)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
