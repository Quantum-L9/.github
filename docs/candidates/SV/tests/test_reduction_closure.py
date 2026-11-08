"""Two-invariant reduction: exact closure, lossless lineage, and negative controls.

Expected values come from the disposition ledger; actual values are parsed from
the candidate sources. Each negative test mutates a parsed copy and must be
caught by ``closure_violations`` (or the applier / provenance gates), proving the
obligation is enforced rather than merely asserted.
"""

import copy
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import yaml
from reduction_closure import (
    DONOR,
    LINEAGE,
    ROOT,
    closure_violations,
    donor_statements,
    expected,
    load_sources,
    mutated,
    producer_receipt_problems,
    read_yaml,
)

REDUCTION_EVIDENCE = ROOT / "evidence" / "reduction-v1"


class ExactClosure(unittest.TestCase):
    def setUp(self):
        self.src = load_sources()
        self.exp = expected()

    def test_reduced_candidate_is_closed(self):
        self.assertEqual(closure_violations(self.src), [])

    def test_exact_identity_sets_from_parsed_sources(self):
        exp = self.exp
        self.assertEqual(exp["new_ids"], {"L9-SV-001", "L9-SV-002"})
        self.assertEqual(len(exp["existing_ids"]), 10)
        self.assertEqual(exp["selected_ids"], exp["new_ids"] | exp["existing_ids"])
        self.assertEqual({r["id"] for r in self.src["invariants"]}, exp["new_ids"])
        self.assertEqual(
            set(self.src["model"][LINEAGE]), {f"L9-SV-{n:03d}" for n in range(15, 21)}
        )
        self.assertEqual(
            set(self.src["model"]["retained_former_candidate_semantics"]),
            {f"L9-SV-{n:03d}" for n in range(3, 15)},
        )

    def test_existing_governing_ids_resolve_at_beneficiary_baseline(self):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                "020a94bea86e7c5c5e4107da7014ec259508f397:semantics/invariants.yaml",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        text = result.stdout if result.returncode == 0 else ""
        if not text:
            self.fail(
                "beneficiary baseline invariants.yaml unavailable; cannot resolve existing IDs (Unknown, not PASS)"
            )
        ids = {r["id"] for r in yaml.safe_load(text)["invariants"]}
        self.assertTrue(
            self.exp["existing_ids"] <= ids, sorted(self.exp["existing_ids"] - ids)
        )
        self.assertFalse(self.exp["new_ids"] & ids)

    def test_reduction_tool_reproduces_committed_files(self):
        tool = ROOT / "tools" / "reduce_to_two_invariants.py"
        result = subprocess.run(
            [sys.executable, str(tool), "--check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


class LosslessAgainstDonor(unittest.TestCase):
    """The reduction changes provenance only; obligations are byte-for-byte preserved."""

    def setUp(self):
        self.src = load_sources()

    def test_six_relocated_meanings_are_verbatim_donor_statements(self):
        statements = donor_statements()
        for cid, rec in self.src["model"][LINEAGE].items():
            self.assertEqual(rec["meaning"], statements[cid], cid)
            self.assertEqual(
                rec["authority_status"], "not_admitted_as_independent_invariant"
            )

    def test_sv001_is_the_owner_approved_verbatim_merge(self):
        """D1 Option B: donor SV-001 then donor SV-015, verbatim, with nothing narrowed."""
        led = yaml.safe_load(
            (REDUCTION_EVIDENCE / "owner-disposition-ledger.yaml").read_text()
        )
        rows = {r["candidate_id"]: r for r in led["dispositions"]}
        statements = donor_statements()
        approved = f"{statements['L9-SV-001']} {statements['L9-SV-015']}"
        overlay = {r["id"]: r["statement"] for r in self.src["invariants"]}
        self.assertEqual(overlay["L9-SV-001"], approved)
        self.assertEqual(
            rows["L9-SV-001"]["statement_change"],
            "VERBATIM_CONCATENATION_OF_DONOR_SV001_AND_SV015_OWNER_APPROVED_D1",
        )
        self.assertEqual(
            rows["L9-SV-015"]["meaning_preservation"],
            "MERGE_VERBATIM_OWNER_APPROVED_D1",
        )
        for phrase in (
            "cannot establish a complete Strategic Value ranking",
            "For a Strategic Value claim, a counterfactual comparison must identify",
            "explicitly quantify their divergence",
        ):
            self.assertIn(phrase, overlay["L9-SV-001"])
        for narrowed in (
            "causally attributed",
            "identified and justified",
            "When causal",
        ):
            self.assertNotIn(narrowed, overlay["L9-SV-001"])
        # The superseded development text stays on record, and only there.
        self.assertIn(
            "causally attributed",
            rows["L9-SV-001"]["superseded_development_statement"],
        )

    def test_sv002_statement_unchanged_and_sv001_is_the_ledgered_text(self):
        statements = donor_statements()
        overlay = {r["id"]: r["statement"] for r in self.src["invariants"]}
        self.assertEqual(overlay["L9-SV-002"], statements["L9-SV-002"])
        sv001 = next(
            r
            for r in yaml.safe_load(
                (REDUCTION_EVIDENCE / "owner-disposition-ledger.yaml").read_text()
            )["dispositions"]
            if r["candidate_id"] == "L9-SV-001"
        )
        self.assertEqual(overlay["L9-SV-001"], sv001["amended_statement"].strip())
        self.assertEqual(set(overlay), {"L9-SV-001", "L9-SV-002"})

    def test_contract_obligations_are_not_more_permissive(self):
        donor = read_yaml("contracts_additions.yaml", DONOR)["contracts"][0]
        reduced = self.src["contract"]
        for key in set(donor) | set(reduced):
            if key == "source_invariants":
                continue
            self.assertEqual(reduced.get(key), donor.get(key), key)

    def test_model_changes_only_governance_and_lineage(self):
        donor = read_yaml("strategic_value_model.yaml", DONOR)
        reduced = copy.deepcopy(self.src["model"])
        reduced.pop(LINEAGE)
        reduced["governed_by"]["invariants"] = donor["governed_by"]["invariants"]
        self.assertEqual(reduced, donor)
        self.assertEqual(len(self.src["model"]["evaluation_integrity"]), 6)

    def test_schemas_change_only_invariants_and_lineage(self):
        for name in (
            "strategic_planner_value_projection.schema.yaml",
            "strategic_planner_value_composition.schema.yaml",
        ):
            donor = read_yaml(name, DONOR)
            reduced = read_yaml("semantics/" + name)
            props = reduced["properties"]
            # Mask exactly the declared changes; every other byte of meaning
            # (e.g. the invariant record's required fields) must equal the donor.
            if "strategic_value_model" in props:
                svm = props["strategic_value_model"]
                svm["properties"].pop(LINEAGE)
                svm["required"].remove(LINEAGE)
                gov = svm["properties"]["governed_by"]["properties"]["invariants"]
                inv = props["invariants"]["properties"]["invariants"]
                donor_inv = donor["properties"]["invariants"]["properties"][
                    "invariants"
                ]
            else:
                props.pop(LINEAGE)
                gov = props["governed_by"]["properties"]["invariants"]
                inv = props["invariants"]
                donor_inv = donor["properties"]["invariants"]
            self.assertEqual(gov["min_items"], 12)
            gov["min_items"] = 15
            self.assertEqual(len(gov["items"].pop("enum")), 12)
            self.assertEqual(inv["min_items"], 12)
            inv["min_items"] = donor_inv["min_items"]
            inv["items"]["properties"]["id"]["enum"] = donor_inv["items"]["properties"][
                "id"
            ]["enum"]
            self.assertEqual(reduced, donor, name)

    def test_profile_changes_only_invariant_selectors_and_lineage_selector(self):
        donor = read_yaml("projection_profile_additions.yaml", DONOR)
        reduced = copy.deepcopy(self.src["catalog"])
        p = reduced["projection_profiles"][0]
        p["sources"]["strategic_value_model"]["selectors"].remove("$." + LINEAGE)
        p["sources"]["invariants"] = donor["projection_profiles"][0]["sources"][
            "invariants"
        ]
        self.assertEqual(reduced, donor)


class NegativeControls(unittest.TestCase):
    """Section 11.2: each mutation must be detected through its intended check."""

    def setUp(self):
        self.src = load_sources()

    def assertCaught(self, fn, fragment):
        violations = closure_violations(mutated(self.src, fn))
        self.assertTrue(any(fragment in v for v in violations), violations)

    def test_reintroduced_sv015_selector(self):
        self.assertCaught(
            lambda s: s["catalog"]["projection_profiles"][0]["sources"]["invariants"][
                "selectors"
            ].append('$.invariants[?(@.id=="L9-SV-015")]'),
            "profile invariant selectors",
        )

    def test_removed_sv015_counterfactual_obligation(self):
        ob = "counterfactual_worlds_share_defensible_initial_conditions_time_basis_and_identification_assumptions"
        self.assertCaught(
            lambda s: s["contract"]["requires"].remove(ob),
            "L9-SV-015: contract obligation",
        )

    def test_removed_sv020_model_assurance_obligation(self):
        self.assertCaught(
            lambda s: s["model"]["evaluation_integrity"].pop(
                "independent_method_assurance"
            ),
            "L9-SV-020: model section",
        )
        ob = (
            "method_identity_input_lineage_executed_method_evidence_and_applicable_independently_reviewable_"
            "model_validation_evidence_for_strong_numerical_claims"
        )
        self.assertCaught(
            lambda s: s["contract"]["requires"].remove(ob),
            "L9-SV-020: contract obligation",
        )

    def test_missing_evidence_or_assurance_governance(self):
        for ref in ("L9-EVIDENCE-001", "L9-ASSURANCE-001"):
            self.assertCaught(
                lambda s, r=ref: s["model"]["governed_by"]["invariants"].remove(r),
                "model governed_by.invariants",
            )
            self.assertCaught(
                lambda s, r=ref: s["contract"]["source_invariants"].remove(r),
                "contract source_invariants",
            )

    def test_model_change_not_reflected_in_schema(self):
        def add_selector(s):
            s["model"]["new_semantic_section"] = {"x": 1}
            s["catalog"]["projection_profiles"][0]["sources"]["strategic_value_model"][
                "selectors"
            ].append("$.new_semantic_section")

        self.assertCaught(add_selector, "absent from a payload schema")

        def add_lineage(s):
            s["model"][LINEAGE]["L9-SV-021"] = dict(s["model"][LINEAGE]["L9-SV-015"])

        self.assertCaught(add_lineage, "lineage required != model lineage keys")

    def test_duplicate_selected_invariant(self):
        self.assertCaught(
            lambda s: s["contract"]["source_invariants"].append("L9-HARD-001"),
            "duplicate IDs",
        )

    def test_missing_selected_invariant(self):
        self.assertCaught(
            lambda s: s["catalog"]["projection_profiles"][0]["sources"]["invariants"][
                "selectors"
            ].pop(),
            "profile invariant selectors",
        )

    def test_schema_accepting_false_for_normative_truth(self):
        def unpin(s):
            node = s["projection_schema"]["properties"]["valuation"]["properties"][
                "accounting_partition_contract"
            ]["properties"]["normative_partition"]["properties"][
                "mutually_exclusive_booking"
            ]
            node.pop("const")

        self.assertCaught(unpin, "not pinned to source")

    def test_schema_accepting_empty_required_array(self):
        def drop_min(s):
            s["composition_schema"]["properties"]["strategic_value_model"][
                "properties"
            ][LINEAGE]["properties"]["L9-SV-018"]["properties"][
                "governing_invariants"
            ].pop("min_items")

        self.assertCaught(drop_min, "accepts empty array")
        self.assertCaught(
            lambda s: s["projection_schema"]["properties"]["invariants"].__setitem__(
                "min_items", 0
            ),
            "invariant min_items",
        )

    def test_composition_missing_namespace(self):
        self.assertCaught(
            lambda s: s["composition_schema"]["required"].remove("authority_model"),
            "exactly the five source classes",
        )

    def test_lineage_meaning_drift_and_authority_promotion(self):
        self.assertCaught(
            lambda s: s["model"][LINEAGE]["L9-SV-016"].__setitem__(
                "meaning", "shortened"
            ),
            "L9-SV-016.meaning",
        )
        self.assertCaught(
            lambda s: s["model"][LINEAGE]["L9-SV-019"].__setitem__(
                "authority_status", "admitted"
            ),
            "L9-SV-019.authority_status",
        )
        self.assertCaught(
            lambda s: s["model"][LINEAGE]["L9-SV-017"].__setitem__("when", "always"),
            "L9-SV-017.when",
        )

    def test_removed_id_leaking_into_normative_context(self):
        self.assertCaught(
            lambda s: s["model"]["comparisons"].__setitem__("note", "see L9-SV-018"),
            "removed candidate ID in normative context",
        )

    def test_removed_id_in_lineage_schema_enum(self):
        def widen(s):
            s["projection_schema"]["properties"][LINEAGE]["properties"]["L9-SV-015"][
                "properties"
            ]["governing_invariants"]["items"]["enum"].append("L9-SV-015")

        self.assertCaught(widen, "governing_invariants enum")

    def test_governed_by_schema_enum_widened(self):
        self.assertCaught(
            lambda s: s["composition_schema"]["properties"]["strategic_value_model"][
                "properties"
            ]["governed_by"]["properties"]["invariants"]["items"]["enum"].append(
                "L9-SV-016"
            ),
            "governed_by.invariants enum",
        )

    def test_lineage_meaning_unpinned_in_schema(self):
        self.assertCaught(
            lambda s: s["projection_schema"]["properties"][LINEAGE]["properties"][
                "L9-SV-020"
            ]["properties"]["meaning"].__setitem__("const", "rewritten"),
            "L9-SV-020.meaning not pinned",
        )

    def test_fixture_claiming_source_invariant(self):
        self.assertCaught(
            lambda s: s["fixtures"]["cases"][0].__setitem__(
                "source_invariant", "L9-SV-015"
            ),
            "still claims a source invariant",
        )


class DigestAndProvenanceGates(unittest.TestCase):
    def test_package_checksums_match_and_detect_tampering(self):
        from reduction_closure import checksum_mismatches

        self.assertTrue((ROOT / "SHA256SUMS.txt").read_text().strip())
        self.assertEqual(checksum_mismatches(ROOT), [])
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "SV"
            shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns("__pycache__"))
            target = tree / "overlays" / "contracts_additions.yaml"
            target.write_text(target.read_text().replace("L9-SV-002", "L9-SV-019", 1))
            self.assertEqual(
                checksum_mismatches(tree), ["overlays/contracts_additions.yaml"]
            )

    def test_frozen_donor_matches_source_candidate_hashes(self):
        manifest = json.loads(
            (REDUCTION_EVIDENCE / "source-digest-lock.json").read_text()
        )
        from reduction_closure import sha256_file

        for row in manifest["donor_files"]:
            self.assertEqual(
                sha256_file(REDUCTION_EVIDENCE / row["frozen_copy"]),
                row["sha256"],
                row["path"],
            )

    def test_local_falsifier_result_is_not_a_producer_receipt(self):
        result = json.loads(
            (REDUCTION_EVIDENCE / "falsification-results.json").read_text()
        )
        self.assertTrue(producer_receipt_problems(result))
        for case in result["cases"]:
            self.assertTrue(producer_receipt_problems(case))

    def test_real_producer_receipts_are_bound_to_rehearsal_revision_not_canonical(self):
        with tarfile.open(REDUCTION_EVIDENCE / "projection-run1.tar") as tar:
            receipts = {
                m.name: json.loads(tar.extractfile(m).read())
                for m in tar.getmembers()
                if m.isfile() and m.name.startswith("receipts/")
            }
        self.assertEqual(len(receipts), 6)
        summary = json.loads(
            (REDUCTION_EVIDENCE / "determinism-comparison.json").read_text()
        )
        rehearsal = summary["rehearsal_authority_revision"]
        for name, receipt in sorted(receipts.items()):
            self.assertEqual(producer_receipt_problems(receipt), [], name)
            self.assertEqual(receipt["governing_coordinates"]["revision"], rehearsal)
            stale = copy.deepcopy(receipt)
            stale["producer_identity"]["compiler"] = "local-falsifier"
            self.assertTrue(producer_receipt_problems(stale))


if __name__ == "__main__":
    unittest.main()


class OwnerDecisionGuard(unittest.TestCase):
    """The reduction refuses an approval that the owner-decision record does not back."""

    def _load(self, ledger_edit=None, decision_edit=None):
        import importlib.util
        import tempfile

        spec = importlib.util.spec_from_file_location(
            "reduce_tool", ROOT / "tools" / "reduce_to_two_invariants.py"
        )
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        ledger = yaml.safe_load(tool.LEDGER.read_text(encoding="utf-8"))
        decision = yaml.safe_load(tool.OWNER_DECISION.read_text(encoding="utf-8"))
        if ledger_edit:
            ledger_edit(ledger)
        if decision_edit:
            decision_edit(decision)
        with tempfile.TemporaryDirectory() as tmp:
            lp, dp = Path(tmp) / "ledger.yaml", Path(tmp) / "decision.yaml"
            lp.write_text(yaml.safe_dump(ledger), encoding="utf-8")
            dp.write_text(yaml.safe_dump(decision), encoding="utf-8")
            tool.LEDGER, tool.OWNER_DECISION = lp, dp
            return tool.load_ledger()

    def test_committed_approval_is_accepted(self):
        self.assertEqual(len(self._load()["dispositions"]), 8)

    def test_approval_without_an_approved_record_is_refused(self):
        def unapprove(d):
            d["decision_status"] = "PENDING_UNTIL_AUTHORIZED"

        with self.assertRaises(ValueError):
            self._load(decision_edit=unapprove)

    def test_approval_citing_another_record_is_refused(self):
        def reroute(led):
            led["dispositions"][3]["owner_decision_ref"] = "elsewhere.yaml"

        with self.assertRaises(ValueError):
            self._load(ledger_edit=reroute)

    def test_disposition_differing_from_the_approved_one_is_refused(self):
        def flip(d):
            d["approved_dispositions"]["L9-SV-019"] = "CONTRACT"

        with self.assertRaises(ValueError):
            self._load(decision_edit=flip)
