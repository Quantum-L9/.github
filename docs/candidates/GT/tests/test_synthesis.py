"""Hermetic checks on the committed compiler-generated GT candidate schemas.

These do not re-run the compiler (``tools/synthesize_candidate_schemas.py
--check`` does that). They prove the committed outputs are internally bound:
extracted schemas equal the compiler candidate, digests verify under the
compiler's declared basis, the run receipt records success and candidate-only
status, the governance documents are candidates, and the rehearsal is GT core on the
admitted SV foundation pinned by the GT binding.
"""

import hashlib
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "synthesis" / "generated"
GOV = ROOT / "synthesis" / "governance"
BINDING = json.loads((ROOT / "evidence" / "sv_alignment_binding.json").read_text())
PROJECTION_ID = "l9.projection.strategic-planner-interaction/v1"
COMPOSITION_ID = "l9.composed-projection.strategic-planner-interaction/v1"
FILES = {
    "projection_schema": "strategic_planner_interaction_projection.candidate.schema.json",
    "composition_schema": "strategic_planner_interaction_composition.candidate.schema.json",
}


def canonical_digest(value):
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(data + b"\n").hexdigest()


def load(name):
    return json.loads((GEN / name).read_text(encoding="utf-8"))


class CandidateBinding(unittest.TestCase):
    def setUp(self):
        self.candidate = load("candidate.json")
        self.receipt = load("run-receipt.json")

    def test_digest_basis_is_the_compilers(self):
        self.assertEqual(
            self.candidate["output_digests"]["digest_basis"],
            "canonical_json_utf8_sorted_keys_with_newline",
        )

    def test_extracted_schemas_equal_candidate_and_verify(self):
        for key, name in FILES.items():
            extracted = load(name)
            self.assertEqual(extracted, self.candidate[key], name)
            self.assertEqual(
                canonical_digest(extracted), self.candidate["output_digests"][key], name
            )
            self.assertEqual(
                self.receipt["outputs"][key]["sha256"],
                self.candidate["output_digests"][key],
            )
        self.assertEqual(
            canonical_digest(self.candidate["provenance"]),
            self.candidate["output_digests"]["provenance"],
        )

    def test_tampered_schema_does_not_verify(self):
        extracted = load(FILES["projection_schema"])
        extracted["schema_id"] = "l9.projection.strategic-planner-value/v1"
        self.assertNotEqual(
            canonical_digest(extracted),
            self.candidate["output_digests"]["projection_schema"],
        )

    def test_schema_identities_are_gt_outputs(self):
        self.assertEqual(
            self.candidate["projection_schema"]["schema_id"], PROJECTION_ID
        )
        self.assertEqual(
            self.candidate["composition_schema"]["schema_id"], COMPOSITION_ID
        )

    def test_candidate_status_never_claims_admission(self):
        for doc in (
            self.candidate,
            self.candidate["projection_schema"],
            self.candidate["composition_schema"],
        ):
            self.assertIs(doc["canonical"], False)
            self.assertEqual(doc["admission"], "not_granted")
        self.assertEqual(self.receipt["status"], "candidate_not_admitted")
        self.assertEqual(self.receipt["owner_review"], "not_performed")
        self.assertEqual(self.receipt["admission"], "not_granted")
        self.assertIs(self.receipt["authority_rehearsal_pushed"], False)


class RunReceipt(unittest.TestCase):
    def setUp(self):
        self.receipt = load("run-receipt.json")

    def test_synthesis_succeeded_twice_identically(self):
        self.assertEqual(self.receipt["schema_synthesize_exit_codes"], [0, 0])
        self.assertIs(self.receipt["deterministic_replay"], True)
        self.assertEqual(self.receipt["schema_candidate_check_exit_code"], 0)
        check = self.receipt["schema_candidate_check"]
        self.assertEqual(check["status"], "candidate_digests_consistent")
        self.assertEqual(check["authenticity"], "not_established")

    def test_compiler_and_rehearsal_are_pinned(self):
        self.assertRegex(self.receipt["compiler"]["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            self.receipt["authority_base_sha"], BINDING["canonical_target"]
        )
        self.assertRegex(
            self.receipt["authority_rehearsal_revision"], r"^[0-9a-f]{40}$"
        )
        self.assertRegex(
            self.receipt["candidate_json_compiler_bytes_sha256"],
            r"^sha256:[0-9a-f]{64}$",
        )

    def test_rehearsal_is_gt_core_on_the_admitted_sv_foundation(self):
        sv = self.receipt["sv_admitted"]
        self.assertEqual(sv["release"], BINDING["sv_admitted"]["release"])
        self.assertEqual(
            sv["admission_merge_commit"],
            BINDING["sv_admitted"]["admission_merge_commit"],
        )
        self.assertEqual(
            self.receipt["authority_semantics_tree_before_gt"],
            BINDING["canonical_target_semantics_tree"],
        )
        self.assertEqual(
            self.receipt["compiler"]["revision"],
            BINDING["sv_admitted"]["compiler_pinned_by_admission"],
        )
        self.assertNotIn("sv_pack", self.receipt)

    def test_request_pins_gt_profiles_and_sources(self):
        request = load("request.json")
        self.assertEqual(request["mode"], "candidate")
        self.assertEqual(
            request["projection_profile"]["ref"],
            "l9.projection/strategic-planner-interaction@1",
        )
        self.assertEqual(
            request["composition_profile"]["ref"],
            "l9.compose/strategic-planner-interaction@1",
        )
        self.assertEqual(
            request["source_order"], ["vocabulary", "invariants", "contracts"]
        )
        self.assertEqual(
            request["authority"]["revision"],
            self.receipt["authority_rehearsal_revision"],
        )
        self.assertTrue(request["authority"]["root"].startswith("<"))
        self.assertTrue(request["governance"]["root"].startswith("<"))


class GovernanceCandidates(unittest.TestCase):
    def test_every_governance_document_is_a_candidate(self):
        docs = sorted(GOV.rglob("*.yaml"))
        self.assertEqual(len(docs), 6)
        for path in docs:
            doc = yaml.safe_load(path.read_text())
            self.assertEqual(doc["approval_status"], "candidate", path.name)
            self.assertIs(doc["canonical"], False, path.name)
            self.assertEqual(doc["admission"], "not_granted", path.name)

    def test_grammars_cover_exactly_the_gt_source_classes_without_sv_records(self):
        grammars = {
            p.stem: yaml.safe_load(p.read_text())
            for p in (GOV / "grammars").glob("*.yaml")
        }
        self.assertEqual(set(grammars), {"vocabulary", "invariants", "contracts"})
        sv_terms = set(BINDING["sv_vocabulary_terms"])
        vocab_fields = set(
            grammars["vocabulary"]["grammar"]["fields"]["terms"]["fields"]
        )
        self.assertFalse(vocab_fields & sv_terms)
        for name, doc in grammars.items():
            text = json.dumps(doc["applies_to_selectors"])
            for sv_id in BINDING["sv_new_invariants"] + [BINDING["sv_contract"]]:
                self.assertNotIn(sv_id, text, name)

    def test_ledger_never_relaxes_into_new_constraints(self):
        ledger = load("constraint-ledger.json")
        for entry in ledger["entries"]:
            if entry["action"] == "structural_fill":
                self.assertIn(entry["constraint"], ("type", "items"), entry)
        for cls, counts in ledger["summary"].items():
            self.assertEqual(
                sum(counts.values()),
                sum(1 for e in ledger["entries"] if e["source_class"] == cls),
                cls,
            )


if __name__ == "__main__":
    unittest.main()
