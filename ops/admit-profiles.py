#!/usr/bin/env python3
"""Turn one node birth's compiled profile admission candidates into one reviewable admission candidate.

A born node's conformance runs only against profiles this repository admits
(`semantics/projection_profiles.yaml#source_classes.conformance_profiles.admitted_profiles`).
The candidates come from the pinned semantic compiler's `birth-closure`
(`birth-requirements.json`, schema `l9.semantic-compiler.birth-requirements/v1`,
ADR-0007 there): one per conformance class the product requires, scoped by its
product kind and archetype. The profile bodies are owned by l9-conformance and
read from its catalog at an exact revision; nothing here authors or edits one.

    admit-profiles.py check --requirements FILE --catalog DIR --catalog-revision SHA
    admit-profiles.py apply --requirements FILE --catalog DIR --catalog-revision SHA \
                            --checkout DIR [--changes-out FILE]

`check` runs the l9-projection-admission subject closure for these subjects and
prints a JSON report. A candidate is ADMISSIBLE only when every check holds:

    identity        the product declares a profile id for the class
    catalog         the id is in the catalog INDEX, with a path
    digest          the INDEX digest is sha256 of the profile file bytes
    shape           the file's id, conformance_class and scope are the candidate's
    membership      the profile names at least one member fixture
    specified       the profile records no `unresolved` entry (underspecified otherwise:
                    each Unknown is reported with its kind and what resolves it)
    immutable       an id already admitted is admitted at this exact digest
                    (a changed body needs a new @N+1 profile, PROJECTION-013)

Exit 0: every candidate admissible. Exit 1: at least one gap (all of them are
reported). Exit 2: an input is unreadable or malformed (UNRESOLVED, never a pass).

`apply` refuses unless `check` passes. It then adds the admissible coordinates to
the ledger, cuts the successor release record SC-008 requires, and runs the
semantic validator. Any failure restores the tree. The record is an
ADDITIVE SUCCESSOR CANDIDATE: this tool decides nothing. Admission is the owner's
decision on that exact subject (l9-projection-admission AUTHORIZE/ADMIT), and the
merge of the pull request carries it. Re-running with nothing new is `present`.

Dependencies: Python 3.11+, PyYAML.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

LEDGER_PATH = "semantics/projection_profiles.yaml"
RELEASES_PATH = "docs/semantic-foundation"
VALIDATOR_PATH = "scripts/validate-semantics.py"
CATALOG_INDEX = "catalog/INDEX.yaml"
CATALOG_REPOSITORY = "Quantum-L9/l9-conformance"
REQUIREMENTS_SCHEMA = "l9.semantic-compiler.birth-requirements/v1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_DIR_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
STATUS = "ADDITIVE SUCCESSOR CANDIDATE"


class AdmissionInputError(RuntimeError):
    """An input cannot be read or interpreted: UNRESOLVED (exit 2)."""


class AdmissionRefused(RuntimeError):
    """Admission cannot proceed (exit 1)."""


def _allowed_roots() -> list[str]:
    roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve()]
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        roots.append(Path(runner_temp).resolve())
    return [str(r) for r in roots]


def _input_path(raw: Path, label: str, *, directory: bool = False) -> Path:
    """A CLI-supplied path, resolved and confined to the working or temp directory."""
    resolved = os.path.realpath(raw)
    if not any(
        os.path.commonpath([root, resolved]) == root for root in _allowed_roots()
    ):
        raise AdmissionInputError(
            f"{label} must be inside the working directory or the runner temp directory"
        )
    target = Path(resolved)
    if not (target.is_dir() if directory else target.is_file()):
        raise AdmissionInputError(
            f"{label} is not an existing {'directory' if directory else 'file'}"
        )
    return target


def _confined(root: Path, relative: str, label: str) -> Path:
    """root/relative, refused when it resolves outside root."""
    base = os.path.realpath(root)
    target = os.path.realpath(os.path.join(base, relative))
    if os.path.commonpath([base, target]) != base:
        raise AdmissionInputError(f"{label} {relative} escapes {base}")
    return Path(target)


def _load_yaml(path: Path, label: str) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise AdmissionInputError(f"{label} unreadable: {exc}") from exc


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_candidates(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """(product_ref, candidates) from the compiler's birth requirements."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionInputError(f"birth requirements unreadable: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != REQUIREMENTS_SCHEMA:
        raise AdmissionInputError(f"birth requirements are not {REQUIREMENTS_SCHEMA}")
    conformance = doc.get("conformance")
    candidates = (
        conformance.get("admission_candidates")
        if isinstance(conformance, dict)
        else None
    )
    if not isinstance(candidates, list) or not all(
        isinstance(c, dict) for c in candidates
    ):
        raise AdmissionInputError(
            "birth requirements carry no admission_candidates list"
        )
    if not candidates:
        raise AdmissionInputError(
            "birth requirements name no conformance class to admit"
        )
    return str(doc.get("product_ref")), candidates


