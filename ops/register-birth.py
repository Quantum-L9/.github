#!/usr/bin/env python3
"""Turn one factory birth into one reviewable repository-registry candidate.

`semantics/repository_registry.yaml` is explicit membership: a repository is a
member because an entry names it, and the merge of that entry is the admission
decision (ADR-039). Typing the entry by hand for every newborn is the manual
step this removes. The entry is derived only from what the factory attested —
the newborn's committed `.l9/birth-receipt.json`, its root commit, and the
factory's own integrity verifier — never from operator-typed input.

    register-birth.py verify  --newborn DIR --template DIR --repository NAME
    register-birth.py render  --newborn DIR --template DIR --repository NAME
    register-birth.py apply   --newborn DIR --template DIR --repository NAME \
                              --checkout DIR [--changes-out FILE]

`verify` proves the birth. `render` prints the registry entry as JSON. `apply`
writes the entry into a `.github` checkout, cuts the registry-only successor
release record SC-008 requires, and (with --changes-out) lists the changed
paths for the caller that opens the pull request. Every subcommand fails closed:
an unverifiable receipt, an unknown or ambiguous class, a conflicting entry, or
a tree the semantic validator rejects is an error, never a partial write.

Re-running is safe. A registry that already holds exactly this entry is
`present` and nothing is written; a registry holding a different entry for the
same id or coordinate is a conflict and is refused.

Dependencies: Python 3.11+, git, PyYAML (the validator's parser pin).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ORG = "Quantum-L9"
PROVIDER = "github"
FACTORY = "Quantum-L9/l9-repo-template"
RECEIPT_SCHEMA = "l9.birth-receipt/v1"
RECEIPT_PATH = ".l9/birth-receipt.json"
REGISTRY_PATH = "semantics/repository_registry.yaml"
CLASSES_PATH = "semantics/repository_classes.yaml"
RELEASES_PATH = "docs/semantic-foundation"
VALIDATOR_PATH = "scripts/validate-semantics.py"
FACTORY_VERIFIER = "scripts/birth-runner/verify_birth_integrity.py"
FACTORY_REF = "origin/main"
TRAILER_RECEIPT = "L9-Birth-Receipt"
TRAILER_TEMPLATE = "L9-Template"
TRAILER_CLASS = "L9-Class"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
VERSION_DIR_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
_TRAILER_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*):[ \t]*(.*)$")


class BirthRegistrationError(RuntimeError):
    """The birth cannot be turned into a registry entry; nothing was written."""


# ─── shared law: one id rule, owned by the validator ────────────────────────


def _load_validator(root: Path):
    """The semantic validator of the `.github` checkout being written.

    The id rule and the factory-entry shape live in RC-023. Importing them
    rather than restating them keeps the writer and the checker on one
    algorithm (the same reason the factory keeps one provenance module).
    """
    path = root / VALIDATOR_PATH
    spec = importlib.util.spec_from_file_location("l9_validate_semantics", path)
    if spec is None or spec.loader is None:
        raise BirthRegistrationError(f"cannot load the semantic validator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ─── git ─────────────────────────────────────────────────────────────────────


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        detail = ((proc.stderr or "") + (proc.stdout or "")).strip()
        raise BirthRegistrationError(f"git {' '.join(args)} failed: {detail[-400:]}")
    return proc.stdout


def root_commit(root: Path) -> str:
    if git(root, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise BirthRegistrationError(
            "the newborn checkout is shallow; its root commit cannot be attested"
        )
    roots = git(root, "rev-list", "--max-parents=0", "HEAD").split()
    if len(roots) != 1:
        raise BirthRegistrationError(
            f"expected exactly one root commit, found {len(roots)}"
        )
    return roots[0]


def parse_trailers(message: str) -> dict[str, str]:
    """Git's rule: trailers are the last paragraph of a multi-paragraph message."""
    lines = message.strip().splitlines()
    paragraph: list[str] = []
    for line in reversed(lines):
        if not line.strip():
            break
        paragraph.insert(0, line.strip())
    if not paragraph or len(paragraph) == len(lines):
        return {}
    matches = [_TRAILER_LINE.match(line) for line in paragraph]
    if not all(matches):
        return {}
    return {m.group(1): m.group(2).strip() for m in matches if m}


