"""Generate a Postman v2.1.0 collection from the FastAPI OpenAPI spec.

Deterministic output (sorted request order, stable ids) so drift-checking
works the same way as `docs/api/openapi.json`.

Usage:
    python scripts/generate_postman.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
API_DIR = REPO_ROOT / "docs" / "api"

sys.path.insert(0, str(BACKEND_DIR))

try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env.example")
    load_dotenv(BACKEND_DIR / ".env", override=True)
except ImportError:
    pass


def _method_order(method: str) -> int:
    return {"GET": 0, "POST": 1, "PATCH": 2, "PUT": 3, "DELETE": 4}.get(
        method.upper(), 9
    )


def _folder_for(path: str, tag_by_path: dict[str, str]) -> str:
    if path in tag_by_path:
        return tag_by_path[path]
    parts = [p for p in path.split("/") if p and not p.startswith("{")]
    return parts[1] if len(parts) > 1 else (parts[0] if parts else "root")


def build(spec: dict) -> dict:
    info = spec.get("info", {})
    tag_by_path: dict[str, str] = {}
    items_by_folder: dict[str, list[dict]] = {}
    for path, methods in sorted(spec.get("paths", {}).items()):
        for method, op in sorted(methods.items(), key=lambda kv: _method_order(kv[0])):
            tags = op.get("tags") or []
            folder = tags[0] if tags else _folder_for(path, tag_by_path)
            tag_by_path[path] = folder
            request: dict = {
                "name": op.get("summary") or f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{access_token}}"},
                        {"key": "X-Request-Id", "value": "{{$guid}}"},
                    ],
                    "url": {
                        "raw": "{{base_url}}" + path,
                        "host": ["{{base_url}}"],
                        "path": [p for p in path.strip("/").split("/") if p],
                    },
                    "description": op.get("description") or "",
                },
                "response": [],
            }
            body = (
                op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if body is not None:
                request["request"]["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {"raw": {"language": "json"}},
                }
            items_by_folder.setdefault(folder, []).append(request)
    folders = [
        {"name": folder, "item": sorted(items, key=lambda r: r["name"])}
        for folder, items in sorted(items_by_folder.items())
    ]
    return {
        "info": {
            "name": info.get("title", "Kaya BOS API"),
            "description": info.get("description")
            or f"Version {info.get('version','')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8001", "type": "string"},
            {"key": "access_token", "value": "", "type": "string"},
        ],
        "item": folders,
    }


def main() -> int:
    from app.main import app  # imported here so env.load runs first

    spec = app.openapi()
    collection = build(spec)
    path = API_DIR / "postman_collection.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(collection, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(
        f"Wrote {path.relative_to(REPO_ROOT)} — {sum(len(f['item']) for f in collection['item'])} requests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
