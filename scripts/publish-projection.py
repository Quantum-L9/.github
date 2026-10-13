#!/usr/bin/env python3
"""Publish a producer-emitted semantic projection pair to the `projections` branch.

`Quantum-L9/.github` `main` owns the canonical sources and this publisher;
`projections` holds only derived, immutable artifact/receipt pairs plus a
transport index. The Semantic Compiler (`l9-semantic-compiler`, the component
`semantics/vocabulary.yaml` assigns the `projection` role) produces each pair.
This script never runs the compiler, never executes selectors, and never
builds or repairs a pair: it verifies one, stages it, and advances the branch.

Subcommands (all print one JSON result on stdout):
  pins     source/profile digests at an independently supplied revision pin,
           for the compiler's --expect-source-digest/--expect-profile-digest
  verify   recompute every binding of one producer output pair
  publish  plan (default, writes nothing) or --apply one commit holding the
           pair and the index, advanced by compare-and-swap (local) or a
           non-force push (remote). Never creates the branch.
  check    read the index and the pair from ONE fixed commit and report
           CURRENT / STALE / REJECTED against an independent pin

The revision pin must come from an independent record of canonical `main`
(e.g. the GitHub API), never from a receipt, an index, or the checkout being
checked: law bytes are bound to the pin, but the pin itself is not
authenticated here. Compiler receipts are unkeyed, so a verified pair proves
digest integrity and producer role, not who produced it.

Exit codes: 0 ok (PLANNED, PUBLISHED, NOOP_*, VERIFIED, CURRENT, PINNED),
1 REJECTED, 2 usage, 3 BLOCKED (Unknown), 4 STALE, 5 CONFLICT (lost a race;
re-evaluate, never force).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # an interpreter without PyYAML is Unknown, not REJECTED
    print(
        json.dumps(
            {
                "status": "BLOCKED",
                "reason": "INTERPRETER_WITHOUT_PYYAML",
                "error": repr(exc),
            }
        )
    )
    raise SystemExit(3) from exc

OWNER_REPOSITORY = "Quantum-L9/.github"
PRODUCER = "l9-semantic-compiler"
REGISTRY_PATH = "semantics/canonical_sources.yaml"
ARTIFACT_SCHEMA_PATH = "semantics/projection_artifact.schema.yaml"
RECEIPT_SCHEMA_PATH = "semantics/compiler_receipt.schema.yaml"
CATALOG_REF = "l9.source/projection-profiles@1"
ARTIFACT_SCHEMA = "l9.projection-artifact/v1"
RECEIPT_SCHEMA = "l9.compiler-receipt/v1"
RECEIPT_TYPE = "l9.receipt/compilation@1"
INDEX_PATH = "index.json"
PROJECTION_FILE = "projection.json"
RECEIPT_FILE = "receipt.json"
INDEX_FORMAT = (
    "quantum-l9-github/projections-index@1"  # transport format, not semantic law
)
DEFAULT_BRANCH = "projections"
DEFAULT_PROFILE = "l9.projection/cursor-governance-operating-plane@1"
DEFAULT_SOURCE_CLASS = "invariants"

EXIT = {"REJECTED": 1, "BLOCKED": 3, "STALE": 4, "CONFLICT": 5}
GIT_TIMEOUT_S = 60
GIT_ENV = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0"}
_SHA1 = re.compile(r"[0-9a-f]{40}")
_ORIGIN = re.compile(
    r"(?:https://(?:[^@/\s]+@)?github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"quantum-l9/\.github(?:\.git)?/?",
    re.IGNORECASE,
)
_SOURCE_CLASS = re.compile(r"[a-z0-9_]+")
# Values that reach git argv: never option-like, never shell-meaningful.
_REMOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class Outcome(Exception):
    def __init__(self, status: str, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.status, self.reason, self.detail = status, reason, detail


# ── digests (the producer's conventions, recomputed independently) ──────────


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return digest_bytes(canonical_json(value))


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-JSON number {name}")


def load_json(data: bytes, what: str) -> dict[str, Any]:
    try:
        doc = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except ValueError as exc:  # includes UnicodeDecodeError
        raise Outcome("REJECTED", "MALFORMED_JSON", input=what, error=str(exc)) from exc
    if not isinstance(doc, dict):
        raise Outcome("REJECTED", "MALFORMED_JSON", input=what, error="not an object")
    return doc


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(
    loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict:
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in seen
            seen.add(key)
        except TypeError as exc:  # a list or mapping key: not plain YAML law
            raise yaml.constructor.ConstructorError(
                None, None, f"unhashable key {key!r}", key_node.start_mark
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)


def load_yaml(data: bytes, what: str) -> dict[str, Any]:
    try:
        doc = yaml.load(data.decode("utf-8"), Loader=_UniqueKeyLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise Outcome(
            "BLOCKED", "AUTHORITY_UNREADABLE", path=what, error=str(exc)
        ) from exc
    if not isinstance(doc, dict):
        raise Outcome(
            "BLOCKED", "AUTHORITY_UNREADABLE", path=what, error="not a mapping"
        )
    return doc


# ── git ─────────────────────────────────────────────────────────────────────


def git(
    repo: Path,
    *args: str,
    data: bytes | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=data,
        capture_output=True,
        timeout=GIT_TIMEOUT_S,
        env={**GIT_ENV, **(env or {})},
        check=False,
    )
    if check and proc.returncode != 0:
        raise Outcome(
            "BLOCKED",
            "GIT_FAILED",
            repo=str(repo),
            args=list(args),
            stderr=proc.stderr.decode("utf-8", "replace").strip()[-400:],
        )
    return proc


def git_out(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.decode("utf-8").strip()


def blob_at(repo: Path, commit: str, path: str) -> bytes | None:
    """Bytes of `path` in `commit`, read from the object store; None when absent."""
    proc = git(repo, "cat-file", "blob", f"{commit}:{path}", check=False)
    return proc.stdout if proc.returncode == 0 else None


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return (
        git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode
        == 0
    )


# ── argv safety: CLI values that reach git ─────────────────────────────────


def require_branch(repo: Path, branch: str) -> str:
    if (
        branch.startswith("-")
        or git(repo, "check-ref-format", "--branch", branch, check=False).returncode
    ):
        raise Outcome("REJECTED", "UNSAFE_BRANCH_NAME", branch=branch)
    return branch


def require_remote(repo: Path, remote: str) -> str:
    """A remote must be a plain, already-configured name; a URL or option is refused."""
    if (
        not _REMOTE_NAME.fullmatch(remote)
        or remote not in git_out(repo, "remote").split()
    ):
        raise Outcome("REJECTED", "UNSAFE_OR_UNKNOWN_REMOTE", remote=remote)
    return remote


def require_full_ref(repo: Path, ref: str) -> str:
    if (
        not ref.startswith("refs/")
        or git(repo, "check-ref-format", ref, check=False).returncode
    ):
        raise Outcome("REJECTED", "UNSAFE_REF_NAME", ref=ref)
    return ref


def require_commit_sha(commit: str) -> str:
    if not _SHA1.fullmatch(commit or ""):
        raise Outcome(
            "REJECTED",
            "PUBLICATION_COMMIT_MALFORMED",
            commit=commit,
            detail="name the publication commit by its full 40-hex SHA",
        )
    return commit


# ── authority: independent pin ──────────────────────────────────────────────


def require_pin(revision: str | None) -> str:
    if not revision or not _SHA1.fullmatch(revision):
        raise Outcome(
            "BLOCKED",
            "REVISION_PIN_ABSENT_OR_MALFORMED",
            revision=revision,
            detail="a 40-hex canonical main revision from an independent record is required",
        )
    return revision


def bind_authority(root: Path, revision: str | None) -> str:
    """Bind the authority checkout to the pin; fail closed on anything local-only."""
    pin = require_pin(revision)
    if (
        not (root / ".git").exists()
        and git(root, "rev-parse", "--git-dir", check=False).returncode
    ):
        raise Outcome("BLOCKED", "AUTHORITY_ROOT_NOT_A_GIT_CHECKOUT", root=str(root))
    origin = (
        git(root, "config", "--get", "remote.origin.url", check=False)
        .stdout.decode()
        .strip()
    )
    if not _ORIGIN.fullmatch(origin):
        raise Outcome(
            "BLOCKED",
            "AUTHORITY_ORIGIN_UNVERIFIED",
            origin=origin,
            expected=OWNER_REPOSITORY,
        )
    if git(root, "cat-file", "-e", f"{pin}^{{commit}}", check=False).returncode:
        raise Outcome("BLOCKED", "REVISION_PIN_UNKNOWN_COMMIT", revision=pin)
    containing = git_out(
        root,
        "for-each-ref",
        "--contains",
        pin,
        "--format=%(refname)",
        "refs/remotes/origin",
    )
    if not containing:
        raise Outcome(
            "BLOCKED",
            "REVISION_PIN_NOT_IN_FETCHED_ORIGIN",
            revision=pin,
            detail="the pin must be contained in a fetched origin ref of the canonical owner",
        )
    return pin


def _single_selector(profile: dict[str, Any], source_class: str) -> list[str]:
    """One selector and no reshape is the only payload shape the producer defines."""
    spec = (profile.get("sources") or {}).get(source_class)
    if not isinstance(spec, dict):
        raise Outcome(
            "REJECTED",
            "UNSUPPORTED_SOURCE_CLASS",
            source_class=source_class,
            detail="profile declares no such source class",
        )
    selectors = spec.get("selectors")
    if (
        not isinstance(selectors, list)
        or len(selectors) != 1
        or not isinstance(selectors[0], str)
        or "reshape" in spec
    ):
        raise Outcome(
            "REJECTED",
            "UNSUPPORTED_SOURCE_CLASS",
            source_class=source_class,
            selectors=selectors,
            detail="multi-selector or reshaped classes have no declared payload shape and are not published",
        )
    return selectors


def compute_pins(
    root: Path, revision: str, profile_ref: str, source_class: str
) -> dict[str, Any]:
    """Source and profile digests at `revision`, from commit objects, never the working tree."""
    if not _SOURCE_CLASS.fullmatch(source_class):
        raise Outcome("REJECTED", "UNSUPPORTED_SOURCE_CLASS", source_class=source_class)

    def read(path: str) -> bytes:
        data = blob_at(root, revision, path)
        if data is None:
            raise Outcome(
                "BLOCKED", "AUTHORITY_PATH_ABSENT", revision=revision, path=path
            )
        return data

    registry_bytes = read(REGISTRY_PATH)
    registry = load_yaml(registry_bytes, REGISTRY_PATH)
    entries = [e for e in registry.get("sources") or [] if isinstance(e, dict)]

    def entry(**match: str) -> dict[str, Any]:
        found = [e for e in entries if all(e.get(k) == v for k, v in match.items())]
        if len(found) != 1:
            raise Outcome(
                "BLOCKED", "SOURCE_REGISTRY_UNRESOLVED", match=match, matches=len(found)
            )
        return found[0]

    catalog_path = entry(id=CATALOG_REF).get("path")
    if not isinstance(catalog_path, str) or not catalog_path:
        raise Outcome("BLOCKED", "CATALOG_PATH_ABSENT", ref=CATALOG_REF)
    catalog_bytes = read(str(catalog_path))
    catalog = load_yaml(catalog_bytes, str(catalog_path))
    profiles = [
        p
        for p in catalog.get("projection_profiles") or []
        if isinstance(p, dict) and p.get("id") == profile_ref
    ]
    if len(profiles) != 1:
        raise Outcome(
            "BLOCKED", "PROFILE_UNRESOLVED", profile=profile_ref, matches=len(profiles)
        )
    profile = profiles[0]
    selectors = _single_selector(profile, source_class)
    class_artifact = (
        (catalog.get("source_classes") or {}).get(source_class) or {}
    ).get("canonical_artifact")
    if not isinstance(class_artifact, str) or not class_artifact:
        raise Outcome(
            "BLOCKED",
            "SOURCE_CLASS_CANONICAL_ARTIFACT_ABSENT",
            source_class=source_class,
        )
    source = entry(path=f"semantics/{class_artifact}")
    if (
        source.get("canonical") is not True
        or source.get("projection_allowed") is not True
    ):
        raise Outcome("REJECTED", "SOURCE_NOT_PROJECTABLE", source=source.get("id"))
    try:
        profile_digest = digest(profile)
    except (TypeError, ValueError) as exc:
        raise Outcome("BLOCKED", "PROFILE_NOT_PLAIN_JSON", error=str(exc)) from exc
    return {
        "authority_revision": revision,
        "profile_ref": profile_ref,
        "profile_digest": profile_digest,
        "source_class": source_class,
        "selectors": selectors,
        "source_ref": source.get("id"),
        "source_path": source.get("path"),
        "source_digest": digest_bytes(read(str(source.get("path")))),
        "catalog_digest": digest_bytes(catalog_bytes),
        "registry_digest": digest_bytes(registry_bytes),
        "authority_owner": (registry.get("authority") or {}).get("owner"),
        # Canonical shapes the pair must satisfy, read at the same revision.
        "schemas": {
            "artifact": load_yaml(read(ARTIFACT_SCHEMA_PATH), ARTIFACT_SCHEMA_PATH),
            "receipt": load_yaml(read(RECEIPT_SCHEMA_PATH), RECEIPT_SCHEMA_PATH),
        },
    }


# ── producer output pair ────────────────────────────────────────────────────


def _expect(cond: bool, reason: str, **detail: Any) -> None:
    if not cond:
        raise Outcome("REJECTED", reason, **detail)


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "semantic_ref": lambda v: isinstance(v, str) and bool(v),
    "semantic_digest": lambda v: isinstance(v, str) and bool(_DIGEST.fullmatch(v)),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "any": lambda v: True,
}


def require_schema(doc: dict[str, Any], schema: dict[str, Any], what: str) -> None:
    """Enforce a canonical l9.schema-definition/v1: required, const, type, nested required."""
    required = schema.get("required")
    if not isinstance(required, list) or not required:
        raise Outcome(
            "BLOCKED",
            "SCHEMA_UNRESOLVED",
            input=what,
            detail="schema declares no required fields",
        )
    missing = sorted(set(required) - set(doc))
    _expect(not missing, "SCHEMA_REQUIRED_FIELD_MISSING", input=what, missing=missing)
    for key, rule in (schema.get("properties") or {}).items():
        if key not in doc or not isinstance(rule, dict):
            continue
        value = doc[key]
        if "const" in rule:
            _expect(
                value == rule["const"], "SCHEMA_CONST_MISMATCH", input=what, field=key
            )
        kind = rule.get("type")
        if kind is not None:
            check = _TYPE_CHECKS.get(kind)
            if check is None:  # an unknown schema type is unresolved law, not a pass
                raise Outcome(
                    "BLOCKED",
                    "SCHEMA_TYPE_UNRESOLVED",
                    input=what,
                    field=key,
                    type=kind,
                )
            _expect(
                check(value), "SCHEMA_TYPE_MISMATCH", input=what, field=key, type=kind
            )
        nested = rule.get("required")
        if isinstance(nested, list) and isinstance(value, dict):
            _expect(
                set(nested) <= set(value),
                "SCHEMA_REQUIRED_FIELD_MISSING",
                input=what,
                field=key,
                missing=sorted(set(nested) - set(value)),
            )


def verify_pair(
    artifact_bytes: bytes,
    receipt_bytes: bytes,
    pins: dict[str, Any],
    expected_revision: str | None,
) -> dict[str, Any]:
    """Recompute every binding of one pair; any mismatch is REJECTED.

    `expected_revision` set: the receipt must assert exactly that revision
    (publication). None: only digest equality with the pins is required and
    the asserted revision is returned for the caller to place (currentness).
    """
    artifact = load_json(artifact_bytes, PROJECTION_FILE)
    receipt = load_json(receipt_bytes, RECEIPT_FILE)
    require_schema(artifact, pins["schemas"]["artifact"], PROJECTION_FILE)
    require_schema(receipt, pins["schemas"]["receipt"], RECEIPT_FILE)
    _expect(
        artifact.get("schema") == ARTIFACT_SCHEMA,
        "ARTIFACT_SCHEMA_MISMATCH",
        schema=artifact.get("schema"),
    )
    _expect(
        receipt.get("schema") == RECEIPT_SCHEMA,
        "RECEIPT_SCHEMA_MISMATCH",
        schema=receipt.get("schema"),
    )
    _expect(receipt.get("receipt_type") == RECEIPT_TYPE, "RECEIPT_TYPE_MISMATCH")
    _expect(
        receipt.get("operation") == "projection" and receipt.get("result") == "pass",
        "RECEIPT_NOT_A_PASSING_PROJECTION",
        operation=receipt.get("operation"),
        result=receipt.get("result"),
    )

    # pins: computed here from the authority, never read from the pair
    _expect(
        artifact.get("source_ref") == pins["source_ref"]
        and artifact.get("source_digest") == pins["source_digest"],
        "SOURCE_DIGEST_MISMATCH",
        expected=pins["source_digest"],
        observed=artifact.get("source_digest"),
    )
    _expect(
        artifact.get("projection_profile_ref") == pins["profile_ref"]
        and artifact.get("projection_profile_digest") == pins["profile_digest"],
        "PROFILE_DIGEST_MISMATCH",
        expected=pins["profile_digest"],
        observed=artifact.get("projection_profile_digest"),
    )
    try:
        payload_digest = digest(artifact.get("payload"))
    except (TypeError, ValueError) as exc:
        raise Outcome("REJECTED", "PAYLOAD_NOT_PLAIN_JSON", error=str(exc)) from exc
    _expect(
        "payload" in artifact and artifact.get("projection_digest") == payload_digest,
        "PROJECTION_DIGEST_MISMATCH",
        expected=payload_digest,
        observed=artifact.get("projection_digest"),
    )
    generated = artifact.get("generated_by") or {}
    producer = receipt.get("producer_identity") or {}
    _expect(
        generated.get("compiler") == PRODUCER
        and producer.get("compiler") == PRODUCER
        and generated.get("version") == producer.get("version")
        and isinstance(producer.get("version"), str),
        "PRODUCER_ROLE_MISMATCH",
        generated_by=generated,
        producer_identity=producer,
    )

    # receipt binds this artifact
    _expect(
        receipt.get("exact_subject_ref") == pins["profile_ref"],
        "RECEIPT_SUBJECT_MISMATCH",
    )
    _expect(
        receipt.get("profile")
        == {"ref": pins["profile_ref"], "digest": pins["profile_digest"]},
        "RECEIPT_PROFILE_MISMATCH",
    )
    _expect(
        receipt.get("output")
        == {
            "ref": f"{pins['profile_ref']}#{pins['source_class']}",
            "digest": artifact["projection_digest"],
        },
        "RECEIPT_OUTPUT_UNBOUND",
    )
    inputs = receipt.get("inputs") or []
    _expect(
        {"ref": pins["source_ref"], "digest": pins["source_digest"]} in inputs
        and {"ref": CATALOG_REF, "digest": pins["catalog_digest"]} in inputs,
        "RECEIPT_INPUTS_UNBOUND",
    )
    gov = receipt.get("governing_coordinates") or {}
    _expect(
        gov.get("source_class") == pins["source_class"]
        and gov.get("selectors") == pins["selectors"]
        and gov.get("canonical_source_registry_digest") == pins["registry_digest"]
        and gov.get("authority_owner") == OWNER_REPOSITORY,
        "RECEIPT_GOVERNING_MISMATCH",
    )
    asserted = gov.get("authority_revision")
    _expect(
        isinstance(asserted, str) and bool(_SHA1.fullmatch(asserted)),
        "RECEIPT_REVISION_UNASSERTED",
        observed=asserted,
    )
    if expected_revision is not None:
        _expect(
            asserted == expected_revision,
            "RECEIPT_REVISION_MISMATCH",
            expected=expected_revision,
            observed=asserted,
        )

    body = {k: v for k, v in receipt.items() if k != "receipt_digest"}
    _expect(receipt.get("receipt_digest") == digest(body), "RECEIPT_DIGEST_MISMATCH")
    identity = (
        "l9.receipt-instance/"
        + digest({**body, "receipt_identity": "pending"}).split(":", 1)[1]
    )
    _expect(receipt.get("receipt_identity") == identity, "RECEIPT_IDENTITY_MISMATCH")
    return {
        "projection_digest": artifact["projection_digest"],
        "receipt_digest": receipt["receipt_digest"],
        "receipt_identity": receipt["receipt_identity"],
        "receipt_authority_revision": asserted,
        "compiler_version": producer["version"],
        "files": {
            PROJECTION_FILE: digest_bytes(artifact_bytes),
            RECEIPT_FILE: digest_bytes(receipt_bytes),
        },
        # Unkeyed receipts: role and digests are checked, the producer is not authenticated.
        "producer_authentication": "unauthenticated_unkeyed_receipt",
    }


def read_pair_dir(pair_dir: Path) -> tuple[bytes, bytes]:
    """The producer's two files, as regular files inside `pair_dir`; symlinks are refused."""
    base = Path(os.path.realpath(pair_dir))
    found = []
    for name in (PROJECTION_FILE, RECEIPT_FILE):
        try:
            fd = os.open(base / name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise OSError(f"{name} is not a regular file")
                found.append(handle.read())
        except OSError as exc:
            raise Outcome(
                "BLOCKED",
                "PRODUCER_OUTPUT_ABSENT",
                pair_dir=str(pair_dir),
                error=str(exc),
            ) from exc
    return found[0], found[1]


# ── publication store ───────────────────────────────────────────────────────


def entry_key(pins: dict[str, Any]) -> str:
    return f"{pins['profile_ref']}#{pins['source_class']}"


def pair_paths(source_class: str, receipt_digest: str) -> tuple[str, str]:
    base = f"pairs/{source_class}/{receipt_digest.split(':', 1)[1]}"
    return f"{base}/{PROJECTION_FILE}", f"{base}/{RECEIPT_FILE}"


def load_index(repo: Path, commit: str) -> dict[str, Any]:
    data = blob_at(repo, commit, INDEX_PATH)
    if data is None:
        return {"transport_format": INDEX_FORMAT, "entries": {}}
    index = load_json(data, INDEX_PATH)
    _expect(
        index.get("transport_format") == INDEX_FORMAT
        and isinstance(index.get("entries"), dict),
        "INDEX_FORMAT_UNSUPPORTED",
        observed=index.get("transport_format"),
    )
    return index


def index_bytes(index: dict[str, Any]) -> bytes:
    return (
        json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def resolve_base(repo: Path, branch: str, remote: str | None) -> str:
    """Current tip of the target branch. The publisher never creates it."""
    ref = f"refs/heads/{require_branch(repo, branch)}"
    if remote:
        require_remote(repo, remote)
        listed = git_out(repo, "ls-remote", "--refs", remote, ref)
        if not listed:
            raise Outcome(
                "BLOCKED",
                "TARGET_REF_ABSENT",
                remote=remote,
                ref=ref,
                detail="creating the publication branch is an activation step, not a publisher action",
            )
        tip = listed.split()[0]
        git(repo, "fetch", "--no-tags", "--quiet", remote, ref)
        _expect(
            git_out(repo, "rev-parse", "FETCH_HEAD") == tip,
            "TARGET_REF_MOVED_DURING_FETCH",
        )
        return tip
    proc = git(
        repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False
    )
    if proc.returncode:
        raise Outcome(
            "BLOCKED",
            "TARGET_REF_ABSENT",
            ref=ref,
            detail="creating the publication branch is an activation step, not a publisher action",
        )
    return proc.stdout.decode().strip()


def plan_publication(
    repo: Path,
    base: str,
    authority_root: Path,
    pins: dict[str, Any],
    facts: dict[str, Any],
    pair: tuple[bytes, bytes],
    compiler_revision: str,
) -> dict[str, Any]:
    index = load_index(repo, base)
    key = entry_key(pins)
    prior = index["entries"].get(key)
    if prior is not None:
        current = prior.get("current") or {}
        if current.get("receipt_digest") == facts["receipt_digest"]:
            return {"status": "NOOP_IDENTICAL", "base": base, "entry": key}
        if (
            current.get("source_digest") == pins["source_digest"]
            and current.get("profile_digest") == pins["profile_digest"]
        ):
            # A later unrelated authority revision: semantics unchanged, nothing to republish.
            return {
                "status": "NOOP_UNCHANGED_SEMANTICS",
                "base": base,
                "entry": key,
                "current_authority_revision": current.get("authority_revision"),
            }
        older = current.get("authority_revision")
        if not (
            isinstance(older, str)
            and _SHA1.fullmatch(older)
            and is_ancestor(authority_root, older, pins["authority_revision"])
        ):
            raise Outcome(
                "REJECTED",
                "ROLLBACK_REFUSED",
                current=older,
                candidate=pins["authority_revision"],
                detail="a material change must come from a descendant of the current revision",
            )

    projection_path, receipt_path = pair_paths(
        pins["source_class"], facts["receipt_digest"]
    )
    for path, data in ((projection_path, pair[0]), (receipt_path, pair[1])):
        existing = blob_at(repo, base, path)
        _expect(
            existing is None or existing == data, "IMMUTABLE_PATH_COLLISION", path=path
        )

    record = {
        "pair": projection_path.rsplit("/", 1)[0],
        "files": facts["files"],
        "projection_digest": facts["projection_digest"],
        "receipt_digest": facts["receipt_digest"],
        "receipt_identity": facts["receipt_identity"],
        "producer_authentication": facts["producer_authentication"],
        "source_ref": pins["source_ref"],
        "source_digest": pins["source_digest"],
        "profile_ref": pins["profile_ref"],
        "profile_digest": pins["profile_digest"],
        "authority_revision": pins["authority_revision"],
        "authority_revision_basis": "independent_pin_verified_in_fetched_canonical_origin",
        "compiler": {
            "name": PRODUCER,
            "version": facts["compiler_version"],
            "revision": compiler_revision,
            "revision_basis": "caller_asserted",
        },
    }
    history = ([prior["current"]] + list(prior.get("history") or [])) if prior else []
    index["entries"][key] = {"current": record, "history": history}
    # The publication commit cannot name itself; its parent is recorded instead.
    index["previous_publication"] = base
    return {
        "status": "PLANNED",
        "base": base,
        "entry": key,
        "record": record,
        "files": {
            projection_path: pair[0],
            receipt_path: pair[1],
            INDEX_PATH: index_bytes(index),
        },
    }


def build_commit(repo: Path, base: str, files: dict[str, bytes], message: str) -> str:
    """One commit on `base` whose tree holds every staged file; no ref is touched."""
    identity = {
        "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "l9-projection-publisher"),
        "GIT_AUTHOR_EMAIL": os.environ.get(
            "GIT_AUTHOR_EMAIL", "l9-projection-publisher@users.noreply.github.com"
        ),
        "GIT_COMMITTER_NAME": os.environ.get(
            "GIT_COMMITTER_NAME", "l9-projection-publisher"
        ),
        "GIT_COMMITTER_EMAIL": os.environ.get(
            "GIT_COMMITTER_EMAIL", "l9-projection-publisher@users.noreply.github.com"
        ),
    }
    with tempfile.TemporaryDirectory(prefix="l9-projection-index-") as tmp:
        env = {**identity, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
        git(repo, "read-tree", base, env=env)
        for path, data in sorted(files.items()):
            blob = (
                git(repo, "hash-object", "-w", "--stdin", data=data)
                .stdout.decode()
                .strip()
            )
            git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                f"100644,{blob},{path}",
                env=env,
            )
        tree = git(repo, "write-tree", env=env).stdout.decode().strip()
    return (
        git(repo, "commit-tree", tree, "-p", base, "-m", message, env=identity)
        .stdout.decode()
        .strip()
    )


def advance(repo: Path, branch: str, base: str, new: str, remote: str | None) -> None:
    """Fast-forward `branch` from `base` to `new`, or lose cleanly. Never forces."""
    ref = f"refs/heads/{require_branch(repo, branch)}"
    require_commit_sha(base)
    require_commit_sha(new)
    if remote is None:
        if git(repo, "update-ref", ref, new, base, check=False).returncode:
            raise Outcome(
                "CONFLICT",
                "TARGET_REF_MOVED",
                ref=ref,
                expected=base,
                detail="another publisher advanced the branch; re-evaluate from the new tip",
            )
        return
    listed = git_out(repo, "ls-remote", "--refs", remote, ref)
    if not listed or listed.split()[0] != base:
        raise Outcome(
            "CONFLICT",
            "TARGET_REF_MOVED",
            remote=remote,
            ref=ref,
            expected=base,
            observed=listed.split()[0] if listed else None,
        )
    # A plain refspec: the server rejects anything that is not a fast-forward.
    push = git(repo, "push", "--porcelain", remote, f"{new}:{ref}", check=False)
    if push.returncode:
        raise Outcome(
            "CONFLICT",
            "PUSH_REJECTED_NOT_FAST_FORWARD",
            remote=remote,
            ref=ref,
            stderr=push.stderr.decode("utf-8", "replace").strip()[-400:],
        )


def require_canonical_fresh(
    authority_root: Path, pins: dict[str, Any], canonical_ref: str
) -> None:
    """Refuse to promote when canonical main has already moved the material inputs."""
    require_full_ref(authority_root, canonical_ref)
    tip = git(
        authority_root,
        "rev-parse",
        "--verify",
        "--quiet",
        f"{canonical_ref}^{{commit}}",
        check=False,
    )
    if tip.returncode:
        raise Outcome("BLOCKED", "CANONICAL_REF_UNAVAILABLE", ref=canonical_ref)
    tip_sha = tip.stdout.decode().strip()
    if not is_ancestor(authority_root, pins["authority_revision"], tip_sha):
        raise Outcome(
            "BLOCKED",
            "REVISION_PIN_NOT_ON_CANONICAL_LINE",
            revision=pins["authority_revision"],
            canonical_ref=canonical_ref,
            canonical_tip=tip_sha,
        )
    now = compute_pins(
        authority_root, tip_sha, pins["profile_ref"], pins["source_class"]
    )
    if (now["source_digest"], now["profile_digest"]) != (
        pins["source_digest"],
        pins["profile_digest"],
    ):
        raise Outcome(
            "STALE",
            "MATERIAL_INPUT_CHANGED_ON_CANONICAL",
            canonical_tip=tip_sha,
            pinned={"source": pins["source_digest"], "profile": pins["profile_digest"]},
            canonical={
                "source": now["source_digest"],
                "profile": now["profile_digest"],
            },
        )


# ── fixed-commit currentness ───────────────────────────────────────────────


def check_publication(
    repo: Path,
    commit: str,
    authority_root: Path,
    revision: str,
    profile_ref: str,
    source_class: str,
) -> dict[str, Any]:
    proc = git(
        repo,
        "rev-parse",
        "--verify",
        "--quiet",
        f"{require_commit_sha(commit)}^{{commit}}",
        check=False,
    )
    if proc.returncode:
        raise Outcome("BLOCKED", "PUBLICATION_COMMIT_UNKNOWN", commit=commit)
    fixed = proc.stdout.decode().strip()  # every read below is from this one commit
    pins = compute_pins(authority_root, revision, profile_ref, source_class)
    entry = load_index(repo, fixed)["entries"].get(entry_key(pins))
    if not entry:
        raise Outcome(
            "BLOCKED", "NO_PUBLISHED_ENTRY", commit=fixed, entry=entry_key(pins)
        )
    current = entry["current"]
    pair = []
    for name in (PROJECTION_FILE, RECEIPT_FILE):
        data = blob_at(repo, fixed, f"{current.get('pair')}/{name}")
        if data is None:
            raise Outcome(
                "REJECTED",
                "INDEXED_PAIR_ABSENT",
                commit=fixed,
                path=f"{current.get('pair')}/{name}",
            )
        _expect(
            digest_bytes(data) == (current.get("files") or {}).get(name),
            "INDEXED_FILE_HASH_MISMATCH",
            file=name,
        )
        pair.append(data)

    # The pair binds the authority at the revision its receipt asserts. That
    # revision is trusted only as an ancestor of the independent pin, never
    # because the index or receipt says so.
    published = (
        load_json(pair[1], RECEIPT_FILE).get("governing_coordinates") or {}
    ).get("authority_revision")
    _expect(
        isinstance(published, str) and bool(_SHA1.fullmatch(published)),
        "RECEIPT_REVISION_UNASSERTED",
    )
    if not is_ancestor(authority_root, published, revision):
        raise Outcome(
            "REJECTED",
            "PUBLISHED_REVISION_NOT_IN_PINNED_HISTORY",
            published=published,
            pinned=revision,
        )
    facts = verify_pair(
        pair[0],
        pair[1],
        compute_pins(authority_root, published, profile_ref, source_class),
        published,
    )
    _expect(
        facts["receipt_digest"] == current.get("receipt_digest"),
        "INDEX_RECEIPT_MISMATCH",
    )

    # Currentness is semantic: the source and profile digests, as the consumer binds them.
    observed = (pins["source_digest"], pins["profile_digest"])
    if (current.get("source_digest"), current.get("profile_digest")) != observed:
        raise Outcome(
            "STALE",
            "MATERIAL_INPUT_CHANGED",
            commit=fixed,
            published_revision=published,
            pinned_revision=revision,
        )
    return {
        "status": "CURRENT",
        "commit": fixed,
        "entry": entry_key(pins),
        "pinned_revision": revision,
        "published_authority_revision": published,
        **facts,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────


def _printable(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"sha256": digest_bytes(value), "bytes": len(value)}
    if isinstance(value, dict):
        return {k: _printable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_printable(v) for v in value]
    return value


def run(args: argparse.Namespace) -> dict[str, Any]:
    authority = Path(args.authority_root)
    revision = bind_authority(authority, args.revision)
    pins = compute_pins(authority, revision, args.profile, args.source_class)
    if args.command == "pins":
        return {"status": "PINNED", **{k: v for k, v in pins.items() if k != "schemas"}}
    if args.command == "check":
        return check_publication(
            Path(args.repo),
            args.commit,
            authority,
            revision,
            args.profile,
            args.source_class,
        )

    pair = read_pair_dir(Path(args.pair_dir))
    facts = verify_pair(pair[0], pair[1], pins, expected_revision=revision)
    _expect(
        Path(args.pair_dir).name == facts["receipt_digest"].split(":", 1)[1],
        "PAIR_DIRECTORY_NOT_CONTENT_ADDRESSED",
        pair_dir=str(args.pair_dir),
    )
    if args.command == "verify":
        return {"status": "VERIFIED", **facts}

    if not args.compiler_revision or not _SHA1.fullmatch(args.compiler_revision):
        raise Outcome(
            "BLOCKED",
            "COMPILER_REVISION_ABSENT",
            detail="--compiler-revision must name the producer commit",
        )
    require_canonical_fresh(authority, pins, args.canonical_ref)
    repo = Path(args.repo)
    base = resolve_base(repo, args.branch, args.remote)
    plan = plan_publication(
        repo, base, authority, pins, facts, pair, args.compiler_revision
    )
    if plan["status"] != "PLANNED" or not args.apply:
        return {**plan, "applied": False, "branch": args.branch, "remote": args.remote}
    message = f"publish {plan['entry']} {facts['receipt_digest']}\n\nauthority_revision: {revision}\n"
    new = build_commit(repo, base, plan["files"], message)
    advance(repo, args.branch, base, new, args.remote)
    return {
        **plan,
        "status": "PUBLISHED",
        "applied": True,
        "commit": new,
        "branch": args.branch,
        "remote": args.remote,
    }


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("pins", "verify", "publish", "check"):
        p = sub.add_parser(name)
        p.add_argument(
            "--authority-root",
            required=True,
            help="Quantum-L9/.github checkout with fetched origin refs",
        )
        p.add_argument(
            "--revision",
            required=True,
            help="40-hex canonical main pin from an independent record",
        )
        p.add_argument("--profile", default=DEFAULT_PROFILE)
        p.add_argument("--source-class", default=DEFAULT_SOURCE_CLASS)
        if name in ("verify", "publish"):
            p.add_argument(
                "--pair-dir",
                required=True,
                help="producer output <out>/<class>/<receipt hex>",
            )
        if name in ("publish", "check"):
            p.add_argument(
                "--repo",
                required=True,
                help="git repository holding the publication branch",
            )
        if name == "publish":
            p.add_argument("--branch", default=DEFAULT_BRANCH)
            p.add_argument(
                "--remote",
                default=None,
                help="push to this remote (non-force); default is a local ref",
            )
            p.add_argument(
                "--canonical-ref",
                default="refs/remotes/origin/main",
                help="authority-root ref holding fetched canonical main, for pre-advance freshness",
            )
            p.add_argument(
                "--compiler-revision",
                default=None,
                help="40-hex producer commit (recorded, caller-asserted)",
            )
            p.add_argument(
                "--apply",
                action="store_true",
                help="write objects and advance; default only plans",
            )
        if name == "check":
            p.add_argument(
                "--commit",
                required=True,
                help="the one publication commit every read comes from",
            )
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result, code = run(args), 0
    except Outcome as out:
        result, code = (
            {"status": out.status, "reason": out.reason, **out.detail},
            EXIT[out.status],
        )
    print(json.dumps(_printable(result), indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
