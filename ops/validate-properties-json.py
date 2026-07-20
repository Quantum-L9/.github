#!/usr/bin/env python3
"""Validate every workflow-templates/*.properties.json against
ops/schemas/workflow-template-properties.schema.json.

See that schema file's $comment for why `categories` is intentionally
type:string with no enum (GitHub's real category vocabulary is an open
union of 11 fixed buckets + linguist languages + tech stacks; there is no
single closed list to validate against, and the community SchemaStore
schema for this exact file type gets this wrong by encoding only the
linguist-language list).
"""
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("jsonschema package not available; install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "ops" / "schemas" / "workflow-template-properties.schema.json"


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    files = sorted((REPO_ROOT / "workflow-templates").glob("*.properties.json"))
    if not files:
        print("No workflow-templates/*.properties.json files found.", file=sys.stderr)
        return 1

    failed = 0
    for path in files:
        rel = path.relative_to(REPO_ROOT)
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"FAIL {rel}: invalid JSON: {exc}")
            failed += 1
            continue
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            print(f"FAIL {rel}: {exc.message} (at {'/'.join(str(p) for p in exc.absolute_path) or '<root>'})")
            failed += 1
            continue
        print(f"OK   {rel}")

    print("---")
    print(f"Checked {len(files)} properties.json file(s).")
    if failed:
        print(f"{failed} file(s) failed schema validation.")
        return 1
    print("All files valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
