#!/usr/bin/env python3
"""Turn one organization-hosted repository into one reviewable registry candidate.

Since v3.43.0 (ADR-040) `semantics/repository_registry.yaml` is
organization-complete: every repository the Quantum-L9 organization hosts must
be registered. Hosting still confers nothing. A repository is a member only
through its entry, and the owner's merge of that exact entry is the admission
decision. This tool proposes the entry for a repository created after v3.43.0
so that nobody types it by hand:

    register-org-repository.py render --repository NAME --github-id N --observed-at TS
    register-org-repository.py apply  --repository NAME --github-id N --observed-at TS \\
                                      [--write-result]

Run from the `.github` checkout: the working directory is the tree read and
written. The command line carries no file path. `--write-result` writes the
apply result to the one fixed file `$RUNNER_TEMP/org-admission/admission.json`
(the system temp directory when RUNNER_TEMP is unset).

The entry is fixed by law, never chosen here: id = the folding of the name
(rc023_factory_repository_id), the single current admitted RepositoryClass,
lifecycle `current`, no ProductKind, plus the `organization_admission` marker
(basis, decision record, GitHub's immutable repository id and when the listing
returned it). `apply` writes the entry into a `.github` checkout, cuts the
registry-only successor release record SC-008 requires, runs the semantic
validator on the result, and restores the tree unless it passes.

Every refusal fails closed: an invalid name, an already-archived repository
(admitted by hand with lifecycle retired), an ambiguous class, or an identity
collision (the folded id and the coordinate disagree). The same id and the
same coordinate are already members: apply leaves that entry, including its
recorded admission evidence, and writes nothing. A factory-born repository is the
birth path's to register (ADR-039); the caller skips one that carries a birth
receipt. Re-running is safe: an identical entry is `present` and nothing is
written.

Dependencies: Python 3.11+, PyYAML (the validator's parser pin).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ORG = "Quantum-L9"
PROVIDER = "github"
REGISTRY_PATH = "semantics/repository_registry.yaml"
CLASSES_PATH = "semantics/repository_classes.yaml"
RELEASES_PATH = "docs/semantic-foundation"
VALIDATOR_PATH = "scripts/validate-semantics.py"
BIRTH_TOOL_PATH = "ops/register-birth.py"
BASIS = "organization_completeness"
DECISION_RECORD = "ADR-040"
CHANGES_OUT_NAME = "admission.json"
# The command line's only free text, checked before it reaches anything: a
# GitHub repository name (the shape RC-023 folds into an id) and the UTC
# second the organization listing returned it (what the workflow emits).
REPOSITORY_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
OBSERVED_AT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class OrgAdmissionError(RuntimeError):
    """A refusal: the proposal is not provably the one the law fixes."""


def _load(root: Path, rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, root / rel)
    if spec is None or spec.loader is None:
        raise OrgAdmissionError(f"cannot load {rel}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _birth_tool(root: Path):
    """ops/register-birth.py, reused for its class rule, scalar rendering and
    release-version ordering so both registration paths share one definition."""
    return _load(root, BIRTH_TOOL_PATH, "register_birth")


# ─── rendering ───────────────────────────────────────────────────────────────


def render_entry(
    validator, repository: str, github_id: int, observed_at: str, class_ref: str
) -> dict[str, Any]:
    rid = validator.rc023_factory_repository_id(repository)
    if rid is None:
        raise OrgAdmissionError(f"{repository!r} is not a repository name")
    if rid in validator.RC023_GRANDFATHERED_IDS:
        raise OrgAdmissionError(f"id {rid!r} is a reserved grandfathered id")
    if isinstance(github_id, bool) or not isinstance(github_id, int) or github_id <= 0:
        raise OrgAdmissionError(f"github repository id {github_id!r} is not positive")
    if not observed_at.strip():
        raise OrgAdmissionError("observed_at is empty")
    return {
        "id": rid,
        "coordinate": {
            "provider": PROVIDER,
            "organization": ORG,
            "repository": repository,
        },
        "lifecycle": "current",
        "class_ref": class_ref,
        "organization_admission": {
            "basis": BASIS,
            "decision_record": DECISION_RECORD,
            "github_repository_id": github_id,
            "observed_at": observed_at,
        },
    }


def render_entry_yaml(birth, entry: dict[str, Any]) -> str:
    """The entry in the registry's own layout, one key order, always."""
    coord = entry["coordinate"]
    marker = entry["organization_admission"]
    scalar = birth._scalar
    return (
        "\n".join(
            [
                f"  - id: {scalar(entry['id'])}",
                "    coordinate:",
                f"      provider: {scalar(coord['provider'])}",
                f"      organization: {scalar(coord['organization'])}",
                f"      repository: {scalar(coord['repository'])}",
                f"    lifecycle: {scalar(entry['lifecycle'])}",
                f"    class_ref: {scalar(entry['class_ref'])}",
                "    organization_admission:",
                f"      basis: {scalar(marker['basis'])}",
                f"      decision_record: {scalar(marker['decision_record'])}",
                f"      github_repository_id: {int(marker['github_repository_id'])}",
                f"      observed_at: {scalar(marker['observed_at'])}",
            ]
        )
        + "\n"
    )