def ledger_entries(checkout: Path) -> list[dict[str, Any]]:
    doc = _load_yaml(checkout / LEDGER_PATH, LEDGER_PATH)
    try:
        entries = doc["source_classes"]["conformance_profiles"]["admitted_profiles"]
    except (KeyError, TypeError) as exc:
        raise AdmissionInputError(
            f"{LEDGER_PATH} has no source_classes.conformance_profiles.admitted_profiles"
        ) from exc
    if not isinstance(entries, list):
        raise AdmissionInputError(f"{LEDGER_PATH} admitted_profiles is not a list")
    return entries


def _gap(
    candidate: dict[str, Any], code: str, detail: str, **extra: Any
) -> dict[str, Any]:
    return {
        "conformance_class": candidate.get("conformance_class"),
        "profile_ref": candidate.get("profile_ref"),
        "code": code,
        "detail": detail,
        **extra,
    }


def _catalog_listing(catalog: Path) -> dict[Any, dict[str, Any]]:
    index = _load_yaml(catalog / CATALOG_INDEX, f"l9-conformance {CATALOG_INDEX}")
    return {
        e.get("id"): e
        for e in (index or {}).get("profiles") or []
        if isinstance(e, dict)
    }


def _underspecified_gaps(
    candidate: dict[str, Any], profile: dict[str, Any]
) -> list[dict[str, Any]]:
    gaps = []
    if not profile.get("membership"):
        gaps.append(
            _gap(
                candidate,
                "membership_empty",
                f"{candidate.get('profile_ref')} names no member fixture",
            )
        )
    for unknown in (u for u in profile.get("unresolved") or [] if isinstance(u, dict)):
        statement = " ".join(str(unknown.get("statement", "")).split())
        gaps.append(
            _gap(
                candidate,
                "underspecified",
                f"{unknown.get('id')} ({unknown.get('kind')}): {statement}",
                unknown_id=unknown.get("id"),
                unknown_kind=unknown.get("kind"),
                resolution_requires=" ".join(
                    str(unknown.get("resolution_requires", "")).split()
                )
                or None,
            )
        )
    return gaps


