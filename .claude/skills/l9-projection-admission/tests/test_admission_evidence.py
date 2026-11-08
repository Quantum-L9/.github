"""Tests for verify_admission_evidence.py: forged or detached admission evidence is rejected."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_admission_closure as cac
import verify_admission_evidence as vae
from test_check_admission_closure import (
    ADMITTED,
    ALL_NAMES,
    LEDGERS,
    MAKEFILE,
    SUBJECT,
    VALIDATOR,
    Repo,
    _Fixture,
)


def fresh(root: Path, *, names=ALL_NAMES, **adr) -> Repo:
    """v1.0.0 admitted in one commit, with ADR-001 shaped by `adr` keyword overrides."""
    root.mkdir(parents=True, exist_ok=True)
    repo = Repo(root)
    repo.git("init", "-q")
    repo.git("config", "user.email", "fixture@example.invalid")
    repo.git("config", "user.name", "fixture")
    for name, text in LEDGERS.items():
        repo.write(f"semantics/{name}", text)
    repo.write("scripts/validate-semantics.py", VALIDATOR)
    repo.write("scripts/exit_code", "0")
    repo.write("Makefile", MAKEFILE)
    repo.admit("v1.0.0", 1, names, **adr)
    repo.commit("admit v1.0.0")
    return repo


class ReleaseAdmission(_Fixture):
    def proof(self, repo=None):
        repo = repo or self.repo
        return vae.release_admission(
            repo.root, cac.Tree(repo.root, "origin/main"), "v1.0.0"
        )

    def forged(self, **adr):
        return self.proof(fresh(self.tmp / "forged", **adr))

    def assert_gap(self, proof, text):
        self.assertEqual(proof["status"], "fail")
        self.assertIn(text, "\n".join(proof["gaps"]))

    def test_genuine_admission_binds_every_field(self):
        proof = self.proof()
        self.assertEqual(proof["status"], "pass", proof["gaps"])
        self.assertEqual(proof["schema"], vae.EVIDENCE_SCHEMA)
        self.assertEqual(proof["admission_release"], "v1.0.0")
        self.assertEqual(proof["admission_commit"], self.repo.git("rev-parse", "HEAD"))
        self.assertEqual(
            proof["admitted_semantics_tree"],
            self.repo.git("rev-parse", "HEAD:semantics"),
        )
        self.assertEqual(proof["target_authority_class"], "canonical_global_semantics")
        self.assertEqual(
            proof["authorized_decision_ref"],
            ["Quantum-L9/.github#1", "session_fixture000001"],
        )

    def test_adr_binding_another_tree_is_rejected(self):
        self.assert_gap(
            self.forged(tree="0" * 40), "is not the admission commit's tree"
        )

    def test_adr_binding_no_tree_is_rejected(self):
        self.assert_gap(self.forged(tree="none"), "binds no approved semantics/ tree")

    def test_adr_not_naming_the_release_is_rejected(self):
        self.assert_gap(self.forged(release_row=False), "does not name release v1.0.0")

    def test_adr_without_target_class_is_rejected(self):
        self.assert_gap(self.forged(target_row=False), "target authority class")

    def test_adr_without_decision_reference_is_rejected(self):
        self.assert_gap(
            self.forged(decision_ref=False), "carries no decision reference"
        )

    def test_adr_missing_from_the_index_is_rejected(self):
        self.assert_gap(self.forged(index=False), "not listed in docs/adr/README.md")

    def test_adr_added_after_the_admission_commit_is_rejected(self):
        root = self.tmp / "late"
        root.mkdir()
        repo = Repo(root)
        repo.git("init", "-q")
        repo.git("config", "user.email", "f@example.invalid")
        repo.git("config", "user.name", "f")
        for name, text in LEDGERS.items():
            repo.write(f"semantics/{name}", text)
        repo.write("docs/adr/README.md", "# ADRs\n")
        repo.release("v1.0.0", ADMITTED.format(adr="ADR-001"))
        repo.commit("flip status with no decision record")
        repo.adr(1, "v1.0.0", ALL_NAMES)
        repo.commit("add the ADR afterwards")
        self.assert_gap(self.proof(repo), "existed at the admission commit")

    def test_adr_edited_after_admission_is_rejected(self):
        path = "docs/adr/ADR-001-admit-v1.0.0.md"
        self.repo.write(
            path, self.repo.read(path) + "\nAlso admits l9.projection/sneaky@1.\n"
        )
        self.repo.commit("edit the decision afterwards")
        self.assert_gap(
            self.proof(), "edited or removed on main after the admission commit"
        )

    def test_release_record_edited_after_admission_is_rejected(self):
        base = "docs/semantic-foundation/v1.0.0/RELEASE_VALIDATION.md"
        self.repo.write(base, "rewritten\n")
        self.repo.commit("edit the admitted release")
        self.assert_gap(self.proof(), "release record edited after admission")

    def test_named_candidate_without_the_approved_tree_is_rejected(self):
        first = self.repo.git("rev-parse", "HEAD")
        self.repo.write("semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "z: 1\n")
        self.repo.commit("a different tree")
        tree = self.repo.semantics_tree()
        name = self.repo.adr(
            2, "v1.1.0", ["l9.source/x-model@1"], tree=f"{tree}` (candidate `{first}`)"
        )
        self.repo.release("v1.1.0", ADMITTED.format(adr="ADR-002"))
        self.repo.commit("admit v1.1.0 naming a stale candidate")
        proof = vae.release_admission(
            self.repo.root, cac.Tree(self.repo.root, "origin/main"), "v1.1.0"
        )
        self.assertEqual(proof["adr"], name)
        self.assert_gap(proof, "does not carry the approved semantics/ tree")


class DecisionScope(_Fixture):
    def scope(self, repo, version="v1.0.0", subject=SUBJECT):
        main = cac.Tree(repo.root, "origin/main")
        proof = vae.release_admission(repo.root, main, version)
        self.assertEqual(proof["status"], "pass", proof["gaps"])
        loaded = cac.load_subject(self._subject(subject))
        records = cac.registration(
            cac.Tree(repo.root, proof["admission_commit"]), loaded
        )["records"]
        return vae.decision_scope(repo.root, main, version, proof, loaded, records)

    def test_adr_naming_every_introduced_identity_covers_the_subject(self):
        scope = self.scope(self.repo)
        self.assertEqual(scope["status"], "pass", scope["gaps"])
        self.assertIn("projection profile:l9.projection/x@1", scope["introduced"])

    def test_adr_not_naming_the_subject_does_not_establish_admission(self):
        repo = fresh(self.tmp / "silent", names=["L9-X-001"])
        scope = self.scope(repo)
        self.assertEqual(scope["status"], "fail")
        self.assertIn(
            "does not name projection profile:l9.projection/x@1",
            "\n".join(scope["gaps"]),
        )

    def test_pair_and_schemas_are_covered_through_the_projection_profile(self):
        names = [n for n in ALL_NAMES if n != "l9.compose/x@1"]
        scope = self.scope(fresh(self.tmp / "pair", names=names))
        self.assertEqual(scope["status"], "pass", scope["gaps"])

    def test_only_what_the_release_introduced_must_be_named(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("purpose: x", "purpose: revised"),
        )
        self.repo.admit("v1.1.0", 2, ["l9.contract/x@1"])
        self.repo.commit("admit v1.1.0")
        scope = self.scope(self.repo, "v1.1.0")
        self.assertEqual(scope["introduced"], ["contract:l9.contract/x@1"])
        self.assertEqual(scope["predecessor_release"], "v1.0.0")
        self.assertEqual(scope["status"], "pass", scope["gaps"])

    def test_name_matching_respects_identifier_boundaries(self):
        self.assertTrue(vae._names("admits `L9-X-001`.", "L9-X-001"))
        self.assertFalse(vae._names("admits L9-X-0012", "L9-X-001"))
        self.assertFalse(vae._names("admits l9.projection/x@12", "l9.projection/x@1"))


class CommandLine(_Fixture):
    def run_main(self, *extra, subject=SUBJECT):
        return vae.main(
            [
                "--checkout",
                str(self.repo.root),
                "--subject",
                str(self._subject(subject)),
                *extra,
            ]
        )

    def test_established(self):
        self.assertEqual(self.run_main("--release", "v1.0.0"), 0)

    def test_unknown_release_is_unresolved(self):
        self.assertEqual(self.run_main("--release", "v9.9.9"), 2)

    def test_subject_not_registered_at_admission_is_not_established(self):
        subject = {"schema": cac.SUBJECT_SCHEMA, "invariants": ["L9-X-404"]}
        self.assertEqual(self.run_main("--release", "v1.0.0", subject=subject), 1)


class ProducerChecks(unittest.TestCase):
    def test_strict_const_distinguishes_booleans_from_numbers(self):
        schema = {
            "type": "object",
            "properties": {"flag": {"const": True}, "level": {"enum": [0, 1]}},
        }
        self.assertEqual(
            vae.strict_const_violations({"flag": True, "level": 1}, schema), []
        )
        self.assertTrue(vae.strict_const_violations({"flag": 1}, schema))
        self.assertTrue(vae.strict_const_violations({"level": True}, schema))
        self.assertTrue(
            vae.strict_const_violations(
                [{"flag": 1}], {"type": "array", "items": schema}
            )
        )

    def test_compare_runs(self):
        import tempfile

        root = Path(tempfile.mkdtemp())
        for run, text in (("a", "x"), ("b", "x")):
            (root / run / "receipts").mkdir(parents=True)
            (root / run / "receipts" / "r.json").write_text(text)
            (root / run / "requests").mkdir()
            (root / run / "requests" / "q.yaml").write_text(run)  # names its own root
        self.assertEqual(vae.compare_runs(root / "a", root / "b")["status"], "pass")
        (root / "b" / "receipts" / "r.json").write_text("y")
        self.assertEqual(
            vae.compare_runs(root / "a", root / "b")["differing"], ["receipts/r.json"]
        )
        empty = root / "empty"
        empty.mkdir()
        self.assertEqual(vae.compare_runs(empty, empty)["status"], "fail")

    def test_receipt_must_state_an_empty_unresolved_list_and_complete_coverage(self):
        base = {
            "result": "pass",
            "output": {"ref": "o", "digest": "d"},
            "profile": {"ref": "p", "digest": "e"},
            "inputs": [{"ref": "i"}],
            "verification_basis": {
                "coverage": "complete",
                "unresolved_criteria": [],
                "criteria": {"c": {"status": "pass"}},
            },
        }
        kwargs = {
            "output": base["output"],
            "profile": base["profile"],
            "inputs": base["inputs"],
        }

        def gaps(receipt):
            receipt["receipt_digest"] = vae._self_digest(receipt, "receipt_digest")
            return vae.check_receipt(receipt, "r", **kwargs)

        self.assertEqual(gaps(json.loads(json.dumps(base))), [])
        for mutate in (
            lambda r: r["verification_basis"].pop("unresolved_criteria"),
            lambda r: r["verification_basis"].__setitem__("unresolved_criteria", ["x"]),
            lambda r: r["verification_basis"].__setitem__("coverage", "incomplete"),
            lambda r: r["verification_basis"]["criteria"].__setitem__(
                "c", {"status": "unresolved"}
            ),
            lambda r: r.__setitem__("inputs", [{"ref": "other"}]),
            lambda r: r.__setitem__("result", "unknown"),
        ):
            receipt = json.loads(json.dumps(base))
            mutate(receipt)
            self.assertTrue(gaps(receipt), receipt)


if __name__ == "__main__":
    unittest.main()