# ─── verification ────────────────────────────────────────────────────────────


def receipt_digest(receipt: dict[str, Any]) -> str:
    """The factory's algorithm (birth_provenance.receipt_digest): sha256 over
    sorted-key compact JSON of the receipt without its own digest field."""
    body = {key: value for key, value in receipt.items() if key != "digest"}
    data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_receipt(newborn: Path) -> dict[str, Any]:
    path = newborn / RECEIPT_PATH
    if not path.is_file():
        raise BirthRegistrationError(
            f"{RECEIPT_PATH} is absent: this repository was not factory-born"
        )
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BirthRegistrationError(f"{RECEIPT_PATH} is not JSON: {exc}") from exc
    if not isinstance(receipt, dict):
        raise BirthRegistrationError(f"{RECEIPT_PATH} is not an object")
    return receipt


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BirthRegistrationError(f"receipt {field} is not an object")
    return value


def verify_receipt(newborn: Path, repository: str, receipt: dict[str, Any]) -> str:
    """The receipt's own claims, checked here. Returns the root commit.

    This does not replace the factory verifier; it pins what the registry entry
    depends on (identity, factory, digest, trailers) so an entry can never be
    rendered from a receipt that only the factory script was asked about.
    """
    if not REPO_NAME_RE.match(repository):
        raise BirthRegistrationError(f"invalid repository name {repository!r}")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise BirthRegistrationError(
            f"receipt schema is {receipt.get('schema')!r}, expected {RECEIPT_SCHEMA}"
        )
    expected_slug = f"{ORG}/{repository}"
    if receipt.get("repository") != expected_slug:
        raise BirthRegistrationError(
            f"receipt names {receipt.get('repository')!r}, not {expected_slug}"
        )
    template = _mapping(receipt.get("template"), "template")
    policy = _mapping(receipt.get("org_policy"), "org_policy")
    if template.get("repository") != FACTORY:
        raise BirthRegistrationError(
            f"receipt template is {template.get('repository')!r}, not the factory {FACTORY}"
        )
    for field, value in (
        ("template.sha", template.get("sha")),
        ("org_policy.sha", policy.get("sha")),
    ):
        if not isinstance(value, str) or not SHA_RE.match(value):
            raise BirthRegistrationError(
                f"receipt {field} is not a commit sha: {value!r}"
            )
    for field in ("repo_class", "born_at"):
        if not isinstance(receipt.get(field), str) or not receipt[field]:
            raise BirthRegistrationError(f"receipt {field} is missing")
    if not isinstance(template.get("version"), str) or not template["version"]:
        raise BirthRegistrationError("receipt template.version is missing")
    recorded = receipt.get("digest")
    recomputed = receipt_digest(receipt)
    if not isinstance(recorded, str) or recorded != recomputed:
        raise BirthRegistrationError(
            f"receipt digest {str(recorded)[:12]!r} does not match its content ({recomputed[:12]})"
        )
    commit = root_commit(newborn)
    trailers = parse_trailers(git(newborn, "log", "-1", "--format=%B", commit))
    expected = {
        TRAILER_RECEIPT: f"sha256:{recomputed}",
        TRAILER_TEMPLATE: template["sha"],
        TRAILER_CLASS: receipt["repo_class"],
    }
    wrong = sorted(key for key, value in expected.items() if trailers.get(key) != value)
    if wrong:
        raise BirthRegistrationError(
            f"root commit {commit[:12]} trailers disagree with the receipt: {', '.join(wrong)}"
        )
    at_root = git(newborn, "show", f"{commit}:{RECEIPT_PATH}")
    if at_root != (newborn / RECEIPT_PATH).read_text(encoding="utf-8"):
        raise BirthRegistrationError(
            f"{RECEIPT_PATH} was modified after the root commit"
        )
    return commit


