#!/usr/bin/env python3
"""Verify an organization-policy release.

A GitHub Sigstore attestation proves the workflow signed these bytes. It does
not admit the policy. ``verified`` requires a checked signature, the default
branch workflow identity, a matching subject, and an owner admission that this
file does not create.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import subprocess
from pathlib import Path
from typing import Any

PREDICATE_TYPE = (
    "https://github.com/Quantum-L9/.github/attestations/"
    "quantum-l9.org-governance-policy/v1"
)
RELEASE_WORKFLOW = "Quantum-L9/.github/.github/workflows/policy-provenance.yml"
MAIN_REF = "refs/heads/main"
ADMISSION_NAMESPACE = "quantum-l9.org-policy-admission"
SUBJECT_PATH = "policies/ORG_INVARIANTS.yaml"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _subject_sha256(statement: dict[str, Any]) -> str:
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or not subjects:
        return ""
    first = subjects[0]
    if not isinstance(first, dict):
        return ""
    digest = first.get("digest")
    if not isinstance(digest, dict):
        return ""
    value = digest.get("sha256")
    return value if isinstance(value, str) else ""


def canonical_admission(subject_sha256: str, subject_commit: str) -> bytes:
    """Bytes an owner key signs. An authority string is not part of this payload."""
    return (
        f"namespace={ADMISSION_NAMESPACE}\n"
        "admitted=true\n"
        f"subject_commit={subject_commit}\n"
        f"subject_path={SUBJECT_PATH}\n"
        f"subject_sha256={subject_sha256}\n"
    ).encode()


def signature_verifies(payload: bytes, signature: str, public_key: str) -> bool:
    """Return whether this Ed25519 trust key signed the exact admission bytes."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
    except ImportError:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key)).verify(
            base64.b64decode(signature),
            payload,
        )
    except (binascii.Error, ValueError, InvalidSignature):
        return False
    return True


def authenticate_admission(
    admission: dict[str, Any] | None,
    *,
    subject_sha256: str,
    subject_commit: str,
    trust_keys: list[dict[str, Any]],
) -> bool:
    """True only when a trust-root key signed this digest and commit.

    ``authority`` text is ignored. An empty trust root rejects every claim.
    """
    if not trust_keys or not isinstance(admission, dict):
        return False
    if admission.get("admitted") is not True:
        return False
    if admission.get("subject_sha256") != subject_sha256:
        return False
    if not isinstance(subject_commit, str) or len(subject_commit) != 40:
        return False
    if admission.get("subject_commit") != subject_commit:
        return False
    signature = admission.get("signature")
    principal = admission.get("principal")
    if not isinstance(signature, str) or not isinstance(principal, str):
        return False
    key = next(
        (
            item.get("public_key")
            for item in trust_keys
            if isinstance(item, dict) and item.get("principal") == principal
        ),
        None,
    )
    if not isinstance(key, str) or not key.strip():
        return False
    return signature_verifies(
        canonical_admission(subject_sha256, subject_commit),
        signature,
        key.strip(),
    )


def decide(
    *,
    subject_sha256: str,
    statement: dict[str, Any] | None,
    signature_verified: bool,
    signer_ref: str,
    signer_workflow: str,
    admission_verified: bool,
) -> tuple[str, str]:
    """Return ``(status, reason)``. A reference or an authority string is not a release."""
    if not signature_verified or not isinstance(statement, dict):
        return "unverified", "signature was not verified"
    attested = _subject_sha256(statement)
    if attested != subject_sha256:
        return "fail", "attested subject does not match the policy bytes"
    if statement.get("predicateType") != PREDICATE_TYPE:
        return "fail", "attestation predicate is not the organization-policy predicate"
    if signer_workflow != RELEASE_WORKFLOW:
        return (
            "fail",
            "signer workflow is not the organization-policy provenance workflow",
        )
    if signer_ref != MAIN_REF:
        return "rejected", "signer ref is not refs/heads/main"
    if not admission_verified:
        return "rejected", "owner admission signature was not verified"
    return (
        "verified",
        "signature, default-branch signer, and owner admission signature match",
    )


def exit_code(status: str) -> int:
    """A rejected or unverified result is a failed release check."""
    return 0 if status == "verified" else 1


def _verify_with_gh(
    subject: Path,
    bundle: Path | None,
    source_ref: str | None,
) -> bool:
    command = [
        "gh",
        "attestation",
        "verify",
        str(subject),
        "--repo",
        "Quantum-L9/.github",
        "--signer-workflow",
        RELEASE_WORKFLOW,
        "--predicate-type",
        PREDICATE_TYPE,
    ]
    if bundle is not None:
        command.extend(["--bundle", str(bundle)])
    if source_ref:
        command.extend(["--source-ref", source_ref])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return completed.returncode == 0


def load_mapping(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    import yaml

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path.parent), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.strip()
    if completed.returncode != 0 or len(value) != 40:
        return ""
    return value


def trust_keys(subject: Path) -> list[dict[str, Any]]:
    document = load_mapping(subject.parent / "admission-trust.yaml") or {}
    keys = document.get("keys")
    if not isinstance(keys, list):
        return []
    return [item for item in keys if isinstance(item, dict)]


def evaluate(subject: Path, bundle: Path | None) -> tuple[str, str]:
    """Verify the Sigstore signature, then the sibling owner admission."""
    signature_verified = _verify_with_gh(subject, bundle, None)
    if not signature_verified:
        return "unverified", "signature was not verified"
    digest = sha256_file(subject)
    on_main = _verify_with_gh(subject, bundle, MAIN_REF)
    statement = {
        "predicateType": PREDICATE_TYPE,
        "subject": [{"digest": {"sha256": digest}}],
    }
    admission = load_mapping(subject.parent / "ADMISSION.yaml")
    return decide(
        subject_sha256=digest,
        statement=statement,
        signature_verified=True,
        signer_ref=MAIN_REF if on_main else "",
        signer_workflow=RELEASE_WORKFLOW,
        admission_verified=authenticate_admission(
            admission,
            subject_sha256=digest,
            subject_commit=git_head(subject),
            trust_keys=trust_keys(subject),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, default=None)
    parser.add_argument(
        "--require-release",
        action="store_true",
        help="Exit 1 unless the decision is verified. This is also the default.",
    )
    args = parser.parse_args()
    status, reason = evaluate(args.subject, args.bundle)
    print(f"org-policy-release: {status}")
    print(f"org-policy-detail: {reason}")
    return exit_code(status)


if __name__ == "__main__":
    raise SystemExit(main())
