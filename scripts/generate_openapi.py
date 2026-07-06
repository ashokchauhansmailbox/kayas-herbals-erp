"""Generate OpenAPI snapshot files.

Produces two artifacts:
    docs/api/openapi.json  — canonical JSON (used by CI drift detection)
    docs/api/openapi.yaml  — human-readable mirror

Both files are re-generated deterministically:
    * sorted keys
    * 2-space indent
    * trailing newline

CI diff-checks these files against the committed baseline. Any route change
that is not reflected in the baseline fails the "openapi-contract" job and
must be re-committed with the code change that triggered it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
API_DIR = REPO_ROOT / "docs" / "api"

sys.path.insert(0, str(BACKEND_DIR))

# Load .env so app.core.config can be imported without live env vars.
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env.example")
    load_dotenv(BACKEND_DIR / ".env", override=True)
except ImportError:
    pass

try:
    import yaml  # type: ignore
except ImportError:  # PyYAML is a dev dep — CI installs it.
    yaml = None


def _load_spec() -> dict:
    from app.main import app

    return app.openapi()


def _write_json(spec: dict) -> Path:
    path = API_DIR / "openapi.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def _write_yaml(spec: dict) -> Path:
    path = API_DIR / "openapi.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:
        # Deterministic fallback: serialise JSON as-is with a warning header.
        with path.open("w", encoding="utf-8") as fh:
            fh.write("# PyYAML unavailable — YAML mirrors JSON verbatim.\n")
            json.dump(spec, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return path
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(spec, fh, sort_keys=True, default_flow_style=False, allow_unicode=True)
    return path


def main() -> int:
    spec = _load_spec()
    json_path = _write_json(spec)
    yaml_path = _write_yaml(spec)
    print(f"Wrote {json_path.relative_to(REPO_ROOT)}")
    print(f"Wrote {yaml_path.relative_to(REPO_ROOT)}")
    print(f"Routes: {len(spec.get('paths', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