def verify_factory_revision(template: Path, sha: str) -> None:
    """The template commit the receipt names must be factory history.

    The factory verifier is run from that very commit, so it has to be a commit
    of the factory's default branch — not a fork branch carrying a verifier that
    passes everything.
    """
    proc = subprocess.run(
        ["git", "-C", str(template), "merge-base", "--is-ancestor", sha, FACTORY_REF],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise BirthRegistrationError(
            f"template commit {sha[:12]} is not on {FACTORY} {FACTORY_REF}"
        )


def run_factory_verifier(template: Path, sha: str, newborn: Path) -> dict[str, Any]:
    """BIRTH INTEGRITY, answered by the factory at the commit that did the birth."""
    verify_factory_revision(template, sha)
    worktree = template / ".l9-birth-registry-verifier"
    if worktree.exists():
        git(template, "worktree", "remove", "--force", str(worktree))
    git(template, "worktree", "add", "--detach", str(worktree), sha)
    try:
        verifier = worktree / FACTORY_VERIFIER
        if not verifier.is_file():
            raise BirthRegistrationError(
                f"template commit {sha[:12]} carries no {FACTORY_VERIFIER}"
            )
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                str(verifier),
                "--root",
                str(newborn),
                "--require-receipt",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        git(template, "worktree", "remove", "--force", str(worktree))
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise BirthRegistrationError(
            f"factory verifier produced no report (exit {proc.returncode}): {proc.stderr[-300:]}"
        ) from exc
    checks = report.get("checks") if isinstance(report, dict) else None
    if not isinstance(checks, list) or not checks:
        raise BirthRegistrationError("factory verifier report carries no checks")
    not_passed = [
        c for c in checks if not isinstance(c, dict) or c.get("status") != "PASS"
    ]
    if proc.returncode != 0 or report.get("result") != "PASS" or not_passed:
        names = ", ".join(
            f"{c.get('key')}={c.get('status')}"
            for c in not_passed
            if isinstance(c, dict)
        )
        raise BirthRegistrationError(
            f"factory birth integrity is not PASS: {names or proc.stderr[-300:]}"
        )
    return report


# ─── rendering ───────────────────────────────────────────────────────────────


def admitted_class(classes_doc: dict[str, Any]) -> str:
    """The one current admitted RepositoryClass, or a refusal.

    The class is an admission decision, never inferred from the birth profile.
    While the catalog admits exactly one current class, proposing it is the
    only assignment the merge can approve; if that ever stops being unique the
    proposal is ambiguous and fails closed.
    """
    admitted = (classes_doc.get("catalog_status") or {}).get("admitted_classes") or []
    current = [
        spec.get("id")
        for spec in (classes_doc.get("classes") or {}).values()
        if isinstance(spec, dict)
        and spec.get("status") == "current"
        and spec.get("id") in admitted
    ]
    if len(current) != 1:
        raise BirthRegistrationError(
            f"repository class is ambiguous: {len(current)} current admitted classes {current}"
        )
    return str(current[0])


def render_entry(
    validator, repository: str, receipt: dict[str, Any], commit: str, class_ref: str
) -> dict[str, Any]:
    template = receipt["template"]
    return {
        "id": validator.rc023_factory_repository_id(repository),
        "coordinate": {
            "provider": PROVIDER,
            "organization": ORG,
            "repository": repository,
        },
        "lifecycle": "current",
        "class_ref": class_ref,
        "birth_provenance": {
            "factory": FACTORY,
            "receipt_schema": RECEIPT_SCHEMA,
            "receipt_digest": f"sha256:{receipt['digest']}",
            "root_commit": commit,
            "template_sha": template["sha"],
            "template_version": str(template["version"]),
            "org_policy_sha": receipt["org_policy"]["sha"],
            "birth_profile": str(receipt["repo_class"]),
            "born_at": str(receipt["born_at"]),
        },
    }


def _scalar(value: str) -> str:
    """A YAML scalar that loads back as exactly this string (plain when safe)."""
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:+-]*", value)
        and yaml.safe_load(value) == value
    ):
        return value
    return json.dumps(value)


