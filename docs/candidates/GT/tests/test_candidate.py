"""GT candidate boundary checks. Local and structural; real-producer evidence is read, not re-run."""

import json
import re
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import GOVERNING, ROOT, gt_payload, read

SV_TERMS = read("evidence/sv_alignment_binding.json")["sv_vocabulary_terms"]
LINEAGE = read("evidence/sv_alignment_binding.json")["sv_lineage_only_ids"]


class CanonicalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.t = read("overlays/vocabulary_additions.yaml")["terms"]
        self.i = read("overlays/invariants_additions.yaml")["invariants"]
        self.c = read("overlays/contracts_gt_core.yaml")["contracts"][0]
        self.sv = read("overlays/contracts_sv_dependent.yaml")["contracts"][0]
        self.p = read("overlays/projection_profile_additions.yaml")[
            "projection_profiles"
        ][0]
        self.cp = read("overlays/composition_profile_additions.yaml")["profiles"][0]
        self.inv = gt_payload("invariants")["invariants"]

    def test_minimal_nonduplicate_semantics(self):
        self.assertEqual([x["id"] for x in self.i], ["L9-GT-001"])
        self.assertEqual(len(self.t), 12)
        self.assertFalse(set(self.t) & set(SV_TERMS))
        self.assertEqual(self.c["source_invariants"], GOVERNING)
        self.assertFalse(
            any(x.startswith("L9-SV-") for x in self.c["source_invariants"])
        )
        self.assertNotIn("five_bucket", str(self.t))

    def test_dependent_contract_cites_reduced_sv_law_only(self):
        cited = self.sv["source_invariants"]
        self.assertEqual(len(cited), len(set(cited)))
        self.assertEqual(
            {x for x in cited if x.startswith("L9-SV-")}, {"L9-SV-001", "L9-SV-002"}
        )
        self.assertFalse(set(cited) & set(LINEAGE))
        for required in (
            "L9-GT-001",
            "L9-ASSURANCE-001",
            "L9-PROV-001",
            "L9-COORD-001",
            "L9-PROJECTION-001",
        ):
            self.assertIn(required, cited)
        self.assertNotIn("212", json.dumps(self.sv))
        self.assertNotIn("pr_", json.dumps(self.sv))

    def test_dependent_contract_uses_durable_admission_predicates(self):
        req = self.sv["requires"]
        for predicate in (
            "independently_admitted_sv_model_and_assessment_contract",
            "authenticated_current_sv_projection_and_composition",
            "authenticated_current_gt_projection_and_composition",
            "exact_compatible_canonical_authority_coordinates",
        ):
            self.assertEqual(req.count(predicate), 1)
        self.assertEqual(len(req), 16)
        self.assertIn(
            "claiming_sv_contract_is_admitted_because_a_candidate_is_open_or_candidate_schemas_pass",
            self.sv["forbidden"],
        )

    def test_gt_only_independent_of_sv(self):
        self.assertEqual(self.c["id"], "l9.contract/strategic-interaction-assessment@1")
        self.assertNotIn("strategic-value-assessment@1", json.dumps(self.c))
        self.assertEqual(self.c["applicability"]["sv_dependency"], "none_for_gt_only")
        self.assertIn("strategic-value-assessment@1", self.sv["purpose"])

    def test_projection_is_gt_only_and_selector_closed(self):
        self.assertEqual(self.p["id"], "l9.projection/strategic-planner-interaction@1")
        self.assertEqual(
            list(self.p["sources"]), ["vocabulary", "invariants", "contracts"]
        )
        self.assertEqual(
            self.p["sources"]["vocabulary"]["selectors"],
            ["$.terms." + x for x in self.t],
        )
        self.assertEqual(
            self.p["sources"]["invariants"]["selectors"],
            [f'$.invariants[?(@.id=="{x}")]' for x in GOVERNING],
        )
        self.assertEqual(
            self.p["sources"]["contracts"]["selectors"],
            ['$.contracts[?(@.id=="' + self.c["id"] + '")]'],
        )
        self.assertNotIn("strategic-planner-value@1", json.dumps(self.p))
        self.assertEqual(self.cp["composes"]["projection_profile"], self.p["id"])
        self.assertEqual(
            self.cp["merge_strategy"]["placement"], "source_class_namespace"
        )
        self.assertEqual(self.cp["merge_strategy"]["source_coverage"], "exact")

    def test_forbidden_tokens_all_have_registered_criteria(self):
        defs = read("overlays/projection_forbidden_constraint_additions.yaml")[
            "forbidden_constraint_definitions"
        ]
        self.assertEqual(
            self.p["forbidden"], ["sv_semantic_records_excluded_from_gt_projection"]
        )
        d = defs["sv_semantic_records_excluded_from_gt_projection"]
        self.assertEqual(set(d), {"criterion", "excluded_selections"})
        self.assertEqual(d["criterion"], "payload_excludes")
        vocab = [
            e["selector"]
            for e in d["excluded_selections"]
            if e["source_class"] == "vocabulary"
        ]
        self.assertEqual(vocab, ["$.terms." + t for t in SV_TERMS])
        invs = [
            e["selector"]
            for e in d["excluded_selections"]
            if e["source_class"] == "invariants"
        ]
        self.assertEqual(
            invs,
            [
                '$.invariants[?(@.id=="L9-SV-001")]',
                '$.invariants[?(@.id=="L9-SV-002")]',
            ],
        )
        self.assertNotIn("L9-SV-015", json.dumps(d))

    def test_retired_forbidden_protections_remain_contract_obligations(self):
        self.assertIn(
            "consumer_keeps_strategy_policy_permission_and_execution_authority",
            self.c["requires"],
        )
        self.assertIn(
            "iterative_stability_alone_claimed_as_nash_equilibrium_proof",
            self.c["forbidden"],
        )
        self.assertIn(
            "counterparty_statement_promoted_to_unknown_private_fact",
            self.c["forbidden"],
        )
        self.assertIn(
            "analysis_or_projection_result_promoted_to_action_permission",
            self.c["forbidden"],
        )

    def test_no_new_valuer_or_permission(self):
        self.assertIn(
            "one_question_appropriate_numerical_owner_method_for_canonical_sv_valuation_not_mandatory_qv",
            self.sv["requires"],
        )
        self.assertIn(
            "semantic_projection_composition_does_not_execute_numerical_valuation",
            self.sv["guarantees"],
        )
        self.assertIn(
            "adding_independent_gt_uplift_to_already_counted_sv_effect",
            self.sv["forbidden"],
        )
        self.assertIn(
            "automatic_plan_revision_or_action_from_combined_assessment",
            self.sv["forbidden"],
        )

    def test_native_schemas_carry_output_discriminators_and_six_ids(self):
        proj = read("semantics/strategic_interaction_projection.schema.yaml")
        comp = read("semantics/strategic_interaction_composition.schema.yaml")
        self.assertEqual(
            proj["properties"]["schema"], {"const": self.p["output"]["schema"]}
        )
        self.assertEqual(
            comp["properties"]["schema"], {"const": self.cp["output"]["schema"]}
        )
        self.assertNotIn("schema", proj.get("required", []))
        self.assertNotIn("schema", comp["required"])
        self.assertEqual(comp["required"], ["vocabulary", "invariants", "contracts"])
        for descriptor in (
            proj["properties"]["invariants"],
            comp["properties"]["invariants"]["properties"]["invariants"],
        ):
            self.assertEqual(descriptor["min_items"], 6)
            self.assertEqual(descriptor["items"]["properties"]["id"]["enum"], GOVERNING)
            self.assertEqual(
                descriptor["items"]["properties"]["scope"], {"const": "global"}
            )
            self.assertEqual(
                descriptor["items"]["properties"]["owner"],
                {"const": "Quantum-L9/.github"},
            )
        self.assertEqual(
            comp["properties"]["vocabulary"]["properties"]["terms"],
            proj["properties"]["terms"],
        )
        self.assertEqual(
            comp["properties"]["contracts"]["properties"]["contracts"],
            proj["properties"]["contracts"],
        )

    def test_producer_payload_is_exactly_the_six_governing_invariants(self):
        ids = [r["id"] for r in self.inv]
        self.assertEqual(sorted(ids), sorted(GOVERNING))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            gt_payload("vocabulary")["terms"],
            {k: self.t[k] for k in self.t},
        )
        self.assertEqual(gt_payload("contracts")["contracts"], [self.c])

    def test_strict_local_schema_accepts_producer_payloads(self):
        schema = read(
            "schemas/strategic_interaction_selected_payload.candidate.schema.json"
        )
        jsonschema.Draft202012Validator.check_schema(schema)
        for payload in (
            gt_payload("vocabulary"),
            gt_payload("invariants"),
            gt_payload("contracts"),
        ):
            jsonschema.validate(payload, schema)
        comp = {
            "vocabulary": gt_payload("vocabulary"),
            "invariants": gt_payload("invariants"),
            "contracts": gt_payload("contracts"),
        }
        jsonschema.validate(
            comp,
            read(
                "schemas/strategic_interaction_composed_payload.candidate.schema.json"
            ),
        )

    def test_strict_schema_rejects_missing_duplicate_or_extra_invariants(self):
        schema = read(
            "schemas/strategic_interaction_selected_payload.candidate.schema.json"
        )
        sv001 = {
            "id": "L9-SV-001",
            "statement": "x",
            "scope": "global",
            "owner": "Quantum-L9/.github",
        }
        bad = [
            self.inv[:-1],
            [*self.inv[:-1], self.inv[0]],
            [*self.inv, sv001],
            [*self.inv[:-1], sv001],
        ]
        for rows in bad:
            with (
                self.subTest(n=len(rows)),
                self.assertRaises(jsonschema.ValidationError),
            ):
                jsonschema.validate({"invariants": rows}, schema)

    def test_strict_schema_rejects_swapped_sv_and_extra_semantics(self):
        schema = read(
            "schemas/strategic_interaction_selected_payload.candidate.schema.json"
        )
        bad = [
            {
                "terms": dict(
                    self.t,
                    strategic_value={"semantic_class": "value", "definition": "copy"},
                )
            },
            {"invariants": self.inv, "sv": {"value": 500}},
            {"contracts": [self.sv]},
            {"terms": self.t, "invariants": self.inv},
        ]
        for payload in bad:
            with (
                self.subTest(payload=list(payload)),
                self.assertRaises(jsonschema.ValidationError),
            ):
                jsonschema.validate(payload, schema)

    def test_source_local_selector_replay_matches_producer(self):
        # Local replay of the two selector forms used; the producer evidence is the authority.
        records = {
            "vocabulary": {"terms": dict(self.t, **{t: {} for t in SV_TERMS})},
            "invariants": {
                "invariants": [*self.inv, {"id": "L9-SV-001"}, {"id": "L9-AUTH-001"}],
            },
            "contracts": {"contracts": [self.c, self.sv]},
        }
        result = {}
        for source_class, config in self.p["sources"].items():
            selected = {}
            for selector in config["selectors"]:
                term = re.fullmatch(r"\$\.terms\.([a-z_]+)", selector)
                target = re.fullmatch(
                    r'\$\.(invariants|contracts)\[\?\(@\.id=="([^"]+)"\)\]', selector
                )
                if term:
                    selected.setdefault("terms", {})[term.group(1)] = records[
                        source_class
                    ]["terms"][term.group(1)]
                else:
                    family, ref = target.groups()
                    rows = [r for r in records[source_class][family] if r["id"] == ref]
                    self.assertEqual(len(rows), 1, ref)
                    selected.setdefault(family, []).extend(rows)
            result[source_class] = selected
        self.assertEqual(result["vocabulary"], gt_payload("vocabulary"))
        self.assertEqual(
            sorted(r["id"] for r in result["invariants"]["invariants"]),
            sorted(r["id"] for r in gt_payload("invariants")["invariants"]),
        )
        self.assertEqual(result["contracts"], gt_payload("contracts"))

    def test_no_skill_and_no_sv_source_artifact_in_candidate(self):
        self.assertFalse(
            any(
                "/skills/" in p.as_posix() or p.name in ("SKILL.md", "skill.zip")
                for p in ROOT.rglob("*")
            )
        )
        for name in (
            "strategic_value_model.yaml",
            "strategic_planner_value_projection.schema.yaml",
            "strategic_value_interaction_assessment.schema.yaml",
        ):
            self.assertFalse((ROOT / "semantics" / name).exists())

    def test_lineage_only_sv_ids_absent_from_every_normative_gt_artifact(self):
        for rel in (
            "overlays/invariants_additions.yaml",
            "overlays/contracts_gt_core.yaml",
            "overlays/contracts_sv_dependent.yaml",
            "overlays/projection_profile_additions.yaml",
            "overlays/projection_forbidden_constraint_additions.yaml",
            "overlays/composition_profile_additions.yaml",
            "semantics/strategic_interaction_projection.schema.yaml",
            "semantics/strategic_interaction_composition.schema.yaml",
            "schemas/gt_sv_consumer_assessment.candidate.schema.json",
        ):
            text = (ROOT / rel).read_text()
            for cid in LINEAGE:
                self.assertNotIn(cid, text, rel)


if __name__ == "__main__":
    unittest.main()
