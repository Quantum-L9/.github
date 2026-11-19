#!/usr/bin/env python3
"""Verify an organization-policy release.

A GitHub Sigstore attestation proves the workflow signed these bytes. It does
not admit the policy. ``verified`` requires a checked signature, the default
branch workflow identity, a matching subject, and an owner admission that this
file does not create.
"""

from __future__ import annotations

import argparse
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
PRODUCER_MARKERS = ("github-actions", "policy-provenance.yml", "actions/attest")


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


def admission_binds(admission: dict[str, Any] | None, subject_sha256: str) -> bool:
    """True only for an owner admission of this exact digest."""
    if not isinstance(admission, dict) or admission.get("admitted") is not True:
        return False
    if admission.get("subject_sha256") != subject_sha256:
        return False
    authority = admission.get("authority")
    if not isinstance(authority, str) or not authority.strip():
        return False
    lowered = authority.lower()
    return not any(marker in lowered for marker in PRODUCER_MARKERS)


def decide(
    *,
    subject_sha256: str,
    statement: dict[str, Any] | None,
    signature_verified: bool,
    signer_ref: str,
    signer_workflow: str,
    admission: dict[str, Any] | None,
) -> tuple[str, str]:
    """Return ``(status, reason)``. A reference or an unchecked statement is not verified."""
    if not signature_verified or not isinstance(statement, dict):
        return "unverified", "signature was not verified"
    attested = _subject_sha256(statement)
    if attested != subject_sha256:
        return "fail", "attested subject does not match the policy bytes"
    if statement.get("predicateType") != PREDICATE_TYPE:
        return "fail", "attestation predicate is not the organization-policy predicate"
    if signer_workflow != RELEASE_WORKFLOW:
        return "fail", "signer workflow is not the organization-policy provenance workflow"
    if signer_ref != MAIN_REF:
        return "rejected", "signer ref is not refs/heads/main"
    if not admission_binds(admission, subject_sha256):
        return "rejected", "no owner admission binds this digest"
    return "verified", "signature, default-branch signer, and owner admission match"


def _verify_with_gh(subject: Path, bundle: Path, source_ref: str | None) -> bool:
    command = [
        "gh",
        "attestation",
        "verify",
        str(subject),
        "--bundle",
        str(bundle),
        "--repo",
        "Quantum-L9/.github",
        "--signer-workflow",
        RELEASE_WORKFLOW,
        "--predicate-type",
        PREDICATE_TYPE,
    ]
    if source_ref:
        command.extend(["--source-ref", source_ref])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return completed.returncode == 0


def load_admission(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    import yaml

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def evaluate(subject: Path, bundle: Path, admission_path: Path | None) -> tuple[str, str]:
    """Trust ``gh attestation verify`` for the signature, then apply admission."""
    signature_verified = _verify_with_gh(subject, bundle, None)
    if not signature_verified:
        return "unverified", "signature was not verified"
    digest = sha256_file(subject)
    on_main = _verify_with_gh(subject, bundle, MAIN_REF)
    statement = {
        "predicateType": PREDICATE_TYPE,
        "subject": [{"digest": {"sha256": digest}}],
    }
    return decide(
        subject_sha256=digest,
        statement=statement,
        signature_verified=True,
        signer_ref=MAIN_REF if on_main else "",
        signer_workflow=RELEASE_WORKFLOW,
        admission=load_admission(admission_path),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--admission", type=Path, default=None)
    parser.add_argument(
        "--require-release",
        action="store_true",
        help="Exit 1 unless the decision is verified.",
    )
    args = parser.parse_args()
    status, reason = evaluate(args.subject, args.bundle, args.admission)
    print(f"org-policy-release: {status}")
    print(f"org-policy-detail: {reason}")
    if args.require_release and status != "verified":
        return 1
    if status == "fail" or status == "unverified":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