def render_entry_yaml(entry: dict[str, Any]) -> str:
    """The entry in the registry's own layout, one key order, always."""
    coord = entry["coordinate"]
    prov = entry["birth_provenance"]
    lines = [
        f"  - id: {_scalar(entry['id'])}",
        "    coordinate:",
        f"      provider: {_scalar(coord['provider'])}",
        f"      organization: {_scalar(coord['organization'])}",
        f"      repository: {_scalar(coord['repository'])}",
        f"    lifecycle: {_scalar(entry['lifecycle'])}",
        f"    class_ref: {_scalar(entry['class_ref'])}",
        "    birth_provenance:",
    ]
    for key in (
        "factory",
        "receipt_schema",
        "receipt_digest",
        "root_commit",
        "template_sha",
        "template_version",
        "org_policy_sha",
        "birth_profile",
        "born_at",
    ):
        lines.append(f"      {key}: {_scalar(prov[key])}")
    return "\n".join(lines) + "\n"


def add_entry(registry_text: str, entry: dict[str, Any]) -> tuple[str, str]:
    """(new text, status) where status is `added` or `present`.

    `present`: an identical entry already exists — a re-run, nothing to do.
    Any other entry sharing the id or the coordinate is a conflict.
    """
    doc = yaml.safe_load(registry_text)
    repositories = doc.get("repositories") if isinstance(doc, dict) else None
    if not isinstance(repositories, list):
        raise BirthRegistrationError(f"{REGISTRY_PATH} has no repositories list")
    coordinate = entry["coordinate"]
    for existing in repositories:
        if not isinstance(existing, dict):
            continue
        same_id = existing.get("id") == entry["id"]
        same_coord = existing.get("coordinate") == coordinate
        if same_id or same_coord:
            if existing == entry:
                return registry_text, "present"
            raise BirthRegistrationError(
                f"registry already holds a different entry for "
                f"{'id ' + entry['id'] if same_id else '/'.join(coordinate.values())}; refusing a duplicate"
            )
    marker = "\naliases:"
    if registry_text.count(marker) != 1:
        raise BirthRegistrationError(
            f"{REGISTRY_PATH}: cannot locate the end of repositories"
        )
    head, tail = registry_text.split(marker, 1)
    new_text = (
        head.rstrip("\n") + "\n" + render_entry_yaml(entry).rstrip("\n") + marker + tail
    )
    if yaml.safe_load(new_text)["repositories"][-1] != entry:
        raise BirthRegistrationError(
            "rendered entry does not round-trip; refusing to write"
        )
    return new_text, "added"


# ─── release record ──────────────────────────────────────────────────────────


