#!/usr/bin/env python3
"""Tests for scripts/publish-projection.py, in disposable local git repositories.

Nothing here touches a network remote or the live `projections` branch. The
authority is a throwaway repository whose origin URL names the canonical
owner and whose fetched `origin/main` is a local ref; the "remote" is a local
bare repository.

Pairs are built by `make_pair` below, which follows the producer's documented
conventions (sha256 of raw source bytes; sha256 of canonical JSON for payload,
profile and receipt). It is a test fixture standing in for the producer's
output, not a producer: the publisher must accept it only because every
binding recomputes, and reject it as soon as one does not. A real
l9-semantic-compiler pair is exercised separately (docs/PROJECTION_PUBLICATION.md).

Run from the repository root:  python3 scripts/test-publish-projection.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "publish_projection", HERE / "publish-projection.py"
)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)

PROFILE = "l9.projection/cursor-governance-operating-plane@1"
ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
}

REGISTRY = """schema: l9.canonical-sources/v1
artifact_id: l9.canonical-sources/global@1
canonical: true
authority:
  owner: Quantum-L9/.github
sources:
  - id: l9.source/invariants@1
    path: semantics/invariants.yaml
    canonical: true
    projection_allowed: true
  - id: l9.source/projection-profiles@1
    path: semantics/projection_profiles.yaml
    canonical: true
    projection_allowed: true
"""
CATALOG = """artifact_id: l9.projection-profile-catalog/global@1
canonical: true
source_classes:
  invariants:
    canonical_artifact: invariants.yaml
projection_profiles:
  - id: l9.projection/cursor-governance-operating-plane@1
    sources:
      invariants:
        selectors:
          - $.invariants[?(@.scope=="global")]
      grouped:
        selectors: [$.a, $.b]
