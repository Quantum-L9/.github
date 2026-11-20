#!/usr/bin/env python3
"""Offline validator for settings/ (GitHub settings as code).

Observational only: it reads settings/, the schema, the repository registry and
policies/repo-settings.yml, and never writes or repairs anything.

Checks, every one of them fatal:
  - settings/org.yml and every settings/repos/*.yml match settings/settings.schema.json;
  - a repository file is named exactly after its `repository`;
  - the repository is registered in semantics/repository_registry.yaml;
  - a repository is declared by exactly one file (never both .yml and .yaml);
  - environment and ruleset names are unique within a repository;
  - a section named in `observed.unreadable` stays UNKNOWN, except a field listed
    in `observed.decided` (a recorded decision, not an observation).

Reported, not fatal (fatal with --strict-policy): a merge setting that disagrees
with policies/repo-settings.yml (`CONFLICT`). Settings here are observed live
values, so the disagreement is shown, never reconciled.

Exit 0 when valid, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
UNKNOWN = "UNKNOWN"
POLICY_MERGE_KEYS = (
    "allow_merge_commit",
    "allow_squash_merge",
    "allow_rebase_merge",
    "allow_auto_merge",
    "delete_branch_on_merge",
)
# observed.unreadable entry -> the declaration section(s) it covers.
UNREADABLE_SECTIONS = {
    "actions/permissions": (
        "actions",
        (
            "access_level",
            "default_workflow_permissions",
            "can_approve_pull_request_reviews",
        ),
    ),
    "environments": ("environments", None),
}


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def registered_repositories(root: Path) -> set[str]:
    registry = _load_yaml(root / "semantics" / "repository_registry.yaml") or {}
    names: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            coordinate = node.get("coordinate")
            if isinstance(coordinate, dict) and isinstance(
                coordinate.get("repository"), str
            ):
                names.add(coordinate["repository"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(registry)
    return names


def policy_merge_settings(root: Path, repository: str) -> dict[str, Any]:
    path = root / "policies" / "repo-settings.yml"
    if not path.is_file():
        return {}
    policy = _load_yaml(path) or {}
    effective = {
        k: v
        for k, v in (policy.get("defaults") or {}).items()
        if k in POLICY_MERGE_KEYS
    }
    for override in policy.get("overrides") or []:
        if repository in (override.get("repos") or []):
            effective.update(
                {k: v for k, v in override.items() if k in POLICY_MERGE_KEYS}
            )
    return effective


def repository_files(settings: Path) -> list[Path]:
    directory = settings / "repos"
    if not directory.is_dir():
        return []
    # iterdir, not glob: `.github.yml` is a dotfile.
    return sorted(
        p for p in directory.iterdir() if p.is_file() and p.suffix in (".yml", ".yaml")
    )


def validate(root: Path, strict_policy: bool = False) -> tuple[list[str], list[str]]:
    """Return (errors, conflicts)."""
    settings = root / "settings"
    errors: list[str] = []
    conflicts: list[str] = []
    schema = json.loads((settings / "settings.schema.json").read_text(encoding="utf-8"))
    validators = {
        kind: Draft202012Validator(
            {"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"}
        )
        for kind in ("org", "repo")
    }

    def schema_errors(rel: str, doc: Any, kind: str) -> bool:
        """Validate against one declaration kind; report the most specific cause of each error."""
        found = sorted(
            validators[kind].iter_errors(doc), key=lambda e: list(e.absolute_path)
        )
        for error in found:
            cause = error
            # Inside a oneOf (value | UNKNOWN), the deepest branch error names the real defect.
            while cause.context:
                cause = max(cause.context, key=lambda e: len(e.absolute_path))
            where = "/".join(str(p) for p in cause.absolute_path) or "<root>"
            errors.append(f"{rel}: {where}: {cause.message[:300]}")
        return not found

    org_path = settings / "org.yml"
    if not org_path.is_file():
        errors.append("settings/org.yml: missing")
    else:
        org = _load_yaml(org_path)
        schema_errors("settings/org.yml", org, "org")

    files = repository_files(settings)
    if not files:
        errors.append("settings/repos: no repository declarations")
    registered = registered_repositories(root)
    seen: dict[str, str] = {}
    for path in files:
        rel = f"settings/repos/{path.name}"
        doc = _load_yaml(path)
        if not schema_errors(rel, doc, "repo"):
            continue
        repository = doc["repository"]
        if repository in seen:
            errors.append(
                f"{rel}: {repository} is already declared by settings/repos/{seen[repository]}"
            )
        seen[repository] = path.name
        if path.stem != repository:
            errors.append(f"{rel}: file must be named {repository}.yml")
        if repository not in registered:
            errors.append(
                f"{rel}: {repository} is not registered in semantics/repository_registry.yaml"
            )
        for section in ("environments", "rulesets"):
            items = doc[section]
            if isinstance(items, list):
                names = [item["name"] for item in items]
                duplicates = sorted({n for n in names if names.count(n) > 1})
                if duplicates:
                    errors.append(
                        f"{rel}: duplicate {section} name(s): {', '.join(duplicates)}"
                    )
        decided = set(doc["observed"].get("decided", []))
        for entry in doc["observed"].get("unreadable", []):
            if entry not in UNREADABLE_SECTIONS:
                errors.append(
                    f"{rel}: observed.unreadable names an unknown section {entry!r}"
                )
                continue
            section, keys = UNREADABLE_SECTIONS[entry]
            value = doc[section]
            if value == UNKNOWN:
                continue
            if keys is None:
                # A section that was unreadable may only carry what was observed some other way;
                # every field that would need the unreadable endpoint stays UNKNOWN.
                for item in value:
                    for key, field in item.items():
                        if key not in ("name", "required_secrets") and field != UNKNOWN:
                            errors.append(
                                f"{rel}: {section}[{item['name']}].{key} is declared but {entry} was unreadable"
                            )
            else:
                for key in keys:
                    if value.get(key) != UNKNOWN and f"{section}.{key}" not in decided:
                        errors.append(
                            f"{rel}: {section}.{key} is declared but {entry} was unreadable"
                        )
        merge = doc["merge"]
        if isinstance(merge, dict):
            for key, wanted in sorted(policy_merge_settings(root, repository).items()):
                declared = merge.get(key, UNKNOWN)
                if declared != UNKNOWN and declared != wanted:
                    conflicts.append(
                        f"{rel}: merge.{key}={json.dumps(declared)} but policies/repo-settings.yml says {json.dumps(wanted)}"
                    )
    if strict_policy:
        errors.extend(conflicts)
    return errors, conflicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--strict-policy",
        action="store_true",
        help="fail on a CONFLICT with policies/repo-settings.yml",
    )
    args = parser.parse_args(argv)
    errors, conflicts = validate(args.root.resolve(), strict_policy=args.strict_policy)
    for line in conflicts:
        print(f"CONFLICT {line}")
    for line in errors:
        print(f"ERROR {line}", file=sys.stderr)
    files = len(repository_files(args.root.resolve() / "settings"))
    print(
        f"settings: {files} repository declaration(s), {len(conflicts)} conflict(s), {len(errors)} error(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
