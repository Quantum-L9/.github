from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "verify_release.py")
assert SPEC is not None
assert SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)

DIGEST = "fdb3a6d45af46f237470671b57873557301f1261679d67c352cda5a81661b59c"


def statement() -> dict:
    return {
        "predicateType": verify.PREDICATE_TYPE,
        "subject": [{"digest": {"sha256": DIGEST}}],
    }


def admission() -> dict:
    return {
        "admitted": True,
        "subject_sha256": DIGEST,
        "authority": "governance-admins",
    }


class ReleaseVerificationTests(unittest.TestCase):
    def test_unchecked_signature_is_not_verified(self) -> None:
        status, reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=False,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission=admission(),
        )
        self.assertEqual("unverified", status)
        self.assertIn("not verified", reason)

    def test_pull_request_signer_is_rejected(self) -> None:
        status, _reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref="refs/pull/269/merge",
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission=admission(),
        )
        self.assertEqual("rejected", status)

    def test_workflow_cannot_admit_itself(self) -> None:
        self.assertFalse(
            verify.admission_binds(
                {
                    "admitted": True,
                    "subject_sha256": DIGEST,
                    "authority": "github-actions policy-provenance.yml",
                },
                DIGEST,
            )
        )

    def test_owner_admission_of_the_signed_default_branch_passes(self) -> None:
        status, _reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission=admission(),
        )
        self.assertEqual("verified", status)

    def test_tampered_subject_fails(self) -> None:
        status, _reason = verify.decide(
            subject_sha256="a" * 64,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission=admission(),
        )
        self.assertEqual("fail", status)

    def test_missing_admission_is_rejected(self) -> None:
        status, reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission=None,
        )
        self.assertEqual("rejected", status)
        self.assertIn("admission", reason)