def _evaluate_candidate(
    candidate: dict[str, Any], catalog: Path, listed: dict[Any, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """(gaps, coordinate). The coordinate is set only when there are no gaps."""
    cls, ref, scope = (
        candidate.get("conformance_class"),
        candidate.get("profile_ref"),
        candidate.get("scope"),
    )
    if not isinstance(ref, str) or not ref:
        return [
            _gap(
                candidate,
                "identity_undeclared",
                f"the product declares no profile for class {cls}",
            )
        ], None
    entry = listed.get(ref)
    if entry is None or not isinstance(entry.get("path"), str):
        return [
            _gap(
                candidate,
                "not_in_catalog",
                f"{ref} is not in {CATALOG_REPOSITORY} {CATALOG_INDEX}",
            )
        ], None
    path = _confined(catalog, entry["path"], "catalog profile")
    try:
        observed = _sha256(path)
    except OSError as exc:
        raise AdmissionInputError(
            f"catalog profile {entry['path']} unreadable: {exc}"
        ) from exc
    if observed != entry.get("digest"):
        return [
            _gap(
                candidate,
                "digest_mismatch",
                f"{entry['path']} is {observed}, INDEX says {entry.get('digest')}",
            )
        ], None
    profile = _load_yaml(path, f"catalog profile {entry['path']}")
    if not isinstance(profile, dict):
        raise AdmissionInputError(f"catalog profile {entry['path']} is not a mapping")
    if profile.get("id") != ref or profile.get("conformance_class") != cls:
        detail = f"{entry['path']} declares {profile.get('id')} / class {profile.get('conformance_class')}"
        return [_gap(candidate, "shape_mismatch", detail)], None
    if profile.get("scope") != scope:
        detail = (
            f"{entry['path']} scope {profile.get('scope')} is not the product's {scope}"
        )
        return [_gap(candidate, "scope_mismatch", detail)], None
    gaps = _underspecified_gaps(candidate, profile)
    if gaps:
        return gaps, None
    return [], {
        "id": ref,
        "conformance_class": cls,
        "distribution_repository": CATALOG_REPOSITORY,
        "distribution_path": entry["path"],
        "digest": observed,
    }


def check(
    *, candidates: list[dict[str, Any]], catalog: Path, admitted: list[dict[str, Any]]
) -> dict[str, Any]:
    """Every gap of every candidate, and the coordinates of the admissible ones."""
    listed = _catalog_listing(catalog)
    by_id = {e.get("id"): e for e in admitted if isinstance(e, dict)}
    gaps: list[dict[str, Any]] = []
    admissible: list[dict[str, Any]] = []
    present: list[str] = []
    for candidate in candidates:
        found, coordinate = _evaluate_candidate(candidate, catalog, listed)
        gaps.extend(found)
        if coordinate is None:
            continue
        prior = by_id.get(coordinate["id"])
        if prior is None:
            admissible.append(coordinate)
        elif prior.get("digest") != coordinate["digest"]:
            gaps.append(
                _gap(
                    candidate,
                    "admitted_profile_changed",
                    f"{coordinate['id']} is admitted at {prior.get('digest')}; a changed body needs a new profile version",
                )
            )
        else:
            present.append(coordinate["id"])
    return {
        "status": "admissible" if not gaps else "refused",
        "gaps": gaps,
        "admissible": admissible,
        "present": present,
    }


def _entry_yaml(entry: dict[str, Any]) -> str:
    keys = (
        "id",
        "conformance_class",
        "distribution_repository",
        "distribution_path",
        "digest",
    )
    lines = [f"      - id: {entry['id']}"] + [
        f"        {k}: {entry[k]}" for k in keys[1:]
    ]
    return "\n".join(lines) + "\n"


def add_entries(text: str, entries: list[dict[str, Any]]) -> str:
    """Append ledger entries at the end of the admitted_profiles list, formatting preserved."""
    lines = text.splitlines(keepends=True)
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == "admitted_profiles:"),
        None,
    )
    if start is None:
        raise AdmissionInputError(f"{LEDGER_PATH} has no admitted_profiles block")
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = start + 1
    while end < len(lines) and (
        not lines[end].strip() or len(lines[end]) - len(lines[end].lstrip()) > indent
    ):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    insert = "".join(_entry_yaml(e) for e in entries)
    return "".join(lines[:end]) + insert + "".join(lines[end:])


def _versions(root: Path) -> list[tuple[int, int, int]]:
    found = []
    for path in (root / RELEASES_PATH).iterdir():
        match = VERSION_DIR_RE.match(path.name)
        if match and path.is_dir():
            found.append(tuple(int(g) for g in match.groups()))
    return sorted(found)  # type: ignore[arg-type]