def release_versions(root: Path) -> list[tuple[int, int, int]]:
    base = root / RELEASES_PATH
    found = []
    for path in base.iterdir() if base.is_dir() else []:
        match = VERSION_DIR_RE.match(path.name)
        if match and path.is_dir():
            found.append(tuple(int(part) for part in match.groups()))
    return sorted(found)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cut_release(root: Path, entry: dict[str, Any]) -> tuple[str, list[str]]:
    """The registry-only successor release record: highest vX.Y.Z -> vX.Y.(Z+1).

    SC-008 hashes the registry in the highest release record, and a released
    record is immutable (L9-REVISION-001), so a registry change is a new
    release. Its subject is exactly one entry; its admission is the merge.
    Returns (version, written paths).
    """
    versions = release_versions(root)
    if not versions:
        raise BirthRegistrationError(f"no release record under {RELEASES_PATH}")
    major, minor, patch = versions[-1]
    predecessor = f"v{major}.{minor}.{patch}"
    version = f"v{major}.{minor}.{patch + 1}"
    target = root / RELEASES_PATH / version
    if target.exists():
        raise BirthRegistrationError(f"{RELEASES_PATH}/{version} already exists")
    sources = sorted(f"semantics/{p.name}" for p in (root / "semantics").glob("*.yaml"))
    adrs = sorted((root / "docs" / "adr").glob("ADR-*.md"))
    repo = entry["coordinate"]["repository"]
    prov = entry["birth_provenance"]
    subject = (
        f"`{REGISTRY_PATH}#repositories[{entry['id']}]` — `{ORG}/{repo}`, "
        f"class `{entry['class_ref']}`, lifecycle `{entry['lifecycle']}`, "
        f"factory receipt `{prov['receipt_digest']}` (root commit `{prov['root_commit']}`, "
        f"template `{prov['template_sha']}`)."
    )
    status = "REGISTRY-ONLY SUCCESSOR CANDIDATE"
    manifest = "\n".join(
        [
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
                "No other ledger changes. Generated by `ops/register-birth.py` from the "
                "factory-attested birth record (ADR-039); no field was typed by an operator."
            ),
            "",
            "## Replacement basis",
            "",
            f"Immediate predecessor: `{RELEASES_PATH}/{predecessor}/`, preserved unchanged.",
            "",
        ]
    )
    readme = "\n".join(
        [
            f"# Semantic Foundation {version}",
            "",
            f"Status: **{status}**",
            "",
            f"Registers one factory-born repository. Subject: {subject}",
            "",
            (
                "Registration is repository identity and RepositoryClass assignment only. It is "
                "not product admission, deployment or runtime readiness "
                f"(`{REGISTRY_PATH}#does_not_own`)."
            ),
            "",
            "## Authority",
            "",
            (
                "`Quantum-L9/.github` owns this ledger. The birth receipt is evidence of what the "
                "factory produced and confers no authority (L9-EVIDENCE-001). This record admits "
                "nothing itself: admission is the repository owner's merge of this exact subject."
            ),
            "",
        ]
    )
    validation = "\n".join(
        [
            f"# Release Validation {version}",
            "",
            (
                f"Release status: **{status.lower()}**. Admission requires the repository owner's "
                "explicit decision (the merge) for this exact subject; no admission is claimed."
            ),
            "",
            "## Closure",
            "",
            (
                "- The factory's `verify_birth_integrity.py --require-receipt`, run from the template "
                "commit the receipt names (an ancestor of the factory's default branch), passed every "
                "check against a full clone of the newborn."
            ),
            (
                "- The receipt digest, root-commit trailers and immutability were re-checked by "
                "`ops/register-birth.py`."
            ),
            "- RC-023 checks the entry as factory-born (ADR-039); SC-008 proves this record.",
            "",
            "## Release integrity",
            "",
            (
                "`HASHES.sha256` inventories every canonical source, every ADR plus the index, and "
                "this release's Markdown (`sha256sum` with `./` paths, `LC_ALL=C` order by path)."
            ),
            "",
        ]
    )
    target.mkdir(parents=True)
    written = []
    for name, text in (
        ("MANIFEST.md", manifest),
        ("README.md", readme),
        ("RELEASE_VALIDATION.md", validation),
    ):
        (target / name).write_text(text, encoding="utf-8")
        written.append(f"{RELEASES_PATH}/{version}/{name}")
    inventory = [f"./{path}" for path in sources]
    inventory += [f"./docs/adr/{p.name}" for p in adrs] + ["./docs/adr/README.md"]
    inventory += [
        f"./{name}" for name in ("MANIFEST.md", "README.md", "RELEASE_VALIDATION.md")
    ]
    lines = []
    for entry_path in sorted(inventory, key=lambda p: p.encode("utf-8")):
        on_disk = (
            target / entry_path[2:]
            if entry_path.count("/") == 1
            else root / entry_path[2:]
        )
        lines.append(f"{_sha256(on_disk)}  {entry_path}")
    (target / "HASHES.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(f"{RELEASES_PATH}/{version}/HASHES.sha256")
    return version, written


# ─── orchestration ───────────────────────────────────────────────────────────


def prove_and_render(args: argparse.Namespace, checkout: Path) -> dict[str, Any]:
    newborn = Path(args.newborn).resolve()
    template = Path(args.template).resolve()
    receipt = load_receipt(newborn)
    commit = verify_receipt(newborn, args.repository, receipt)
    if not args.skip_factory_verifier:
        run_factory_verifier(template, receipt["template"]["sha"], newborn)
    validator = _load_validator(checkout)
    classes = yaml.safe_load((checkout / CLASSES_PATH).read_text(encoding="utf-8"))
    entry = render_entry(
        validator, args.repository, receipt, commit, admitted_class(classes)
    )
    problems = validator.rc023_factory_entry_problems(entry)
    if problems:
        raise BirthRegistrationError(
            f"rendered entry fails RC-023: {'; '.join(problems)}"
        )
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
        raise BirthRegistrationError(
            "semantic validator rejects the registered tree:\n"
            + "\n".join(failures[-20:])
        )


def apply(args: argparse.Namespace) -> dict[str, Any]:
    checkout = Path(args.checkout).resolve()
    entry = prove_and_render(args, checkout)
    registry_file = checkout / REGISTRY_PATH
    original = registry_file.read_text(encoding="utf-8")
    new_text, status = add_entry(original, entry)
    result: dict[str, Any] = {"status": status, "entry": entry, "changed_paths": []}
    if status == "present":
        return result
    registry_file.write_text(new_text, encoding="utf-8")
    written: list[str] = []
    try:
        version, written = cut_release(checkout, entry)
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


def confined_output(raw: str) -> Path:
    """Resolve ``--changes-out`` to a JSON file inside an allowed scratch root.

    The result file is a run artifact, never a repository edit, so it may only
    land under the runner's temp directory, the system temp directory or the
    working directory. Anything else (a traversal, an absolute path elsewhere,
    a symlink or a non-JSON name) is refused before a byte is written.
    """
    candidate = Path(raw)
    if candidate.is_symlink():
        raise BirthRegistrationError(f"--changes-out must not be a symlink: {raw}")
    target = candidate.resolve()
    if target.suffix != ".json":
        raise BirthRegistrationError(f"--changes-out must name a .json file: {raw}")
    roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve()]
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        roots.append(Path(runner_temp).resolve())
    if not any(target.is_relative_to(root) for root in roots):
        raise BirthRegistrationError(
            f"--changes-out must be inside the working directory or a temp directory: {raw}"
        )
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="register-birth.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("command", choices=("verify", "render", "apply"))
    parser.add_argument(
        "--newborn", required=True, help="full (non-shallow) clone of the newborn"
    )
    parser.add_argument(
        "--template", required=True, help="full clone of Quantum-L9/l9-repo-template"
    )
    parser.add_argument(
        "--repository", required=True, help="newborn repository name, without owner"
    )
    parser.add_argument(
        "--checkout", default=".", help="Quantum-L9/.github checkout (default: cwd)"
    )
    parser.add_argument(
        "--changes-out", help="write the apply result as JSON to this file"
    )
    parser.add_argument(
        "--skip-factory-verifier",
        action="store_true",
        help=argparse.SUPPRESS,  # tests only: fixtures carry no factory checkout
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            receipt = load_receipt(Path(args.newborn).resolve())
            commit = verify_receipt(
                Path(args.newborn).resolve(), args.repository, receipt
            )
            if not args.skip_factory_verifier:
                run_factory_verifier(
                    Path(args.template).resolve(),
                    receipt["template"]["sha"],
                    Path(args.newborn).resolve(),
                )
            result: dict[str, Any] = {"status": "verified", "root_commit": commit}
        elif args.command == "render":
            result = {
                "status": "rendered",
                "entry": prove_and_render(args, Path(args.checkout).resolve()),
            }
        else:
            result = apply(args)
    except BirthRegistrationError as exc:
        print(f"register-birth: REFUSED: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.changes_out:
        try:
            out = confined_output(args.changes_out)
        except BirthRegistrationError as exc:
            print(f"register-birth: REFUSED: {exc}", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