def _same_repository(existing: dict[str, Any], entry: dict[str, Any]) -> bool:
    coord = existing.get("coordinate")
    want = entry["coordinate"]
    return (
        isinstance(coord, dict)
        and coord.get("provider") == want["provider"]
        and coord.get("organization") == want["organization"]
        and coord.get("repository") == want["repository"]
    )


def add_entry(birth, registry_text: str, entry: dict[str, Any]) -> tuple[str, str]:
    """(new text, status): `added`, or `present` when that identity is already registered.

    The same folded id and the same coordinate are one member. The recorded
    entry is kept, including an older `observed_at`, so a later listing does
    not open a second admission. The same id with a different coordinate, or
    the same coordinate with a different id, is a collision.
    """
    doc = yaml.safe_load(registry_text)
    repositories = doc.get("repositories") if isinstance(doc, dict) else None
    if not isinstance(repositories, list):
        raise OrgAdmissionError(f"{REGISTRY_PATH} has no repositories list")
    for existing in repositories:
        if not isinstance(existing, dict):
            continue
        same_id = existing.get("id") == entry["id"]
        same_repo = _same_repository(existing, entry)
        if same_id and same_repo:
            return registry_text, "present"
        if same_id or same_repo:
            which = f"id {entry['id']}" if same_id else "/".join(entry["coordinate"].values())
            raise OrgAdmissionError(
                f"registry already holds a different identity for {which}; refusing a duplicate"
            )
    marker = "\naliases:"
    if registry_text.count(marker) != 1:
        raise OrgAdmissionError(
            f"{REGISTRY_PATH}: cannot locate the end of repositories"
        )
    head, tail = registry_text.split(marker, 1)
    new_text = (
        head.rstrip("\n")
        + "\n"
        + render_entry_yaml(birth, entry).rstrip("\n")
        + marker
        + tail
    )
    if yaml.safe_load(new_text)["repositories"][-1] != entry:
        raise OrgAdmissionError("rendered entry does not round-trip; refusing to write")
    return new_text, "added"