def cut_release(
    root: Path, product_ref: str, entries: list[dict[str, Any]], catalog_revision: str
) -> tuple[str, list[str]]:
    """The successor release record for exactly these ledger entries (SC-008, L9-REVISION-001)."""
    versions = _versions(root)
    if not versions:
        raise AdmissionInputError(f"no release record under {RELEASES_PATH}")
    major, minor, patch = versions[-1]
    predecessor, version = f"v{major}.{minor}.{patch}", f"v{major}.{minor}.{patch + 1}"
    target = root / RELEASES_PATH / version
    if target.exists():
        raise AdmissionRefused(f"{RELEASES_PATH}/{version} already exists")
    sources = sorted(f"semantics/{p.name}" for p in (root / "semantics").glob("*.yaml"))
    adrs = sorted((root / "docs" / "adr").glob("ADR-*.md"))
    subjects = [
        f"`{LEDGER_PATH}#source_classes.conformance_profiles.admitted_profiles[{e['id']}]` — "
        f"class `{e['conformance_class']}`, `{CATALOG_REPOSITORY}@{catalog_revision}` "
        f"`{e['distribution_path']}` `{e['digest']}`."
        for e in entries
    ]
    texts = {
        "MANIFEST.md": [
            f"# Semantic Foundation Manifest {version}",
            "",
            f"Release status: **{STATUS}**",
            "",
            "## Install surface",
            "",
            f"The release contains **{len(sources)}** canonical semantic YAML files:",
            *[f"- `{path}`" for path in sources],
            "",
            "## Decision records",
            "",
            f"The release contains **{len(adrs)}** accepted ADRs under `docs/adr/` (unchanged).",
            "",
            "## Semantic changes",
            "",
            *[f"- {s}" for s in subjects],
            "",
            (
                "No other ledger changes. Generated by `ops/admit-profiles.py` from the pinned "
                f"semantic compiler's birth requirements for `{product_ref}` and the l9-conformance "
                "catalog bytes; no field was typed by an operator."
            ),
            "",
            "## Replacement basis",
            "",
            f"Immediate predecessor: `{RELEASES_PATH}/{predecessor}/`, preserved unchanged.",
            "",
        ],
        "README.md": [
            f"# Semantic Foundation {version}",
            "",
            f"Status: **{STATUS}**",
            "",
            f"Admission candidate for the conformance profiles `{product_ref}` requires.",
            "",
            "## Authority",
            "",
            (
                "`Quantum-L9/.github` owns this ledger; `l9-conformance` owns the profile bodies "
                "(l9.conformance-model/global@1). This record admits nothing itself: admission is "
                "the owner's explicit decision on this exact subject (L9-ADMISSION-001), and the "
                "merge of this record carries it."
            ),
            "",
        ],
        "RELEASE_VALIDATION.md": [
            f"# Release Validation {version}",
            "",
            f"Release status: **{STATUS.lower()}**. No admission is claimed.",
            "",
            "## Closure",
            "",
            (
                "- `ops/admit-profiles.py check` passed for every subject: declared identity, "
                "catalog INDEX entry, file digest, id/class/scope, non-empty membership, no "
                "`unresolved` entry, and immutability of any prior admission."
            ),
            "- The semantic validator passed on this tree before the record was proposed.",
            "",
            "## Release integrity",
            "",
            (
                "`HASHES.sha256` inventories every canonical source, every ADR plus the index, and "
                "this release's Markdown (`sha256sum` with `./` paths, `LC_ALL=C` order by path)."
            ),
            "",
        ],
    }
    target.mkdir(parents=True)
    written = []
    for name, lines in texts.items():
        (target / name).write_text("\n".join(lines), encoding="utf-8")
        written.append(f"{RELEASES_PATH}/{version}/{name}")
    inventory = [f"./{p}" for p in sources] + [f"./docs/adr/{p.name}" for p in adrs]
    inventory += [
        "./docs/adr/README.md",
        "./MANIFEST.md",
        "./README.md",
        "./RELEASE_VALIDATION.md",
    ]
    lines = []
    for rel in sorted(inventory, key=lambda p: p.encode("utf-8")):
        on_disk = target / rel[2:] if rel.count("/") == 1 else root / rel[2:]
        lines.append(f"{_sha256(on_disk).split(':', 1)[1]}  {rel}")
    (target / "HASHES.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(f"{RELEASES_PATH}/{version}/HASHES.sha256")
    return version, written


def run_validator(checkout: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(checkout / VALIDATOR_PATH), "--root", str(checkout)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        failures = [
            line for line in proc.stdout.splitlines() if line.startswith("FAIL")
        ]
        raise AdmissionRefused(
            "semantic validator rejects the tree:\n" + "\n".join(failures[-20:])
        )


def apply(
    *, requirements: Path, catalog: Path, catalog_revision: str, checkout: Path
) -> dict[str, Any]:
    product_ref, candidates = load_candidates(requirements)
    report = check(
        candidates=candidates, catalog=catalog, admitted=ledger_entries(checkout)
    )
    report["product_ref"] = product_ref
    if report["status"] != "admissible":
        raise AdmissionRefused(json.dumps(report, indent=2, sort_keys=True))
    if not report["admissible"]:
        return {**report, "status": "present", "changed_paths": []}
    ledger = checkout / LEDGER_PATH
    original = ledger.read_text(encoding="utf-8")
    ledger.write_text(add_entries(original, report["admissible"]), encoding="utf-8")
    written: list[str] = []
    try:
        version, written = cut_release(
            checkout, product_ref, report["admissible"], catalog_revision
        )
        run_validator(checkout)
    except BaseException:
        ledger.write_text(original, encoding="utf-8")
        for rel in written:
            (checkout / rel).unlink(missing_ok=True)
        if written:
            (checkout / written[0]).parent.rmdir()
        raise
    return {
        **report,
        "status": "proposed",
        "release": version,
        "changed_paths": [LEDGER_PATH, *written],
    }


def _changes_out(raw: str) -> Path:
    base = (
        Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()).resolve()
        / "admission"
    )
    target = Path(raw).resolve()
    if target.parent != base:
        raise AdmissionInputError(f"--changes-out must be a file directly under {base}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("check", "apply"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--requirements", type=Path, required=True)
        cmd.add_argument("--catalog", type=Path, required=True)
        cmd.add_argument("--catalog-revision", required=True)
        if name == "apply":
            cmd.add_argument("--checkout", type=Path, required=True)
            cmd.add_argument("--changes-out")
        else:
            cmd.add_argument("--checkout", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        if not SHA_RE.match(args.catalog_revision):
            raise AdmissionInputError("--catalog-revision must be a full 40-hex commit")
        args.requirements = _input_path(args.requirements, "--requirements")
        args.catalog = _input_path(args.catalog, "--catalog", directory=True)
        args.checkout = _input_path(args.checkout, "--checkout", directory=True)
        if args.cmd == "check":
            product_ref, candidates = load_candidates(args.requirements)
            report = check(
                candidates=candidates,
                catalog=args.catalog,
                admitted=ledger_entries(args.checkout.resolve()),
            )
            report["product_ref"] = product_ref
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report["status"] == "admissible" else 1
        target = _changes_out(args.changes_out) if args.changes_out else None
        result = apply(
            requirements=args.requirements,
            catalog=args.catalog,
            catalog_revision=args.catalog_revision,
            checkout=args.checkout.resolve(),
        )
        if target is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except AdmissionInputError as exc:
        print(f"UNRESOLVED: {exc}", file=sys.stderr)
        return 2
    except AdmissionRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
