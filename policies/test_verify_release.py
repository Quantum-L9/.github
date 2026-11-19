from __future__ import annotations

import base64
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
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

    def test_later_admission_commit_proves_the_signed_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            source, _head, digest, admission, keys = _admitted_history(repo)
            subject = repo / "policies" / "ORG_INVARIANTS.yaml"
            previous = os.getcwd()
            os.chdir(repo)
            try:
                self.assertEqual(
                    (digest, source), verify.release_binding(subject, admission)
                )
            finally:
                os.chdir(previous)
            self.assertTrue(
                verify.authenticate_admission(
                    admission,
                    subject_sha256=digest,
                    subject_commit=source,
                    trust_keys=keys,
                )
            )

    def test_signature_over_the_admission_commit_is_not_a_release(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            _source, head, digest, admission, _keys = _admitted_history(repo)
            private = Ed25519PrivateKey.generate()
            public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
            signature = base64.b64encode(
                private.sign(verify.canonical_admission(digest, head))
            ).decode()
            circular = dict(admission)
            circular["subject_commit"] = head
            circular["signature"] = signature
            circular["principal"] = "owner"
            previous = os.getcwd()
            os.chdir(repo)
            try:
                self.assertIsNone(
                    verify.release_binding(
                        repo / "policies" / "ORG_INVARIANTS.yaml", circular
                    )
                )
            finally:
                os.chdir(previous)
            self.assertTrue(
                verify.authenticate_admission(
                    circular,
                    subject_sha256=digest,
                    subject_commit=head,
                    trust_keys=[{"principal": "owner", "public_key": public}],
                )
            )

    def test_changed_policy_bytes_break_the_source_binding(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            _source, _head, _digest, admission, _keys = _admitted_history(repo)
            subject = repo / "policies" / "ORG_INVARIANTS.yaml"
            subject.write_text("changed\n", encoding="utf-8")
            previous = os.getcwd()
            os.chdir(repo)
            try:
                self.assertIsNone(verify.release_binding(subject, admission))
            finally:
                os.chdir(previous)

    def test_a_path_outside_the_working_directory_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            outside = Path(raw) / "ORG_INVARIANTS.yaml"
            outside.write_text("policy: candidate\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify.sha256_file(outside)

    def test_a_commit_argument_cannot_inject_a_git_option(self) -> None:
        self.assertEqual("", verify.blob_sha256(Path("."), "HEAD", verify.SUBJECT_PATH))
        self.assertFalse(
            verify.is_strict_ancestor(Path("."), "--output=/tmp/x", "a" * 40)
        )

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


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Release Test",
            "GIT_AUTHOR_EMAIL": "release-test@example.com",
            "GIT_COMMITTER_NAME": "Release Test",
            "GIT_COMMITTER_EMAIL": "release-test@example.com",
        },
    )
    return completed.stdout.strip()


def _admitted_history(
    repo: Path,
) -> tuple[str, str, str, dict[str, object], list[dict[str, str]]]:
    """Commit the policy, sign that commit, then commit the admission later."""
    _git(repo, "init", "-b", "main")
    policy = repo / "policies"
    policy.mkdir()
    subject = policy / "ORG_INVARIANTS.yaml"
    subject.write_text("policy: candidate\n", encoding="utf-8")
    _git(repo, "add", "policies/ORG_INVARIANTS.yaml")
    _git(repo, "commit", "-m", "policy source")
    source = _git(repo, "rev-parse", "HEAD")
    digest = hashlib.sha256(subject.read_bytes()).hexdigest()
    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    signature = base64.b64encode(
        private.sign(verify.canonical_admission(digest, source))
    ).decode()
    admission: dict[str, object] = {
        "admitted": True,
        "subject_sha256": digest,
        "subject_commit": source,
        "principal": "owner",
        "signature": signature,
    }
    (policy / "ADMISSION.yaml").write_text("admitted: true\n", encoding="utf-8")
    _git(repo, "add", "policies/ADMISSION.yaml")
    _git(repo, "commit", "-m", "record the admission")
    head = _git(repo, "rev-parse", "HEAD")
    keys = [{"principal": "owner", "public_key": public}]
    return source, head, digest, admission, keys
