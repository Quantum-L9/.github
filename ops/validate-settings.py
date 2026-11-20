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


class DuplicateKeyError(yaml.constructor.ConstructorError):
    """A mapping repeats a key; PyYAML would otherwise keep the last one silently."""


class _StrictLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> Any:
        seen: dict[Any, yaml.Mark] = {}
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise DuplicateKeyError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r} (first at line {seen[key].line + 1})",
                    key_node.start_mark,
                )
            seen[key] = key_node.start_mark
        return super().construct_mapping(node, deep=deep)


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_StrictLoader)


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


_UNPARSED = object()


def _yaml_error(rel: str, exc: yaml.YAMLError) -> str:
    return f"{rel}: invalid YAML: {' '.join(str(exc).split())[:300]}"


def _parsed(rel: str, path: Path, errors: list[str]) -> Any:
    """Load one declaration, reporting a YAML error (duplicate keys included) as fatal."""
    try:
        return _load_yaml(path)
    except yaml.YAMLError as exc:
        errors.append(_yaml_error(rel, exc))
        return _UNPARSED


def _schema_validators(settings: Path) -> dict[str, Draft202012Validator]:
    schema = json.loads((settings / "settings.schema.json").read_text(encoding="utf-8"))
    return {
        kind: Draft202012Validator(
            {"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"}
        )
        for kind in ("org", "repo")
    }


def _schema_errors(
    validator: Draft202012Validator, rel: str, doc: Any, errors: list[str]
) -> bool:
    """Validate one document; report the most specific cause of each error."""
    found = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    for error in found:
        cause = error
        # Inside a oneOf (value | UNKNOWN), the deepest branch error names the real defect.
        while cause.context:
            cause = max(cause.context, key=lambda e: len(e.absolute_path))
        where = "/".join(str(p) for p in cause.absolute_path) or "<root>"
        errors.append(f"{rel}: {where}: {cause.message[:300]}")
    return not found


def _check_identity(
    rel: str,
    path: Path,
    repository: str,
    seen: dict[str, str],
    registered: set[str] | None,
    errors: list[str],
) -> None:
    if repository in seen:
        errors.append(
            f"{rel}: {repository} is already declared by settings/repos/{seen[repository]}"
        )
    seen[repository] = path.name
    if path.name != f"{repository}.yml":
        errors.append(f"{rel}: file must be named {repository}.yml")
    if registered is not None and repository not in registered:
        errors.append(
            f"{rel}: {repository} is not registered in semantics/repository_registry.yaml"
        )


def _check_unique_names(rel: str, doc: dict[str, Any], errors: list[str]) -> None:
    for section in ("environments", "rulesets"):
        items = doc[section]
        if not isinstance(items, list):
            continue
        names = [item["name"] for item in items]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            errors.append(
                f"{rel}: duplicate {section} name(s): {', '.join(duplicates)}"
            )


def _check_unreadable_list(
    rel: str,
    section: str,
    entry: str,
    value: list[dict[str, Any]],
    decided: set[str],
    errors: list[str],
) -> None:
    # A section that was unreadable may only carry what was observed some other way;
    # every field that would need the unreadable endpoint stays UNKNOWN.
    for item in value:
        for key, field in item.items():
            if key in ("name", "required_secrets") or field == UNKNOWN:
                continue
            if f"{section}.{key}" not in decided:
                errors.append(
                    f"{rel}: {section}[{item['name']}].{key} is declared but {entry} was unreadable"
                )


def _check_unreadable(rel: str, doc: dict[str, Any], errors: list[str]) -> None:
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
            _check_unreadable_list(rel, section, entry, value, decided, errors)
            continue
        for key in keys:
            if value.get(key) != UNKNOWN and f"{section}.{key}" not in decided:
                errors.append(
                    f"{rel}: {section}.{key} is declared but {entry} was unreadable"
                )


def _merge_conflicts(
    root: Path, rel: str, repository: str, merge: Any, conflicts: list[str]
) -> None:
    if not isinstance(merge, dict):
        return
    for key, wanted in sorted(policy_merge_settings(root, repository).items()):
        declared = merge.get(key, UNKNOWN)
        if declared != UNKNOWN and declared != wanted:
            conflicts.append(
                f"{rel}: merge.{key}={json.dumps(declared)} but policies/repo-settings.yml says {json.dumps(wanted)}"
            )


def validate(root: Path, strict_policy: bool = False) -> tuple[list[str], list[str]]:
    """Return (errors, conflicts)."""
    settings = root / "settings"
    errors: list[str] = []
    conflicts: list[str] = []
    validators = _schema_validators(settings)

    org_path = settings / "org.yml"
    if not org_path.is_file():
        errors.append("settings/org.yml: missing")
    else:
        org = _parsed("settings/org.yml", org_path, errors)
        if org is not _UNPARSED:
            _schema_errors(validators["org"], "settings/org.yml", org, errors)

    files = repository_files(settings)
    if not files:
        errors.append("settings/repos: no repository declarations")
    # An unreadable registry or policy file is one fatal error, not a traceback;
    # the checks that need it are skipped rather than reported once per file.
    registered: set[str] | None
    try:
        registered = registered_repositories(root)
    except yaml.YAMLError as exc:
        errors.append(_yaml_error("semantics/repository_registry.yaml", exc))
        registered = None
    policy_readable = True
    try:
        policy_merge_settings(root, "")
    except yaml.YAMLError as exc:
        errors.append(_yaml_error("policies/repo-settings.yml", exc))
        policy_readable = False
    seen: dict[str, str] = {}
    for path in files:
        rel = f"settings/repos/{path.name}"
        doc = _parsed(rel, path, errors)
        if doc is _UNPARSED or not _schema_errors(validators["repo"], rel, doc, errors):
            continue
        repository = doc["repository"]
        _check_identity(rel, path, repository, seen, registered, errors)
        _check_unique_names(rel, doc, errors)
        _check_unreadable(rel, doc, errors)
        if policy_readable:
            _merge_conflicts(root, rel, repository, doc["merge"], conflicts)
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
