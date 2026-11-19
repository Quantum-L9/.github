from __future__ import annotations

import base64
import importlib.util
import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "verify_release", ROOT / "verify_release.py"
)
assert SPEC is not None
assert SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)

DIGEST = "fdb3a6d45af46f237470671b57873557301f1261679d67c352cda5a81661b59c"
COMMIT = "9d68f33220477f48ea427910d59c05848e37d311"


def statement() -> dict:
    return {
        "predicateType": verify.PREDICATE_TYPE,
        "subject": [{"digest": {"sha256": DIGEST}}],
    }


def signed_admission() -> tuple[dict, list[dict[str, str]]]:
    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    signature = base64.b64encode(
        private.sign(verify.canonical_admission(DIGEST, COMMIT))
    ).decode()
    return (
        {
            "admitted": True,
            "subject_sha256": DIGEST,
            "subject_commit": COMMIT,
            "principal": "owner",
            "signature": signature,
            "authority": "governance-admins",
        },
        [{"principal": "owner", "public_key": public}],
    )


class ReleaseVerificationTests(unittest.TestCase):
    def test_authority_text_is_not_admission(self) -> None:
        self.assertFalse(
            verify.authenticate_admission(
                {
                    "admitted": True,
                    "subject_sha256": DIGEST,
                    "subject_commit": COMMIT,
                    "authority": "governance-admins",
                },
                subject_sha256=DIGEST,
                subject_commit=COMMIT,
                trust_keys=[{"principal": "owner", "public_key": "ssh-ed25519 AAAA"}],
            )
        )

    def test_empty_trust_root_rejects_a_signed_claim(self) -> None:
        admission, _keys = signed_admission()
        self.assertFalse(
            verify.authenticate_admission(
                admission,
                subject_sha256=DIGEST,
                subject_commit=COMMIT,
                trust_keys=[],
            )
        )

    def test_trusted_signature_of_this_commit_passes(self) -> None:
        admission, keys = signed_admission()
        self.assertTrue(
            verify.authenticate_admission(
                admission,
                subject_sha256=DIGEST,
                subject_commit=COMMIT,
                trust_keys=keys,
            )
        )
        status, _reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission_verified=True,
        )
        self.assertEqual("verified", status)
        self.assertEqual(0, verify.exit_code(status))

    def test_signature_for_a_different_commit_fails(self) -> None:
        admission, keys = signed_admission()
        self.assertFalse(
            verify.authenticate_admission(
                admission,
                subject_sha256=DIGEST,
                subject_commit="a" * 40,
                trust_keys=keys,
            )
        )

    def test_unchecked_signature_is_not_verified(self) -> None:
        status, reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=False,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission_verified=True,
        )
        self.assertEqual("unverified", status)
        self.assertEqual(1, verify.exit_code(status))
        self.assertIn("not verified", reason)

    def test_pull_request_signer_is_a_failed_release_check(self) -> None:
        status, _reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref="refs/pull/269/merge",
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission_verified=True,
        )
        self.assertEqual("rejected", status)
        self.assertEqual(1, verify.exit_code(status))

    def test_tampered_subject_fails(self) -> None:
        status, _reason = verify.decide(
            subject_sha256="b" * 64,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission_verified=True,
        )
        self.assertEqual("fail", status)
        self.assertEqual(1, verify.exit_code(status))

    def test_missing_admission_is_rejected(self) -> None:
        status, reason = verify.decide(
            subject_sha256=DIGEST,
            statement=statement(),
            signature_verified=True,
            signer_ref=verify.MAIN_REF,
            signer_workflow=verify.RELEASE_WORKFLOW,
            admission_verified=False,
        )
        self.assertEqual("rejected", status)
        self.assertIn("admission", reason)