"""


def invariants(text: str = "first") -> str:
    return f"invariants:\n  - id: L9-T-001\n    scope: global\n    statement: {text}\n"


def sh(repo: Path, *args: str, data: bytes | None = None) -> str:
    return (
        subprocess.run(
            ["git", "-C", str(repo), *args],
            input=data,
            capture_output=True,
            check=True,
            env=ENV,
        )
        .stdout.decode()
        .strip()
    )


def commit_files(repo: Path, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    sh(repo, "add", "-A")
    sh(repo, "commit", "-q", "-m", message)
    return sh(repo, "rev-parse", "HEAD")


def make_pair(
    out: Path, pins: dict, revision: str, payload=None, version: str = "0.9.3"
) -> Path:
    """Write one producer-shaped pair under out/<class>/<receipt hex>/ (test fixture)."""
    payload = (
        payload if payload is not None else [{"id": "L9-T-001", "scope": "global"}]
    )
    artifact = {
        "schema": pp.ARTIFACT_SCHEMA,
        "source_ref": pins["source_ref"],
        "source_digest": pins["source_digest"],
        "projection_profile_ref": pins["profile_ref"],
        "projection_profile_digest": pins["profile_digest"],
        "payload": payload,
        "projection_digest": pp.digest(payload),
        "generated_by": {"compiler": pp.PRODUCER, "version": version},
    }
    receipt = {
        "schema": pp.RECEIPT_SCHEMA,
        "receipt_identity": "pending",
        "receipt_type": pp.RECEIPT_TYPE,
        "exact_subject_ref": pins["profile_ref"],
        "claim": "fixture",
        "operation": "projection",
        "inputs": [
            {"ref": pins["source_ref"], "digest": pins["source_digest"]},
            {"ref": pp.CATALOG_REF, "digest": pins["catalog_digest"]},
        ],
        "profile": {"ref": pins["profile_ref"], "digest": pins["profile_digest"]},
        "output": {
            "ref": f"{pins['profile_ref']}#{pins['source_class']}",
            "digest": artifact["projection_digest"],
        },
        "governing_coordinates": {
            "authority_owner": "Quantum-L9/.github",
            "authority_revision": revision,
            "authority_revision_basis": "caller_asserted",
            "canonical_source_registry_digest": pins["registry_digest"],
            "source_class": pins["source_class"],
            "selectors": pins["selectors"],
        },
        "result": "pass",
        "verification_basis": {"authenticity": "unsigned"},
        "producer_identity": {"compiler": pp.PRODUCER, "version": version},
        "diagnostics": [],
    }
    receipt["receipt_identity"] = (
        "l9.receipt-instance/" + pp.digest(receipt).split(":", 1)[1]
    )
    receipt["receipt_digest"] = pp.digest(receipt)
    pair = out / pins["source_class"] / receipt["receipt_digest"].split(":", 1)[1]
    pair.mkdir(parents=True, exist_ok=True)
    for name, doc in (("projection.json", artifact), ("receipt.json", receipt)):
        (pair / name).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return pair


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pub1-test-"))
        self.auth = self.tmp / "authority"
        self.auth.mkdir()
        sh(self.auth, "init", "-q", "-b", "main")
        sh(
            self.auth,
            "remote",
            "add",
            "origin",
            "https://github.com/Quantum-L9/.github.git",
        )
        self.rev1 = commit_files(
            self.auth,
            {
                "semantics/canonical_sources.yaml": REGISTRY,
                "semantics/projection_profiles.yaml": CATALOG,
                "semantics/invariants.yaml": invariants("first"),
            },
            "authority 1",
        )
        self.fetch_origin()
        self.store = self.tmp / "store"
        self.store.mkdir()
        sh(self.store, "init", "-q")
        # Activation stand-in: the publication branch exists before any publish.
        empty_tree = sh(
            self.store, "hash-object", "-t", "tree", "-w", "--stdin", data=b""
        )
        self.root_commit = sh(
            self.store, "commit-tree", empty_tree, "-m", "projections root"
        )
        sh(self.store, "update-ref", "refs/heads/projections", self.root_commit)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fetch_origin(self) -> None:
        sh(
            self.auth,
            "update-ref",
            "refs/remotes/origin/main",
            sh(self.auth, "rev-parse", "HEAD"),
        )

    def pins(self, rev: str, cls: str = "invariants") -> dict:
        return pp.compute_pins(
            self.auth, pp.bind_authority(self.auth, rev), PROFILE, cls
        )

    def cli(self, *args: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = pp.main(list(args))
        return code, json.loads(buf.getvalue())

    def publish(
        self, pair: Path, rev: str, *extra: str, repo: Path | None = None
    ) -> tuple[int, dict]:
        return self.cli(
            "publish",
            "--authority-root",
            str(self.auth),
            "--revision",
            rev,
            "--pair-dir",
            str(pair),
            "--repo",
            str(repo or self.store),
            "--compiler-revision",
            "c" * 40,
            *extra,
        )

    def tip(self, repo: Path | None = None) -> str:
        return sh(repo or self.store, "rev-parse", "refs/heads/projections")

    def objects(self) -> str:
        return sh(self.store, "count-objects", "-v")


class PinTests(Fixture):
    def test_pins_come_from_commit_objects_not_the_working_tree(self):
        before = self.pins(self.rev1)
        (self.auth / "semantics/invariants.yaml").write_text(
            invariants("uncommitted edit")
        )
        self.assertEqual(self.pins(self.rev1), before)
        self.assertEqual(
            before["source_digest"], pp.digest_bytes(invariants("first").encode())
        )

    def test_untrusted_pins_are_blocked(self):
        def blocked(rev: str) -> str:
            with self.assertRaises(pp.Outcome) as ctx:
                pp.bind_authority(self.auth, rev)
            self.assertEqual(ctx.exception.status, "BLOCKED")
            return ctx.exception.reason

        for bad in ("", "abc", "g" * 40):
            self.assertEqual(blocked(bad), "REVISION_PIN_ABSENT_OR_MALFORMED")
        local_only = commit_files(
            self.auth, {"README.md": "local\n"}, "local only"
        )  # origin/main not moved
        self.assertEqual(blocked(local_only), "REVISION_PIN_NOT_IN_FETCHED_ORIGIN")
        sh(
            self.auth,
            "remote",
            "set-url",
            "origin",
            "https://github.com/someone/.github-mirror.git",
        )
        self.assertEqual(blocked(self.rev1), "AUTHORITY_ORIGIN_UNVERIFIED")


class VerifyTests(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.p = self.pins(self.rev1)
        self.pair = make_pair(self.tmp / "out", self.p, self.rev1)

    def verify(self, pins=None, revision=None):
        art, rec = pp.read_pair_dir(self.pair)
        return pp.verify_pair(art, rec, pins or self.p, revision or self.rev1)

    def assertRejected(self, reason, **kw):
        with self.assertRaises(pp.Outcome) as ctx:
            self.verify(**kw)
        self.assertEqual(
            (ctx.exception.status, ctx.exception.reason), ("REJECTED", reason)
        )

    def test_valid_pair_verifies_and_is_marked_unauthenticated(self):
        facts = self.verify()
        self.assertEqual(
            facts["producer_authentication"], "unauthenticated_unkeyed_receipt"
        )
        code, out = self.cli(
            "verify",
            "--authority-root",
            str(self.auth),
            "--revision",
            self.rev1,
            "--pair-dir",
            str(self.pair),
        )
        self.assertEqual((code, out["status"]), (0, "VERIFIED"))

    def test_wrong_source_or_profile_pin_is_rejected(self):
        self.assertRejected(
            "SOURCE_DIGEST_MISMATCH",
            pins={**self.p, "source_digest": "sha256:" + "0" * 64},
        )
        self.assertRejected(
            "PROFILE_DIGEST_MISMATCH",
            pins={**self.p, "profile_digest": "sha256:" + "0" * 64},
        )

    def test_tampering_either_file_is_rejected(self):
        for name, edit, reason in (
            (
                "projection.json",
                lambda d: d["payload"][0].update(scope="local"),
                "PROJECTION_DIGEST_MISMATCH",
            ),
            (
                "receipt.json",
                lambda d: d.update(claim="edited after emission"),
                "RECEIPT_DIGEST_MISMATCH",
            ),
        ):
            original = (self.pair / name).read_text()
            doc = json.loads(original)
            edit(doc)
            (self.pair / name).write_text(json.dumps(doc))
            self.assertRejected(reason)
            (self.pair / name).write_text(original)

    def test_receipt_asserting_another_revision_is_rejected(self):
        self.assertRejected("RECEIPT_REVISION_MISMATCH", revision="d" * 40)


class PublishTests(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.pair = make_pair(self.tmp / "out", self.pins(self.rev1), self.rev1)

    def test_dry_run_is_the_default_and_writes_nothing(self):
        before = (self.tip(), self.objects())
        code, out = self.publish(self.pair, self.rev1)
        self.assertEqual((code, out["status"], out["applied"]), (0, "PLANNED", False))
        self.assertEqual((self.tip(), self.objects()), before)

    def test_apply_publishes_pair_and_index_in_one_commit(self):
        code, out = self.publish(self.pair, self.rev1, "--apply")
        self.assertEqual((code, out["status"]), (0, "PUBLISHED"))
        commit = self.tip()
        self.assertEqual(sh(self.store, "rev-parse", f"{commit}^"), self.root_commit)
        index = json.loads(sh(self.store, "show", f"{commit}:index.json"))
        current = index["entries"][f"{PROFILE}#invariants"]["current"]
        for name in (
            "projection.json",
            "receipt.json",
        ):  # index and pair live in the same tree
            data = (self.pair / name).read_bytes()
            self.assertEqual(
                sh(self.store, "show", f"{commit}:{current['pair']}/{name}").encode()
                + b"\n",
                data,
            )
            self.assertEqual(current["files"][name], pp.digest_bytes(data))
        self.assertEqual(current["authority_revision"], self.rev1)
        self.assertEqual(index["previous_publication"], self.root_commit)

    def test_interrupted_stage_leaves_ref_and_index_unchanged(self):
        real = pp.advance
        pp.advance = lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt())
        try:
            with self.assertRaises(KeyboardInterrupt):
                self.publish(self.pair, self.rev1, "--apply")
        finally:
            pp.advance = real
        self.assertEqual(self.tip(), self.root_commit)
        self.assertIsNone(pp.blob_at(self.store, self.tip(), "index.json"))

    def test_identical_replay_is_noop_and_different_bytes_at_a_path_are_refused(self):
        self.publish(self.pair, self.rev1, "--apply")
        published = self.tip()
        code, out = self.publish(self.pair, self.rev1, "--apply")
        self.assertEqual(
            (code, out["status"], self.tip()), (0, "NOOP_IDENTICAL", published)
        )
        moved = self.tmp / "moved"
        sh(
            self.store, "update-ref", "-d", "refs/heads/projections"
        )  # drop the index, keep the pair path
        base = json.loads(sh(self.store, "show", f"{published}:index.json"))["entries"][
            f"{PROFILE}#invariants"
        ]["current"]
        tree = sh(
            self.store,
            "mktree",
            data=f"040000 tree {sh(self.store, 'rev-parse', published + ':pairs')}\tpairs\n".encode(),
        )
        sh(
            self.store,
            "update-ref",
            "refs/heads/projections",
            sh(self.store, "commit-tree", tree, "-m", "pairs only"),
        )
        shutil.copytree(self.pair, moved / self.pair.name)
        (moved / self.pair.name / "projection.json").write_text(
            (self.pair / "projection.json").read_text() + " "
        )
        code, out = self.publish(moved / self.pair.name, self.rev1, "--apply")
        self.assertEqual((code, out["reason"]), (1, "IMMUTABLE_PATH_COLLISION"))
        self.assertIn(base["pair"], out["path"])

    def test_material_change_publishes_successor_and_retains_prior_pair(self):
        self.publish(self.pair, self.rev1, "--apply")
        rev2 = commit_files(
            self.auth,
            {"semantics/invariants.yaml": invariants("second")},
            "material change",
        )
        self.fetch_origin()
        pair2 = make_pair(self.tmp / "out", self.pins(rev2), rev2)
        code, out = self.publish(pair2, rev2, "--apply")
        self.assertEqual((code, out["status"]), (0, "PUBLISHED"))
        entry = json.loads(sh(self.store, "show", f"{self.tip()}:index.json"))[
            "entries"
        ][f"{PROFILE}#invariants"]
        self.assertEqual(entry["current"]["authority_revision"], rev2)
        self.assertEqual(entry["history"][0]["authority_revision"], self.rev1)
        self.assertIsNotNone(
            pp.blob_at(
                self.store, self.tip(), f"{entry['history'][0]['pair']}/receipt.json"
            )
        )

    def test_unrelated_revision_does_not_republish(self):
        self.publish(self.pair, self.rev1, "--apply")
        first = self.tip()
        rev2 = commit_files(self.auth, {"README.md": "unrelated\n"}, "unrelated change")
        self.fetch_origin()
        pair2 = make_pair(self.tmp / "out", self.pins(rev2), rev2)
        code, out = self.publish(pair2, rev2, "--apply")
        self.assertEqual(
            (code, out["status"], self.tip()), (0, "NOOP_UNCHANGED_SEMANTICS", first)
        )
        code, out = self.cli(
            "check",
            "--authority-root",
            str(self.auth),
            "--revision",
            rev2,
            "--repo",
            str(self.store),
            "--commit",
            first,
        )
        self.assertEqual((code, out["status"]), (0, "CURRENT"))

    def test_stale_pin_is_not_promoted_when_canonical_moved_materially(self):
        rev2 = commit_files(
            self.auth,
            {"semantics/invariants.yaml": invariants("second")},
            "material change",
        )
        self.fetch_origin()
        code, out = self.publish(self.pair, self.rev1, "--apply")
        self.assertEqual(
            (code, out["reason"]), (4, "MATERIAL_INPUT_CHANGED_ON_CANONICAL")
        )
        self.assertEqual(self.tip(), self.root_commit)
        self.assertNotEqual(rev2, self.rev1)

    def test_older_material_revision_cannot_roll_back_the_index(self):
        rev2 = commit_files(
            self.auth,
            {"semantics/invariants.yaml": invariants("second")},
            "material change",
        )
        rev3 = commit_files(
            self.auth,
            {"semantics/invariants.yaml": invariants("first")},
            "revert to first bytes",
        )
        self.fetch_origin()
        # rev3 restores the first bytes and is published as current.
        pair3 = make_pair(self.tmp / "out", self.pins(rev3), rev3)
        self.assertEqual(self.publish(pair3, rev3, "--apply")[1]["status"], "PUBLISHED")
        # The older material revision rev2 must not replace it, even past the freshness check.
        pins2 = self.pins(rev2)
        pair2 = make_pair(self.tmp / "out", pins2, rev2)
        facts = pp.verify_pair(*pp.read_pair_dir(pair2), pins2, rev2)
        pair2_bytes, tip = pp.read_pair_dir(pair2), self.tip()
        with self.assertRaises(pp.Outcome) as ctx:
            pp.plan_publication(
                self.store,
                tip,
                self.auth,
                pins2,
                facts,
                pair2_bytes,
                "c" * 40,
            )
        self.assertEqual(ctx.exception.reason, "ROLLBACK_REFUSED")

    def test_unsafe_or_unsupported_inputs_never_publish_or_reach_git_as_options(self):
        code, out = self.publish(
            self.pair, self.rev1, "--apply", "--source-class", "grouped"
        )
        self.assertEqual(
            (code, out["reason"]), (1, "UNSUPPORTED_SOURCE_CLASS")
        )  # multi-selector: no payload shape
        code, out = self.cli(
            "publish",
            "--authority-root",
            str(self.auth),
            "--revision",
            self.rev1,
            "--pair-dir",
            str(self.pair),
            "--repo",
            str(self.store),
            "--apply",
        )
        self.assertEqual((code, out["reason"]), (3, "COMPILER_REVISION_ABSENT"))
        marker = self.tmp / "INJECTED"
        injected = f"--upload-pack=touch {marker};false"
        for extra, reason in (
            (("--remote", injected), "UNSAFE_OR_UNKNOWN_REMOTE"),
            (
                ("--remote", "https://github.com/Quantum-L9/.github"),
                "UNSAFE_OR_UNKNOWN_REMOTE",
            ),
            (("--branch", injected), "UNSAFE_BRANCH_NAME"),
            (("--canonical-ref", injected), "UNSAFE_REF_NAME"),
        ):
            code, out = self.publish(self.pair, self.rev1, "--apply", *extra)
            self.assertEqual((code, out["reason"]), (1, reason))
        code, out = self.cli(
            "check",
            "--authority-root",
            str(self.auth),
            "--revision",
            self.rev1,
            "--repo",
            str(self.store),
            "--commit",
            injected,
        )
        self.assertEqual((code, out["reason"]), (1, "PUBLICATION_COMMIT_MALFORMED"))
        self.assertFalse(marker.exists(), "an option-like CLI value reached git")
        self.assertEqual(self.tip(), self.root_commit)


class RaceAndRemoteTests(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.pair = make_pair(self.tmp / "out", self.pins(self.rev1), self.rev1)

    def test_two_publishers_from_one_base_one_wins_loser_never_forces(self):
        p = self.pins(self.rev1)
        facts = pp.verify_pair(*pp.read_pair_dir(self.pair), p, self.rev1)
        base = self.tip()
        plan = pp.plan_publication(
            self.store, base, self.auth, p, facts, pp.read_pair_dir(self.pair), "c" * 40
        )
        winner = pp.build_commit(self.store, base, plan["files"], "winner")
        loser = pp.build_commit(self.store, base, plan["files"], "loser")
        pp.advance(self.store, "projections", base, winner, None)
        with self.assertRaises(pp.Outcome) as ctx:
            pp.advance(self.store, "projections", base, loser, None)
        self.assertEqual((ctx.exception.status, self.tip()), ("CONFLICT", winner))
        # Re-evaluation from the new tip finds the work already published.
        self.assertEqual(
            self.publish(self.pair, self.rev1, "--apply")[1]["status"], "NOOP_IDENTICAL"
        )

    def remote_store(self) -> Path:
        bare = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, env=ENV)
        sh(self.store, "remote", "add", "pub", str(bare))
        return bare

    def test_remote_absent_branch_blocks_then_fast_forward_and_moved_remote_conflict(
        self,
    ):
        bare = self.remote_store()
        code, out = self.publish(self.pair, self.rev1, "--apply", "--remote", "pub")
        self.assertEqual(
            (code, out["reason"]), (3, "TARGET_REF_ABSENT")
        )  # the publisher never creates it
        self.assertEqual(sh(bare, "for-each-ref"), "")
        sh(
            self.store,
            "push",
            "-q",
            "pub",
            "refs/heads/projections:refs/heads/projections",
        )
        code, out = self.publish(self.pair, self.rev1, "--apply", "--remote", "pub")
        self.assertEqual((code, out["status"]), (0, "PUBLISHED"))
        self.assertEqual(sh(bare, "rev-parse", "refs/heads/projections"), out["commit"])
        # Someone else advances the remote; our next attempt from a stale base must lose.
        other = sh(
            self.store,
            "commit-tree",
            sh(self.store, "rev-parse", f"{out['commit']}^{{tree}}"),
            "-p",
            out["commit"],
            "-m",
            "other",
        )
        sh(self.store, "push", "-q", "pub", f"{other}:refs/heads/projections")
        with self.assertRaises(pp.Outcome) as ctx:
            pp.advance(self.store, "projections", out["commit"], other, "pub")
        self.assertEqual(ctx.exception.status, "CONFLICT")
        self.assertEqual(sh(bare, "rev-parse", "refs/heads/projections"), other)

    def test_publisher_source_contains_no_force_path(self):
        source = (HERE / "publish-projection.py").read_text()
        for needle in (
            '"--force"',
            "'--force'",
            '"-f"',
            "force-with-lease",
            '"+',
            "reset --hard",
        ):
            self.assertNotIn(needle, source)


class CheckTests(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.pair = make_pair(self.tmp / "out", self.pins(self.rev1), self.rev1)
        self.publish(self.pair, self.rev1, "--apply")
        self.published = self.tip()

    def check(self, rev: str, commit: str) -> tuple[int, dict]:
        return self.cli(
            "check",
            "--authority-root",
            str(self.auth),
            "--revision",
            rev,
            "--repo",
            str(self.store),
            "--commit",
            commit,
        )

    def test_current_from_one_fixed_commit(self):
        code, out = self.check(self.rev1, self.published)
        self.assertEqual(
            (code, out["status"], out["commit"]), (0, "CURRENT", self.published)
        )

    def test_material_change_reports_stale(self):
        rev2 = commit_files(
            self.auth,
            {"semantics/invariants.yaml": invariants("second")},
            "material change",
        )
        self.fetch_origin()
        code, out = self.check(rev2, self.published)
        self.assertEqual((code, out["status"]), (4, "STALE"))

    def test_tampered_pair_inside_a_commit_is_rejected(self):
        current = json.loads(sh(self.store, "show", f"{self.published}:index.json"))[
            "entries"
        ][f"{PROFILE}#invariants"]["current"]
        files = {f"{current['pair']}/projection.json": b'{"tampered": true}\n'}
        bad = pp.build_commit(self.store, self.published, files, "tamper")
        code, out = self.check(self.rev1, bad)
        self.assertEqual((code, out["reason"]), (1, "INDEXED_FILE_HASH_MISMATCH"))

    def test_index_revision_is_not_a_trust_input(self):
        # A pin the consumer did not independently obtain is refused before the index is read.
        code, out = self.check("e" * 40, self.published)
        self.assertEqual((code, out["status"]), (3, "BLOCKED"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
