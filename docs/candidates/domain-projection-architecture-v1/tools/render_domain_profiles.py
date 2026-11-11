#!/usr/bin/env python3
"""Render the eight v1 domain projection and composition profiles.

The section selections below are the v1 design source. Invariant selections
are computed, never hand-listed: primary anchors, the common closure and the
mandatory closure from semantics/domain_projection_model.yaml, plus the
source_invariants of every contract the domain selects, emitted in
invariants.yaml order. `--check` exits 1 when the canonical catalogs differ
from the rendering; `--write` replaces the domain blocks in place.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[4]
SEM = ROOT / "semantics"
BEGIN = "# BEGIN domain projection profiles v1 (rendered by docs/candidates/domain-projection-architecture-v1/tools/render_domain_profiles.py)\n"
END = "# END domain projection profiles v1\n"
CBEGIN = BEGIN.replace("projection profiles", "composition profiles")
CEND = END.replace("projection profiles", "composition profiles")
PAYLOAD_VALIDATION = "l9.payload-validation/source-class-dispatch@1"

COMMON_FORBIDDEN = ["obligation_not_admitted_in_a_selected_source"]

# name -> (purpose, sections, contracts, extra vocabulary terms, forbidden)
DOMAINS: dict[str, dict[str, Any]] = {
    "architecture": {
        "purpose": "Expose reusable canonical architecture semantics: structures, relationships, architecture rules, product kinds, archetypes, ports and composition constraints, independently of any consumer. Structural validity is not capability availability, strategic desirability or governance approval. The profile names no consumer and grants no admission or action authority.",
        "sections": {
            "architecture_patterns": [
                "global_rules",
                "pattern_classes",
                "patterns",
                "composition_rules",
                "architecture_synthesis",
            ],
            "architecture_rules": [
                "global_rules",
                "rule_shape",
                "rules",
                "resolution_rule",
            ],
            "product_topology": [
                "required",
                "properties",
                "semantic_rules",
                "kind_resolution",
            ],
            "product_kinds": ["global_rules", "kinds", "kind_exceptions"],
            "node_archetypes": ["global_rules", "archetypes"],
            "dependency_archetypes": ["global_rules", "archetypes"],
            "port_catalog": ["global_rules", "port_entry_contract", "ports"],
        },
        "contracts": [],
        "terms": [],
        "forbidden": [
            "provider_implementation_details",
            "target_rendering_details",
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "strategic-value": {
        "purpose": "Expose unified qualitative and quantitative Strategic Value semantics: the complete normative strategic value model, the admitted numerical and qualitative invariants, the assessment contract and the Strategic Value vocabulary. Numerical claim authority stays with the model's numerical owner; a qualitative appraisal is not a computed value, missing evidence is not zero, and the profile computes, ranks, admits and authorizes nothing.",
        "sections": {
            "strategic_value_model": [
                "artifact_id",
                "authority",
                "canonical_source",
                "governed_by",
                "purpose",
                "identity",
                "valuation",
                "counterfactual_mathematics",
                "strategic_interaction_lookahead",
                "assessment_claim_levels",
                "evaluation_integrity",
                "causal_accounting",
                "forecast_and_realization",
                "comparisons",
                "explicit_non_ownership",
                "assessment_applicability",
                "retained_former_candidate_semantics",
                "relocated_additional_candidate_semantics",
            ],
        },
        "contracts": ["l9.contract/strategic-value-assessment@1"],
        "terms": [
            "strategic_value",
            "systemic_future_value",
            "strategic_value_assessment",
            "counterfactual_baseline",
            "future_effect_identity",
            "bidirectional_value_propagation",
            "value_propagation_mesh",
            "future_work_elimination",
            "capability_unlock",
            "decision_relevant_information_value",
            "decision_boundary",
            "qualitative_strategic_value_screen",
            "realized_strategic_compounding",
        ],
        "forbidden": [
            "provider_implementation_details",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "signals": {
        "purpose": "Expose admitted Signal semantics: evidence-bearing information movement, propagation, bounded feedback and consumption, independently of evidence assurance and of realized value. Signal propagation does not prove value, feedback is not automatic learning, and consumption is not action authority.",
        "sections": {},
        "contracts": [],
        "terms": [
            "signal",
            "signal_propagation",
            "signal_feedback_episode",
            "signal_consumption",
        ],
        "forbidden": [
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "governance": {
        "purpose": "Expose canonical authority, admission, promotion, lifecycle and policy boundaries: who may decide, what admission requires and which boundaries constrain action. Validation is not admission, execution success is not authority, and no consumer authorizes itself; the profile grants no authority.",
        "sections": {
            "authority_model": [
                "authority_classes",
                "admission_rules",
                "promotion_rules",
                "agent_authority",
                "human_authority",
                "escalation_rules",
            ],
            "lifecycle": ["lifecycles"],
        },
        "contracts": [
            "l9.contract/authority-boundary@1",
            "l9.contract/semantic-ownership@1",
            "l9.contract/monotonic-subordination@1",
            "l9.contract/admission-and-promotion@1",
        ],
        "terms": [],
        "forbidden": [
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "evidence-provenance": {
        "purpose": "Expose evidence, receipts, provenance, assurance and revision-bound currentness: what supports a claim, how it was produced and whether it is current against its governing coordinates. Evidence is not semantic authority, a stale receipt is not current assurance, and provenance is not proof of correctness.",
        "sections": {
            "receipt_catalog": [
                "global_rules",
                "receipt_kernel",
                "receipts",
                "receipt_relations",
            ],
            "artifact_model": ["artifacts", "derivation_rules"],
            "semantic_dependency_model": ["dependency_rules", "invalidation_rules"],
        },
        "contracts": [
            "l9.contract/evidence-and-receipt@1",
            "l9.contract/assurance-and-verification@1",
            "l9.contract/provenance-and-coordinate@1",
            "l9.contract/revision-and-supersession@1",
            "l9.contract/domain-composition-provenance@1",
        ],
        "terms": [],
        "forbidden": [
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "contracts-conformance": {
        "purpose": "Expose the global contract catalog with the invariants its contracts operationalize, and the requirement, resolution and conformance models: what must hold and how satisfaction or violation is established. A candidate never defines its own correctness, validation never mutates its subject, and conformance is not authorization.",
        "sections": {
            "contracts": ["contracts"],
            "conformance_model": [
                "ownership_boundary",
                "global_rules",
                "requirement_derivation_inputs",
                "conformance_requirement_shape",
                "output",
            ],
            "requirement_model": [
                "global_rules",
                "requirement_classes",
                "requirement_entry_contract",
                "closure_rules",
            ],
            "resolution_model": [
                "global_rules",
                "result_domain",
                "resolution_record",
                "selection_rules",
            ],
        },
        "contracts": "*",
        "terms": [],
        "forbidden": [
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "capabilities-dependencies": {
        "purpose": "Expose capability declarations, state dimensions, invocability, capability resolution and semantic dependency closure: which capabilities exist, which states are established and which dependencies govern their use. A capability is not authority, declared is not invocable, and no semantics substitute for another without a declared contract.",
        "sections": {
            "capabilities": [
                "global_rules",
                "capability_entry_contract",
                "capability_state_dimensions",
                "invocability_contract",
                "capability_relations",
                "capabilities",
            ],
            "capability_resolution": ["inputs", "resolution_order", "outputs", "rules"],
            "semantic_dependency_model": ["dependency_rules", "invalidation_rules"],
            "dependency_archetypes": ["global_rules", "archetypes"],
        },
        "contracts": [
            "l9.contract/capability-state@1",
            "l9.contract/unknown-and-degradation@1",
        ],
        "terms": [],
        "forbidden": [
            "provider_implementation_details",
            "target_rendering_details",
            "execution_publication_or_merge_authority_grant",
        ],
    },
    "identity-attribution": {
        "purpose": "Expose typed identity dimensions, actor and surface registries with their typed aliases, identity resolution and identity assertion: which identities are asserted, who acted and what attribution valid evidence supports. A surface is not an actor, a provider is not an author, and an unresolved actor is not a consequential author; identity never implies authority.",
        "sections": {
            "identity_model": [
                "global_rules",
                "identity_dimensions",
                "non_identity_dimensions",
                "identity_binding",
                "identity_resolution",
                "identity_assertion",
                "consumer_rules",
            ],
            "actor_registry": ["actors", "aliases", "alias_rules"],
            "surface_registry": ["surfaces", "aliases", "alias_rules"],
        },
        "contracts": [
            "l9.contract/identity-resolution@1",
            "l9.contract/identity-assertion@1",
        ],
        "terms": [],
        "forbidden": [
            "repository_local_policy_as_global_law",
            "execution_publication_or_merge_authority_grant",
        ],
    },
}


def load(name: str) -> Any:
    return yaml.safe_load((SEM / name).read_text("utf-8"))


def domain_records() -> dict[str, dict[str, Any]]:
    model = load("domain_projection_model.yaml")
    return {
        d["projection_profile"].split("/")[1].split("@")[0]: {
            **d,
            "common": model["common_invariant_closure"],
        }
        for d in model["domains"]
    }


def profile(
    name: str, record: dict[str, Any], invariants: list[dict], contracts: list[dict]
) -> dict[str, Any]:
    spec = DOMAINS[name]
    by_contract = {c["id"]: c for c in contracts}
    contract_ids = (
        [c["id"] for c in contracts]
        if spec["contracts"] == "*"
        else list(spec["contracts"])
    )
    wanted = (
        set(record["primary_anchors"])
        | set(record["common"])
        | set(record["mandatory_closure"])
    )
    for cid in contract_ids:
        wanted |= set(by_contract[cid]["source_invariants"])
    ordered = [i["id"] for i in invariants if i["id"] in wanted]
    missing = wanted - set(ordered)
    if missing:
        raise SystemExit(f"{name}: invariants not declared: {sorted(missing)}")
    sources: dict[str, Any] = {}
    for source_class, sections in spec["sections"].items():
        if source_class == "contracts":
            continue
        sources[source_class] = {"selectors": [f"$.{s}" for s in sections]}
    if spec["terms"]:
        sources["vocabulary"] = {"selectors": [f"$.terms.{t}" for t in spec["terms"]]}
    sources["invariants"] = {
        "selectors": [f'$.invariants[?(@.id=="{i}")]' for i in ordered]
    }
    if spec["contracts"] == "*":
        sources["contracts"] = {"selectors": ["$.contracts"]}
    elif contract_ids:
        sources["contracts"] = {
            "selectors": [f'$.contracts[?(@.id=="{c}")]' for c in contract_ids]
        }
    return {
        "id": record["projection_profile"],
        "class": "domain",
        "consumer": record["consumer"],
        "purpose": spec["purpose"],
        "sources": sources,
        "output": {"schema": f"l9.projection.domain.{name}/v1"},
        "forbidden": spec["forbidden"] + COMMON_FORBIDDEN,
        "payload_validation": {"protocol": PAYLOAD_VALIDATION},
    }


def composition(name: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["composition_profile"],
        "purpose": f"Compose the per-source projections of {record['projection_profile']} into one bounded, derived, non-canonical domain view, preserving each projected source whole under its canonical source-class identity.",
        "accepts": ["projection_artifact"],
        "composes": {"projection_profile": record["projection_profile"]},
        "merge_strategy": {
            "placement": "source_class_namespace",
            "source_coverage": "exact",
            "duplicate_source": "conflict",
            "semantic_identity_collision": "require_equivalence",
        },
        "conflict_result": "invalid",
        "output": {"schema": f"l9.composed-projection.domain.{name}/v1"},
        "payload_validation": {"protocol": PAYLOAD_VALIDATION},
    }


def dump_list(items: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(items, sort_keys=False, width=110, allow_unicode=True)


def render() -> tuple[str, str]:
    invariants = load("invariants.yaml")["invariants"]
    contracts = load("contracts.yaml")["contracts"]
    records = domain_records()
    if set(records) != set(DOMAINS):
        raise SystemExit(f"domain set mismatch: {sorted(set(records) ^ set(DOMAINS))}")
    order = list(records)
    profiles = [profile(n, records[n], invariants, contracts) for n in order]
    compositions = [composition(n, records[n]) for n in order]
    nested = "".join("  " + line for line in dump_list(compositions).splitlines(True))
    return BEGIN + dump_list(profiles) + END, "  " + CBEGIN + nested + "  " + CEND


def splice(text: str, block: str, begin: str, end: str, anchor: str) -> str:
    if begin in text:
        start = text.index(begin)
        stop = text.index(end) + len(end)
        return text[:start] + block + text[stop:]
    at = text.index(anchor)
    return text[:at] + block + text[at:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    pblock, cblock = render()
    pp = SEM / "projection_profiles.yaml"
    cp = SEM / "composition_profiles.yaml"
    new_pp = splice(
        pp.read_text("utf-8"), pblock, BEGIN, END, "projection_engine_contract_ref:"
    )
    ctext = cp.read_text("utf-8")
    if not ctext.endswith("\n"):
        ctext += "\n"
    if CBEGIN in ctext:
        start, stop = ctext.index("  " + CBEGIN), ctext.index(CEND) + len(CEND)
        new_cp = ctext[:start] + cblock + ctext[stop:]
    else:
        new_cp = ctext + cblock
    if args.write:
        pp.write_text(new_pp, "utf-8")
        cp.write_text(new_cp, "utf-8")
        print("rendered 8 domain projection profiles and 8 domain composition profiles")
        return 0
    differs = [
        p.name for p, new in ((pp, new_pp), (cp, new_cp)) if p.read_text("utf-8") != new
    ]
    for name in differs:
        print(f"DIFF semantics/{name}")
    return 1 if differs else 0


if __name__ == "__main__":
    sys.exit(main())
