import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "candidate_apply", ROOT / "apply_to_pinned_checkout.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CandidateTests(unittest.TestCase):
    EXISTING = (
        "L9-AUTH-001",
        "L9-AUTH-002",
        "L9-HARD-001",
        "L9-UNKNOWN-001",
        "L9-STRATEGY-001",
        "L9-PROJECTION-001",
        "L9-PROV-001",
        "L9-EVIDENCE-001",
        "L9-ASSURANCE-001",
        "L9-COORD-001",
    )
    # The ten existing governing IDs must resolve, so the positive fixture carries all
    # ten (the development pack's single-invariant fixture cannot satisfy section 10.1).
    INVARIANTS = "schema: l9.invariants/v1\ninvariants:\n" + "".join(
        f"- id: {i}\n  statement: fixture {i}\n" for i in EXISTING
    )
    CONTRACTS_IDS = (
        "l9.contract/projection@1",
        "l9.contract/authority-boundary@1",
        "l9.contract/hard-constraint@1",
    )

    def fixture(self, root, invariants=None, contracts_digest=None):
        sem = root / "semantics"
        sem.mkdir(parents=True)
        invariants = invariants or self.INVARIANTS
        digest = (
            contracts_digest or hashlib.sha256(invariants.encode("utf-8")).hexdigest()
        )
        contracts = (
            "schema: l9.contracts/v1\nderivation:\n  source_digest_sha256: "
            + digest
            + "\n  source_invariant_count: "
            + str(len(yaml.safe_load(invariants)["invariants"]))
            + "\ncontracts:\n"
            + "".join(f"- id: {c}\n  purpose: fixture\n" for c in self.CONTRACTS_IDS)
        )
        originals = {
            "invariants.yaml": invariants,
            "contracts.yaml": contracts,
            "vocabulary.yaml": "schema: l9.vocabulary/v1\nterms:\n  strategy:\n    definition: Strategy\nrelationships:\n  depends_on: {}\n",
            "canonical_sources.yaml": "sources:\n- id: l9.source/authority-model@1\n  path: semantics/authority_model.yaml\nrules:\n  canonical_sources_must_be_registered: true\n",
            "projection_profiles.yaml": "source_classes:\n  vocabulary:\n    canonical_artifact: vocabulary.yaml\n  invariants:\n    canonical_artifact: invariants.yaml\n  contracts:\n    canonical_artifact: contracts.yaml\n  authority_model:\n    canonical_artifact: authority_model.yaml\nprojection_profiles:\n- id: l9.projection/example@1\n  class: consumer\n  consumer: example\nprojection_engine_contract_ref:\n  artifact: projection_engine_contract.yaml\n",
            "generic_compiler_manifest.yaml": "requires:\n  semantic_catalogs:\n  - strategic_plan_model.yaml\n  - vocabulary.yaml\n  artifact_schemas:\n  - pr_audit_composition.schema.yaml\n",
            "composition_profiles.yaml": "schema: l9.composition-profiles/v1\nprofiles:\n  - id: l9.compose/example@1\n    purpose: fixture\n",
        }
        originals["capabilities.yaml"] = (
            "schema: l9.capabilities/v1\nderivation:\n  source_artifacts:\n"
            "    - artifact: invariants.yaml\n      sha256: "
            + hashlib.sha256(invariants.encode()).hexdigest()
            + "\n      item_count: "
            + str(len(yaml.safe_load(invariants)["invariants"]))
            + "\n    - artifact: contracts.yaml\n      sha256: "
            + hashlib.sha256(contracts.encode()).hexdigest()
            + "\n      item_count: "
            + str(len(self.CONTRACTS_IDS))
            + "\ncapabilities: []\n"
        )
        for name, content in originals.items():
            (sem / name).write_text(content)

    def test_generates_destination_changes_and_rebinds_derivations(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p)
            changes, count = mod.generate(p)
            self.assertEqual(
                count, 12
            )  # 10 existing fixture invariants + 2 new candidate invariants
            self.assertEqual(
                len(changes), 11
            )  # 10 destinations + 1 rebound derived ledger
            contracts = yaml.safe_load(changes["semantics/contracts.yaml"])
            self.assertEqual(
                contracts["derivation"]["source_digest_sha256"],
                hashlib.sha256(
                    changes["semantics/invariants.yaml"].encode()
                ).hexdigest(),
            )
            self.assertEqual(contracts["derivation"]["source_invariant_count"], 12)
            caps = {
                e["artifact"]: e
                for e in yaml.safe_load(changes["semantics/capabilities.yaml"])[
                    "derivation"
                ]["source_artifacts"]
            }
            self.assertEqual(
                caps["invariants.yaml"]["sha256"],
                hashlib.sha256(
                    changes["semantics/invariants.yaml"].encode()
                ).hexdigest(),
            )
            self.assertEqual(caps["invariants.yaml"]["item_count"], 12)
            self.assertEqual(
                caps["contracts.yaml"]["sha256"],
                hashlib.sha256(
                    changes["semantics/contracts.yaml"].encode()
                ).hexdigest(),
            )
            self.assertEqual(caps["contracts.yaml"]["item_count"], 4)
            self.assertEqual(
                mod.generate.rebound,
                {"semantics/capabilities.yaml": ["invariants.yaml", "contracts.yaml"]},
            )
            for path, content in changes.items():
                self.assertIsInstance(yaml.safe_load(content), dict)
            self.assertIn(
                "l9.strategic.value@1", changes["semantics/strategic_value_model.yaml"]
            )
            self.assertIn(
                "l9.projection/strategic-planner-value@1",
                changes["semantics/projection_profiles.yaml"],
            )
            self.assertIn(
                "l9.contract/strategic-value-assessment@1",
                changes["semantics/contracts.yaml"],
            )
            self.assertIn(
                "l9.compose/strategic-planner-value@1",
                changes["semantics/composition_profiles.yaml"],
            )
            self.assertIn(
                "strategic_planner_value_projection.schema.yaml",
                changes["semantics/generic_compiler_manifest.yaml"],
            )
            self.assertIn(
                "strategic_planner_value_composition.schema.yaml",
                changes["semantics/generic_compiler_manifest.yaml"],
            )

    def test_pr6_math_and_profile_are_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p)
            changes, count = mod.generate(p)
            model = yaml.safe_load(changes["semantics/strategic_value_model.yaml"])
            self.assertEqual(count, 12)
            self.assertEqual(model["artifact_id"], "l9.strategic.value@1")
            self.assertEqual(
                model["source_lineage"]["donor_commit"],
                "fb0ae95620cea0dc3f48aa009056ddb755d69640",
            )
            self.assertIn("bounded_expression", model["counterfactual_mathematics"])
            self.assertIn(
                "bounded_recurrence", model["strategic_interaction_lookahead"]
            )
            self.assertIn("nonanticipativity", model["evaluation_integrity"])
            profile = yaml.safe_load(changes["semantics/projection_profiles.yaml"])
            current = [
                x
                for x in profile["projection_profiles"]
                if x["id"] == "l9.projection/strategic-planner-value@1"
            ][0]
            selectors = current["sources"]["strategic_value_model"]["selectors"]
            self.assertIn("$.counterfactual_mathematics", selectors)
            self.assertIn("$.strategic_interaction_lookahead", selectors)
            contract = yaml.safe_load(changes["semantics/contracts.yaml"])
            value_contract = [
                x
                for x in contract["contracts"]
                if x["id"] == "l9.contract/strategic-value-assessment@1"
            ][0]
            self.assertIn(
                "complete_probability_mass_when_probabilistic_method_applies_or_explicit_unresolved_missing_mass",
                value_contract["requires"],
            )

    def test_retired_generic_leverage_machine_term_not_reintroduced(self):
        value_terms = yaml.safe_load(mod.raw("overlays/vocabulary_additions.yaml"))[
            "terms"
        ]
        self.assertEqual(len(value_terms), 11)
        self.assertNotIn("leverage_mesh_loop", value_terms)
        self.assertNotIn("leverage_score", value_terms)
        self.assertIn("value_propagation_mesh", value_terms)
        invariants = yaml.safe_load(mod.raw("overlays/invariants_additions.yaml"))[
            "invariants"
        ]
        self.assertEqual(len(invariants), 2)
        self.assertEqual({row["id"] for row in invariants}, {"L9-SV-001", "L9-SV-002"})

    def test_unresolvable_governing_invariant_fails_closed(self):
        one = "schema: l9.invariants/v1\ninvariants:\n- id: L9-STRATEGY-001\n  statement: strategy owner\n"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p, invariants=one)
            with self.assertRaisesRegex(ValueError, "do not resolve in candidate"):
                mod.generate(p)

    def test_stale_contract_derivation_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p, contracts_digest="0" * 64)
            with self.assertRaisesRegex(
                ValueError, "stale contracts derivation digest"
            ):
                mod.generate(p)

    def test_stale_derived_ledger_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p)
            f = p / "semantics/capabilities.yaml"
            text = f.read_text()
            stale = text.replace(
                hashlib.sha256(self.INVARIANTS.encode()).hexdigest(), "f" * 64
            )
            f.write_text(stale)
            with self.assertRaisesRegex(ValueError, "stale derivation digest"):
                mod.generate(p)

    def test_duplicate_existing_invariant_ids_fail_closed(self):
        dup = self.INVARIANTS + "- id: L9-STRATEGY-001\n  statement: duplicate\n"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p, invariants=dup)
            with self.assertRaisesRegex(ValueError, "duplicate IDs"):
                mod.generate(p)

    def test_duplicate_incoming_ids_fail_closed(self):
        base = "invariants:\n- id: L9-A\n  statement: a\n"
        with self.assertRaisesRegex(
            ValueError, "candidate overlay invariants duplicate IDs"
        ):
            mod.merge_list(
                base,
                "invariants:\n- id: L9-B\n  statement: b\n- id: L9-B\n  statement: c\n",
                "invariants",
            )
        with self.assertRaisesRegex(ValueError, "collides with canonical IDs"):
            mod.merge_list(
                base, "invariants:\n- id: L9-A\n  statement: again\n", "invariants"
            )

    def test_incoming_id_colliding_with_canonical_fails_closed(self):
        inv = self.INVARIANTS + "- id: L9-SV-001\n  statement: earlier admission\n"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p, invariants=inv)
            with self.assertRaisesRegex(ValueError, "collides with canonical IDs"):
                mod.generate(p)

    def test_removed_candidate_in_normative_context_fails_closed(self):
        changed = {"model": {"governed_by": {"invariants": ["L9-SV-015"]}}}
        with self.assertRaisesRegex(
            ValueError, "removed candidate ID in normative context"
        ):
            mod.check_removed_ids_are_lineage_only(
                "model",
                changed["model"],
                [("relocated_additional_candidate_semantics",)],
            )
        mod.check_removed_ids_are_lineage_only(
            "model",
            {"relocated_additional_candidate_semantics": {"L9-SV-015": {}}},
            [("relocated_additional_candidate_semantics",)],
        )

    def test_anchor_cardinality_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p)
            f = p / "semantics/vocabulary.yaml"
            f.write_text(f.read_text() + "extra:\nrelationships:\n  other: {}\n")
            with self.assertRaises(ValueError):
                mod.generate(p)

    def test_collision_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            self.fixture(p)
            f = p / "semantics/vocabulary.yaml"
            f.write_text(
                f.read_text().replace(
                    "relationships:",
                    "  strategic_value:\n    definition: earlier\nrelationships:",
                )
            )
            with self.assertRaisesRegex(ValueError, "collision"):
                mod.generate(p)


if __name__ == "__main__":
    unittest.main()