# ─── release record ──────────────────────────────────────────────────────────


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cut_release(birth, root: Path, entry: dict[str, Any]) -> tuple[str, list[str]]:
    """The registry-only successor release record: highest vX.Y.Z -> vX.Y.(Z+1).

    SC-008 hashes the registry in the highest release record, and a released
    record is immutable (L9-REVISION-001), so a registry change is a new
    release whose subject is exactly this entry. Returns (version, paths).
    """
    versions = birth.release_versions(root)
    if not versions:
        raise OrgAdmissionError(f"no release record under {RELEASES_PATH}")
    major, minor, patch = versions[-1]
    predecessor = f"v{major}.{minor}.{patch}"
    version = f"v{major}.{minor}.{patch + 1}"
    target = root / RELEASES_PATH / version
    if target.exists():
        raise OrgAdmissionError(f"{RELEASES_PATH}/{version} already exists")
    sources = sorted(f"semantics/{p.name}" for p in (root / "semantics").glob("*.yaml"))
    adrs = sorted((root / "docs" / "adr").glob("ADR-*.md"))
    repo = entry["coordinate"]["repository"]
    marker = entry["organization_admission"]
    subject = (
        f"`{REGISTRY_PATH}#repositories[{entry['id']}]` — `{ORG}/{repo}`, "
        f"class `{entry['class_ref']}`, lifecycle `{entry['lifecycle']}`, "
        f"GitHub repository id `{marker['github_repository_id']}` observed "
        f"`{marker['observed_at']}`."
    )
    status = "REGISTRY-ONLY SUCCESSOR CANDIDATE"
    documents = {
        "MANIFEST.md": [
            f"# Semantic Foundation Manifest {version}",
            "",
            f"Release status: **{status}**",
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
            f"- {subject}",
            "",
            (
                "No other ledger changes. Generated by `ops/register-org-repository.py` from the "
                "organization listing (ADR-040); no field was typed by an operator. The entry "
                "carries no ProductKind and does not admit a Node or constellation participation."
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
            f"Status: **{status}**",
            "",
            f"Admits one organization-hosted repository (ADR-040). Subject: {subject}",
            "",
            (
                "Registration is organization membership and RepositoryClass assignment only. It "
                "is not product admission, a ProductKind, a Node or constellation participation "
                f"(`{REGISTRY_PATH}#does_not_own`)."
            ),
            "",
            "## Authority",
            "",
            (
                "`Quantum-L9/.github` owns this ledger. The organization listing is evidence of "
                "what GitHub hosts and confers no authority (L9-EVIDENCE-001). This record admits "
                "nothing itself: admission is the repository owner's merge of this exact subject."
            ),
            "",
        ],
        "RELEASE_VALIDATION.md": [
            f"# Release Validation {version}",
            "",
            (
                f"Release status: **{status.lower()}**. Admission requires the repository owner's "
                "explicit decision (the merge) for this exact subject; no admission is claimed."
            ),
            "",
            "## Closure",
            "",
            "- RC-023 checks the entry as organization-admitted (ADR-040); SC-008 proves this record.",
            "- `ops/register-org-repository.py` ran the semantic validator on this tree before it was proposed.",
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
    try:
        for name, lines in documents.items():
            (target / name).write_text("\n".join(lines), encoding="utf-8")
            written.append(f"{RELEASES_PATH}/{version}/{name}")
        write_hashes(root, target)
        written.append(f"{RELEASES_PATH}/{version}/HASHES.sha256")
    except BaseException:
        # apply() has not received `written` yet, so a failure here would
        # otherwise leave the new release directory for the next validation.
        shutil.rmtree(target)
        raise
    return version, written


def write_hashes(root: Path, target: Path) -> None:
    """HASHES.sha256 for a release directory, in the SC-008 inventory."""
    sources = sorted(f"semantics/{p.name}" for p in (root / "semantics").glob("*.yaml"))
    adrs = sorted((root / "docs" / "adr").glob("ADR-*.md"))
    inventory = [f"./{path}" for path in sources]
    inventory += [f"./docs/adr/{p.name}" for p in adrs] + ["./docs/adr/README.md"]
    inventory += [f"./{p.name}" for p in sorted(target.glob("*.md"))]
    lines = []
    for entry_path in sorted(inventory, key=lambda p: p.encode("utf-8")):
        on_disk = (
            target / entry_path[2:]
            if entry_path.count("/") == 1
            else root / entry_path[2:]
        )
        lines.append(f"{_sha256(on_disk)}  {entry_path}")
    (target / "HASHES.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─── orchestration ───────────────────────────────────────────────────────────


def render(args: argparse.Namespace, checkout: Path) -> dict[str, Any]:
    if args.archived:
        raise OrgAdmissionError(
            f"{ORG}/{args.repository} is archived: admit it by hand with lifecycle retired"
        )
    birth = _birth_tool(checkout)
    validator = birth._load_validator(checkout)
    classes = yaml.safe_load((checkout / CLASSES_PATH).read_text(encoding="utf-8"))
    try:
        class_ref = birth.admitted_class(classes)
    except birth.BirthRegistrationError as exc:
        raise OrgAdmissionError(str(exc)) from exc
    entry = render_entry(
        validator, args.repository, args.github_id, args.observed_at, class_ref
    )
    problems = validator.rc023_org_entry_problems(entry)
    if problems:
        raise OrgAdmissionError(f"rendered entry fails RC-023: {'; '.join(problems)}")
    return entry


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
        raise OrgAdmissionError(
            "semantic validator rejects the admitted tree:\n"
            + "\n".join(failures[-20:])
        )


def apply(args: argparse.Namespace, checkout: Path) -> dict[str, Any]:
    entry = render(args, checkout)
    birth = _birth_tool(checkout)
    registry_file = checkout / REGISTRY_PATH
    original = registry_file.read_text(encoding="utf-8")
    new_text, status = add_entry(birth, original, entry)
    result: dict[str, Any] = {"status": status, "entry": entry, "changed_paths": []}
    if status == "present":
        return result
    registry_file.write_text(new_text, encoding="utf-8")
    written: list[str] = []
    try:
        version, written = cut_release(birth, checkout, entry)
        run_validator(checkout)
    except BaseException:
        registry_file.write_text(original, encoding="utf-8")
        for rel in written:
            (checkout / rel).unlink(missing_ok=True)
        if written:
            (checkout / written[0]).parent.rmdir()
        raise
    result.update(release=version, changed_paths=[REGISTRY_PATH, *written])
    return result


def changes_out_target() -> Path:
    """The one file the result may be written to: ``$RUNNER_TEMP/org-admission/admission.json``."""
    base = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()
    return Path(base).resolve() / "org-admission" / CHANGES_OUT_NAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="register-org-repository.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("command", choices=("render", "apply"))
    parser.add_argument(
        "--repository", required=True, help="repository name, without owner"
    )
    parser.add_argument(
        "--github-id", required=True, type=int, help="GitHub's numeric repository id"
    )
    parser.add_argument(
        "--observed-at", required=True, help="when the organization listing returned it"
    )
    parser.add_argument(
        "--archived", action="store_true", help="the repository is archived (refused)"
    )
    parser.add_argument(
        "--write-result",
        action="store_true",
        help="also write the result as JSON to $RUNNER_TEMP/org-admission/admission.json",
    )
    args = parser.parse_args(argv)
    checkout = Path.cwd().resolve()
    try:
        name = REPOSITORY_NAME_RE.fullmatch(args.repository)
        if name is None:
            raise OrgAdmissionError(
                f"--repository {args.repository!r} is not a GitHub repository name"
            )
        observed = OBSERVED_AT_RE.fullmatch(args.observed_at)
        if observed is None:
            raise OrgAdmissionError(
                f"--observed-at {args.observed_at!r} is not a UTC timestamp "
                "YYYY-MM-DDTHH:MM:SSZ"
            )
        args.repository, args.observed_at = name.group(0), observed.group(0)
        if args.command == "render":
            result: dict[str, Any] = {
                "status": "rendered",
                "entry": render(args, checkout),
            }
        else:
            result = apply(args, checkout)
        out = changes_out_target()
        if args.write_result and out.is_symlink():
            raise OrgAdmissionError(f"{out} must not be a symlink")
    except OrgAdmissionError as exc:
        print(f"register-org-repository: REFUSED: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.write_result:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
