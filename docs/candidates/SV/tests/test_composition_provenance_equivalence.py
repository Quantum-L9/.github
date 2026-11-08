"""Positive and negative controls for verify_composition_provenance.

Each negative control corrupts exactly one provenance fact the four declared
``required_provenance`` tokens name. Where an envelope digest would otherwise also fail,
the control re-seals that envelope so the failure is attributable to the intended check.
"""

import copy
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import verify_composition_provenance as vcp

EVIDENCE = vcp.PACK / "evidence" / "reduction-v1"
REVISION = "0b50cf7a09c96986d2fcd46130032224ad7104a0"


def _reseal_composed(run):
    composed = run["composed"]
    composed["composition_digest"] = vcp.envelope_digest(composed, "composition_digest")


class _RunFixture(unittest.TestCase):
    archive = "projection-run1.tar"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        with tarfile.open(EVIDENCE / self.archive) as tar:
            tar.extractall(self._tmp.name, filter="data")
        self.run_dir = Path(self._tmp.name)
        self.run = vcp.load_run(self.run_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def failed(self, run=None, revision=REVISION):
        return vcp.verify(run or self.run, revision)["failed_checks"]


class PositiveControls(_RunFixture):
    def test_rehearsal_run1_passes_every_check(self):
        report = vcp.verify(self.run, REVISION)
        self.assertEqual(report["result"], "PASS", report["failed_checks"])
        self.assertEqual(set(report["required_provenance_tokens"]), set(vcp.REQUIRED_PROVENANCE_TOKENS))
        for token in report["required_provenance_tokens"].values():
            self.assertEqual(token["status"], "pass")

    def test_compiler_result_is_recorded_not_rewritten(self):
        report = vcp.verify(self.run, REVISION)
        self.assertEqual(report["compiler_reported_result"], "unknown")
        self.assertEqual(
            report["compiler_unresolved_criteria"],
            sorted(f"declared_constraint:required_provenance:{t}" for t in vcp.REQUIRED_PROVENANCE_TOKENS),
        )

    def test_five_projection_receipts_pass_at_one_revision(self):
        binding = vcp.verify(self.run, REVISION)["checks"]["receipt_binding"]
        self.assertEqual(binding["projection_receipts_pass"], 5)
        self.assertEqual(binding["authority_revision"], REVISION)

    def test_verifier_does_not_import_the_compiler(self):
        source = Path(vcp.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import l9_semantic_compiler", source)
        self.assertNotIn("from l9_semantic_compiler", source)

    def test_committed_result_matches_a_fresh_run(self):
        committed = json.loads(
            (vcp.PACK / "evidence" / "admission" / "composition-provenance-equivalence.json").read_text(
                encoding="utf-8"
            )
        )
        fresh = vcp.verify(self.run, REVISION)
        self.assertEqual(committed["runs"]["projection-run1.tar"], fresh)


class PositiveControlsRun2(PositiveControls):
    archive = "projection-run2.tar"

    def test_committed_result_matches_a_fresh_run(self):
        committed = json.loads(
            (vcp.PACK / "evidence" / "admission" / "composition-provenance-equivalence.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(committed["runs"]["projection-run2.tar"], vcp.verify(self.run, REVISION))


class NegativeControls(_RunFixture):
    def test_corrupted_component_digest_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["components"][0]["projection_digest"] = "sha256:" + "0" * 64
        _reseal_composed(run)
        failed = self.failed(run)
        self.assertIn("component_digests", failed)
        self.assertIn("receipt_binding", failed)

    def test_corrupted_source_digest_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["components"][1]["source_digest"] = "sha256:" + "1" * 64
        _reseal_composed(run)
        self.assertIn("component_digests", self.failed(run))

    def test_swapped_source_reference_fails(self):
        run = copy.deepcopy(self.run)
        a, b = run["composed"]["components"][0], run["composed"]["components"][1]
        a["source_ref"], b["source_ref"] = b["source_ref"], a["source_ref"]
        _reseal_composed(run)
        self.assertIn("component_refs", self.failed(run))

    def test_foreign_projection_reference_fails(self):
        run = copy.deepcopy(self.run)
        comp = run["composed"]["components"][2]
        comp["projection_ref"] = comp["projection_ref"].replace(vcp.PROJECTION_PROFILE_REF, "l9.projection/other@1")
        _reseal_composed(run)
        self.assertIn("component_refs", self.failed(run))

    def test_changed_composition_profile_digest_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["composition_profile"]["digest"] = "sha256:" + "2" * 64
        _reseal_composed(run)
        failed = self.failed(run)
        self.assertIn("composition_profile_digest", failed)
        self.assertIn("receipt_binding", failed)

    def test_changed_composition_profile_ref_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["composition_profile"]["ref"] = "l9.compose/stage-context@1"
        _reseal_composed(run)
        self.assertIn("composition_profile_ref", self.failed(run))

    def test_edited_candidate_profile_record_fails(self):
        real = vcp.candidate_profiles()
        edited = copy.deepcopy(real[0])
        edited["merge_strategy"]["duplicate_source"] = "merge"
        with mock.patch.object(vcp, "candidate_profiles", return_value=(edited, real[1])):
            self.assertIn("composition_profile_digest", self.failed())

    def test_duplicated_source_fails(self):
        run = copy.deepcopy(self.run)
        comps = run["composed"]["components"]
        comps[4] = copy.deepcopy(comps[3])
        _reseal_composed(run)
        self.assertIn("coverage", self.failed(run))

    def test_missing_source_fails(self):
        run = copy.deepcopy(self.run)
        dropped = run["composed"]["components"].pop()
        run["composed"]["payload"].pop(dropped["source_class"])
        _reseal_composed(run)
        self.assertIn("coverage", self.failed(run))

    def test_payload_drift_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["payload"]["vocabulary"] = {"terms": {}}
        _reseal_composed(run)
        self.assertIn("coverage", self.failed(run))

    def test_unsealed_composed_artifact_fails(self):
        run = copy.deepcopy(self.run)
        run["composed"]["payload"]["vocabulary"] = {"terms": {}}
        self.assertIn("composition_digest", self.failed(run))

    def test_tampered_projection_artifact_fails(self):
        run = copy.deepcopy(self.run)
        run["projections"][0]["payload"] = {"tampered": True}
        self.assertIn("component_refs", self.failed(run))

    def test_wrong_authority_revision_fails(self):
        self.assertIn("receipt_binding", self.failed(revision="0" * 40))

    def test_receipt_input_mismatch_fails(self):
        run = copy.deepcopy(self.run)
        for _, receipt in run["receipts"]:
            if receipt.get("operation") == "composition":
                receipt["inputs"] = receipt["inputs"][:-1]
                receipt["receipt_digest"] = vcp.envelope_digest(receipt, "receipt_digest")
        self.assertIn("receipt_binding", self.failed(run))

    def test_unsealed_receipt_fails(self):
        run = copy.deepcopy(self.run)
        # Forging the composition receipt's UNKNOWN into PASS without resealing must fail.
        for _, receipt in run["receipts"]:
            if receipt.get("operation") == "composition":
                self.assertEqual(receipt["result"], "unknown")
                receipt["result"] = "pass"
        self.assertIn("receipt_binding", self.failed(run))

    def test_missing_projection_receipt_fails(self):
        run = copy.deepcopy(self.run)
        projection = [r for r in run["receipts"] if r[1].get("operation") == "projection"]
        run["receipts"].remove(projection[0])
        self.assertIn("receipt_binding", self.failed(run))


class OwnerDecisionScaffold(unittest.TestCase):
    """The scaffold must never read as a decision, and its option texts must be exact."""

    def setUp(self):
        import yaml

        self.yaml = yaml
        self.doc = yaml.safe_load(
            (vcp.PACK / "evidence" / "admission" / "owner-decision.yaml").read_text(encoding="utf-8")
        )

    def _statements(self, rel):
        data = self.yaml.safe_load((vcp.PACK / rel).read_text(encoding="utf-8"))
        return {r["id"]: r["statement"] for r in data["invariants"]}

    def test_no_authority_reference_or_selection_is_present(self):
        self.assertEqual(self.doc["decision_status"], "PENDING_UNTIL_AUTHORIZED")
        for key in (
            "approved_sv001_statement_ref",
            "authorized_decider_ref",
            "decision_evidence_ref",
            "decision_record_ref",
        ):
            self.assertIsNone(self.doc[key], key)
        self.assertIsNone(self.doc["subject"]["candidate_revision"])
        for decision in self.doc["decisions_required"]:
            self.assertIsNone(decision["selected"], decision["id"])

    def test_sv001_options_are_exact_source_texts(self):
        options = self.doc["decisions_required"][0]["options"]
        donor = self._statements("evidence/reduction-v1/donor/invariants_additions.yaml")
        overlay = self._statements("overlays/invariants_additions.yaml")
        self.assertEqual(options["A-development-pack"]["statement"].strip(), overlay["L9-SV-001"])
        self.assertEqual(
            options["B-non-weakening"]["statement"].strip(),
            f"{donor['L9-SV-001']} {donor['L9-SV-015']}",
        )

    def test_proposed_dispositions_match_the_ledger(self):
        ledger = self.yaml.safe_load(
            (EVIDENCE / "owner-disposition-ledger.yaml").read_text(encoding="utf-8")
        )
        expected = {d["candidate_id"]: d["disposition"] for d in ledger["dispositions"]}
        self.assertEqual(self.doc["proposed_dispositions"], expected)


class UnreadableInputs(unittest.TestCase):
    def test_missing_composed_artifact_is_unresolved_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(vcp.InputError):
                vcp.load_run(Path(tmp))
            self.assertEqual(vcp.main(["--run-dir", tmp]), 2)


if __name__ == "__main__":
    unittest.main()
