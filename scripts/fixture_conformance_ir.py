#!/usr/bin/env python3
"""Validators for l9.fixture-ir/v1 and l9.conformance-ir/v1 (candidate R5-F1).

Read-only and deterministic. ``schema_violations`` checks shape with the
l9.schema-definition/v1 descriptor grammar (const, enum, type, required,
properties, items, min_items, and the symbolic types). ``fixture_ir_violations``
and ``conformance_ir_violations`` check every semantic rule of the two schemas
that is decidable from the documents alone. Each violation is reported as
``(rule, location, message)`` where ``rule`` is the exact ``semantic_rules``
string of the governing schema, so a negative fixture can name the rule it
falsifies.

Usage: scripts/fixture_conformance_ir.py --fixtures ops/fixtures/fixture-conformance-ir --schemas semantics

scripts/validate-semantics.py runs the same suite as RC-035.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

import yaml

SEMANTIC_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SCALAR_STRINGS = {"string", "semantic_ref"}
STRUCTURAL = "structural"

# --- fixture-IR rule strings (fixture_ir.schema.yaml#semantic_rules) ---------
F_LAW = "every_fixture_case_cites_at_least_one_source_law_and_every_assertion_law_ref_is_one_of_the_case_source_law_refs"
F_SINGLE = "a_single_when_names_exactly_one_operation_and_request_and_no_steps"
F_GROUP = "a_sequence_when_names_at_least_one_step_and_a_parallel_when_names_at_least_two_steps_and_neither_names_a_top_level_operation"
F_OP = "every_when_operation_and_every_interface_action_setup_operation_is_an_interface_surface_action"
F_PORT = "every_port_fixture_setup_operation_is_a_contract_ref_of_a_declared_setup_port"
F_OBS = "every_interface_action_observation_is_an_interface_surface_action_whose_effect_class_is_read_observation"
F_HOBS = "every_harness_observation_names_a_declared_harness_observation"
F_HCTL = "every_harness_control_step_names_a_declared_harness_control"
F_FAULT = "a_fault_injection_control_declares_a_target_port_ref_and_its_step_request_names_port_method_code_and_after_effect_before_or_after"
F_HPORT = "only_fault_injection_and_internal_setup_controls_name_a_target_port_and_no_harness_control_writes_system_under_test_state_otherwise"
F_CTX = "invocation_context_appears_only_on_gate_action_steps_and_interface_action_observations_and_its_values_are_fixture_literals_and_budget_ms_is_a_non_negative_integer"
F_HNOTGATE = (
    "no_harness_control_or_harness_observation_ref_is_an_interface_surface_action"
)
F_FROMCTL = "a_from_reference_names_a_harness_control_step_only_when_that_control_declares_a_result_contract_and_never_names_a_harness_observation"
F_EVAL = "a_relational_assertion_whose_target_or_observed_path_is_absent_at_evaluation_is_an_error_never_a_pass"
F_PRESENCE = "is_present_holds_iff_the_target_path_resolves_is_absent_iff_it_does_not_and_is_null_iff_it_resolves_to_null_and_an_absent_path_is_never_an_error_for_them"
F_COUNT = "a_count_where_operand_is_a_non_empty_where_list_of_path_scalar_predicate_and_literal_operand_clauses_and_a_non_negative_integer_count"
F_COUNTEVAL = (
    "count_where_holds_iff_exactly_count_group_members_satisfy_every_where_clause"
)
F_PRECOND = "a_given_step_precondition_is_a_flat_map_of_dotted_paths_to_literals_that_are_not_mappings_and_contain_no_value_reference"
F_PRECONDEVAL = "a_precondition_holds_iff_every_path_equals_its_literal_and_one_that_does_not_hold_is_a_setup_error_never_a_fail_or_a_pass"
F_FORBID = "no_forbidden_action_is_an_interface_surface_action_or_names_any_step_or_observation_operation"
F_TARGET = "every_assertion_targets_a_when_step_the_when_group_or_a_declared_observation_and_never_a_given_step"
F_GROUPPRED = (
    "count_where_targets_only_a_when_group_and_scalar_predicates_never_target_a_group"
)
F_CONTRACT = "result_contract_is_names_the_target_action_result_contract_or_a_declared_problem_contract"
F_SUT = "no_expected_value_derives_from_the_system_under_test"
F_OBSERVED = "an_observed_operand_appears_only_in_a_relational_predicate_and_never_names_its_own_target_value"
F_FROM = "a_from_reference_names_only_an_earlier_step_of_the_same_case_and_never_a_step_of_its_own_parallel_group"
F_IDS = "step_observation_assertion_and_case_ids_are_unique_within_their_scope"
F_UNRES = "an_unresolved_case_is_listed_in_unresolved_with_a_non_resolved_result_and_names_what_blocks_it"
F_EXEC = "an_executable_case_has_no_blocked_by_and_is_not_listed_in_unresolved"
F_DIGEST = "subject_and_provenance_closure_digest_are_equal"
F_CLOSURE = (
    "subject_closure_digest_is_the_closure_digest_of_the_consumed_product_manifest"
)
F_HSURF = "harness_controls_and_harness_observations_equal_the_product_harness_surface_entries_without_implementation_ref_for_the_same_product"
F_LAWRES = "every_source_law_ref_resolves_to_exactly_one_law_index_entry_with_source_provenance"
F_LAWUNIQ = "law_index_refs_are_unique"
F_LAWDIGEST = "provenance_law_index_digest_is_the_semantic_digest_of_law_index"
FIXTURE_RULES_CHECKED = [
    F_LAWRES,
    F_LAWUNIQ,
    F_LAWDIGEST,
    F_LAW,
    F_SINGLE,
    F_GROUP,
    F_OP,
    F_PORT,
    F_OBS,
    F_HOBS,
    F_HCTL,
    F_FAULT,
    F_HPORT,
    F_CTX,
    F_FORBID,
    F_TARGET,
    F_GROUPPRED,
    F_CONTRACT,
    F_SUT,
    F_OBSERVED,
    F_FROM,
    F_IDS,
    F_UNRES,
    F_EXEC,
    F_DIGEST,
    F_FROMCTL,
    F_HNOTGATE,
    F_COUNT,
    F_PRECOND,
]
# Rules proven by the reference evaluator over recorded results (runtime semantics).
FIXTURE_RULES_EVALUATED = [F_EVAL, F_PRESENCE, F_COUNTEVAL, F_PRECONDEVAL]
# Rules checked against a second document: the consumed manifest closure or the
# product harness surface.
FIXTURE_RULES_CROSS = [F_CLOSURE, F_HSURF]
# Rules whose evidence is a resolved manifest closure or that state a
# non-authority property: the solver's obligation, not decidable here.
FIXTURE_RULES_EXTERNAL = [
    "every_law_index_entry_resolves_in_the_consumed_manifest_resolved_closure_at_its_recorded_revision_and_digest",
    "interface_surface_actions_problem_contracts_and_setup_ports_are_exactly_lowered_from_the_consumed_manifest",
    "fixture_ir_adds_no_law_and_is_never_semantic_authority",
]

# --- conformance-IR rule strings (conformance_ir.schema.yaml#semantic_rules) -
C_WITNESS = "every_obligation_witness_names_a_fixture_case_of_the_consumed_fixture_ir"
C_TRACE = "every_obligation_traces_to_governing_semantics_through_a_governing_ref_shared_with_each_witness_case_source_law_refs"
C_UNRES = (
    "an_obligation_with_an_unresolved_witness_or_no_executable_witness_is_unresolved"
)
C_LISTED = "an_unresolved_obligation_is_listed_in_unresolved_with_a_non_resolved_result_and_an_executable_obligation_is_not"
C_NOPASS = "an_unresolved_obligation_never_yields_a_pass_verdict"
C_PLAN = "a_fixture_replay_obligation_with_witnesses_has_an_execution_plan_whose_cases_are_exactly_the_witnessed_by_cases_and_any_other_obligation_has_none"
C_PERLAW = "there_is_exactly_one_obligation_per_law_index_entry_of_the_consumed_fixture_ir_and_its_governing_refs_are_exactly_that_law_ref"
C_WITNESSALL = "an_obligation_is_witnessed_by_exactly_the_fixture_cases_whose_source_law_refs_cite_its_law"
C_DERIVED = "an_obligation_subject_class_observable_semantics_and_verification_class_are_its_law_kind_statement_and_verification_class"
C_VCLASS = "an_obligation_whose_verification_class_is_not_fixture_replay_is_unresolved_and_carries_no_execution_plan"
C_NEUTRAL = "the_execution_plan_names_no_target_technology_binding_or_runtime"
C_IDS = "obligation_ids_are_unique"
C_FDIGEST = "subject_and_provenance_fixture_ir_digest_are_the_semantic_digest_of_the_consumed_fixture_ir"
C_MDIGEST = (
    "subject_and_provenance_closure_digest_equal_the_consumed_fixture_ir_closure_digest"
)
C_SUT = (
    "no_expected_result_is_defined_by_the_system_under_test_or_by_conformance_evidence"
)
C_PROFILE_ABSENT = "an_absent_fixture_profile_is_recorded_as_a_typed_fixture_profile_absent_unknown_never_as_a_satisfied_requirement"
C_PROFILE_DECLARED = "a_declared_fixture_profile_names_at_least_one_profile_ref_and_records_no_fixture_profile_absent_unknown"
C_EXEC = "a_fixture_replay_obligation_whose_witnesses_are_all_executable_is_executable_whether_or_not_a_fixture_profile_is_declared"
CONFORMANCE_RULES_CHECKED = [
    C_PERLAW,
    C_WITNESSALL,
    C_DERIVED,
    C_VCLASS,
    C_PROFILE_ABSENT,
    C_PROFILE_DECLARED,
    C_EXEC,
    C_WITNESS,
    C_TRACE,
    C_UNRES,
    C_LISTED,
    C_NOPASS,
    C_PLAN,
    C_NEUTRAL,
    C_IDS,
    C_FDIGEST,
    C_MDIGEST,
    C_SUT,
]
CONFORMANCE_RULES_EXTERNAL = [
    "conformance_ir_adds_no_law_and_is_never_semantic_authority"
]

# --- harness-surface rule strings (harness_surface.schema.yaml#semantic_rules)
H_UNIQ = "control_refs_and_observation_refs_are_unique_across_the_surface"
H_PORT = "a_fault_injection_control_declares_a_target_port_ref_and_only_fault_injection_and_internal_setup_controls_name_one"
H_IMPL = "every_implementation_ref_is_a_repository_relative_posix_path_with_an_optional_top_level_symbol_that_never_escapes_the_repository"
HARNESS_RULES_CHECKED = [H_UNIQ, H_PORT, H_IMPL]
HARNESS_RULES_EXTERNAL = [
    "every_implementation_ref_names_existing_product_owned_code_and_is_verified_never_regenerated",
    # Checked on the fixture IR that consumes the surface (F_HNOTGATE + F_HSURF).
    "no_harness_control_or_observation_is_a_gate_action_and_the_surface_grants_none",
    "the_harness_surface_adds_no_law_and_is_never_semantic_authority",
]

# --- product-topology product-file rules (product_topology.schema.yaml) ----
T_DIGEST = (
    "a_conformance_product_file_digest_is_the_sha256_of_the_raw_bytes_of_the_named_file"
)
T_RESOLVE = "a_conformance_product_file_ref_resolves_to_exactly_one_repository_spec_authoritative_source_entry_whose_coordinate_equals_it_and_whose_path_stays_inside_the_repository"
T_REFUSAL = "an_unresolved_ambiguous_escaping_or_digest_mismatched_product_file_ref_is_a_typed_refusal_never_a_resolution"
TOPOLOGY_RULES_CHECKED = [T_DIGEST, T_RESOLVE, T_REFUSAL]
REFUSALS = {
    "product_file_ref_unresolved",
    "product_file_ref_ambiguous",
    "product_file_path_escapes_repository",
    "product_file_digest_mismatch",
}

# --- product-manifest closure rules (product_manifest.schema.yaml) ---------
M_CLOSURE = "manifest_closure_digest_is_the_semantic_digest_of_the_manifest_without_manifest_digest_closure_digest_and_conformance_compilation"
M_RECORD = "a_manifest_that_records_conformance_compilation_records_closure_digest_and_the_compiled_fixture_and_conformance_ir_digests"
MANIFEST_RULES_CHECKED = [M_CLOSURE, M_RECORD]
VERIFICATION_EXECUTABLE = "fixture_replay"

RELATIONAL = {"equals", "not_equals", "greater_than", "less_than"}
OPERAND_FREE = {"is_null", "is_present", "is_absent"}
CLAUSE_PREDICATES = RELATIONAL | OPERAND_FREE | {"includes", "excludes"}
IMPLEMENTATION_REF = re.compile(
    r"^(?P<path>[^:\\]+?)(?:::(?P<symbol>[A-Za-z_][A-Za-z0-9_]*))?$"
)
PLAN_KEYS = {"mode", "cases", "isolation", "verdict_rule"}
VERDICTS = {"pass", "fail", "error", "unresolved"}

Violation = tuple[str, str, str]


def semantic_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --- l9.schema-definition/v1 shape interpreter -----------------------------
def _type_ok(value: Any, type_name: str) -> bool:
    if type_name in SCALAR_STRINGS:
        return isinstance(value, str) and bool(value.strip())
    if type_name == "semantic_digest":
        return isinstance(value, str) and bool(SEMANTIC_DIGEST.match(value))
    if type_name == "any":
        return True
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "object":
        return isinstance(value, dict)
    return False  # unknown type names fail closed


def schema_violations(value: Any, descriptor: Any, path: str = "$") -> list[str]:
    if not isinstance(descriptor, dict):
        return [f"{path}: schema descriptor is not a mapping"]
    if "const" in descriptor and value != descriptor["const"]:
        return [f"{path}: expected const {descriptor['const']!r}"]
    if "enum" in descriptor and value not in (descriptor["enum"] or []):
        return [f"{path}: value not in declared enum"]
    declared = descriptor.get("type")
    if declared and not _type_ok(value, str(declared)):
        return [f"{path}: expected {declared}"]
    if declared == "object":
        for name in descriptor.get("required", []) or []:
            if name not in value:
                return [f"{path}.{name}: required field missing"]
        required = set(descriptor.get("required", []) or [])
        for key, child in (descriptor.get("properties") or {}).items():
            if key in value:
                if value[key] is None and key not in required:
                    continue
                found = schema_violations(value[key], child, f"{path}.{key}")
                if found:
                    return found
    if declared == "array":
        minimum = descriptor.get("min_items")
        if isinstance(minimum, int) and len(value) < minimum:
            return [f"{path}: fewer than {minimum} items"]
        items = descriptor.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                found = schema_violations(item, items, f"{path}[{index}]")
                if found:
                    return found
    return []


def _shape(doc: Any, schema: dict) -> list[Violation]:
    descriptor = {
        k: schema[k] for k in ("type", "required", "properties") if k in schema
    }
    return [(STRUCTURAL, "$", msg) for msg in schema_violations(doc, descriptor)]


# --- helpers ---------------------------------------------------------------
def _walk_special(value: Any) -> list[tuple[str, Any]]:
    """Every {"$name": ...} single-key mapping found anywhere inside value."""
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        keys = list(value)
        if len(keys) == 1 and isinstance(keys[0], str) and keys[0].startswith("$"):
            found.append((keys[0], value[keys[0]]))
        else:
            for child in value.values():
                found.extend(_walk_special(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_special(child))
    return found


def _when_steps(when: dict) -> list[dict]:
    if when.get("mode") == "single":
        return [
            {
                "id": "when",
                "operation": when.get("operation"),
                "request": when.get("request"),
            }
        ]
    return list(when.get("steps") or [])


def _count_where_problem(operand: Any) -> str | None:
    """None when operand is {where: [{path, predicate, operand?}, ...], count}; else why not."""
    if not isinstance(operand, dict) or set(operand) != {"where", "count"}:
        return "count_where operand must be exactly {where, count}"
    count = operand["count"]
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return f"count {count!r} is not a non-negative integer"
    where = operand["where"]
    if not isinstance(where, list) or not where:
        return "where must be a non-empty list of clauses"
    for i, clause in enumerate(where):
        if not isinstance(clause, dict) or not {"path", "predicate"} <= set(clause):
            return f"where[{i}] must name path and predicate"
        if set(clause) - {"path", "predicate", "operand"}:
            return f"where[{i}] carries {sorted(set(clause) - {'path', 'predicate', 'operand'})}"
        if not isinstance(clause["path"], str):
            return f"where[{i}].path is not a dotted path"
        if clause["predicate"] not in CLAUSE_PREDICATES:
            return f"where[{i}].predicate {clause['predicate']!r} is not a scalar clause predicate"
        if (clause["predicate"] in OPERAND_FREE) == ("operand" in clause):
            return f"where[{i}] operand presence does not match {clause['predicate']}"
        if _walk_special(clause.get("operand")):
            return f"where[{i}].operand is a value reference, not a literal"
    return None


# --- fixture IR rules --------------------------------------------------------
def fixture_ir_violations(doc: dict, schema: dict) -> list[Violation]:
    out = _shape(doc, schema)
    if out:
        return out
    surface = doc["interface_surface"]
    actions = {a["action_ref"]: a for a in surface["actions"]}
    problems = set(surface["problem_contract_refs"])
    port_contracts = {c for p in surface["setup_ports"] for c in p["contract_refs"]}
    controls = {c["control_ref"]: c for c in surface["harness_controls"]}
    harness_obs = {o["observation_ref"]: o for o in surface["harness_observations"]}
    forbidden = set(surface["forbidden_actions"])
    for ref in sorted(forbidden & set(actions)):
        out.append(
            (
                F_FORBID,
                "$.interface_surface",
                f"forbidden action {ref} is an interface action",
            )
        )
    for ref in sorted((set(controls) | set(harness_obs)) & set(actions)):
        out.append(
            (
                F_HNOTGATE,
                "$.interface_surface",
                f"harness ref {ref} is an interface (Gate) action",
            )
        )
    for ref, control in controls.items():
        port = control.get("target_port_ref")
        if control["kind"] == "fault_injection" and not port:
            out.append(
                (
                    F_FAULT,
                    f"$.interface_surface.harness_controls({ref})",
                    "fault injection names no target_port_ref",
                )
            )
        if port and control["kind"] not in ("fault_injection", "internal_setup"):
            out.append(
                (
                    F_HPORT,
                    f"$.interface_surface.harness_controls({ref})",
                    f"{control['kind']} control names a target port",
                )
            )
    unresolved_index: dict[str, dict] = {}
    for entry in doc["unresolved"]:
        unresolved_index.setdefault(entry["case_ref"], entry)
    law_refs = [entry["law_ref"] for entry in doc["law_index"]]
    if len(law_refs) != len(set(law_refs)):
        out.append((F_LAWUNIQ, "$.law_index", "duplicate law_ref"))
    indexed = set(law_refs)
    if doc["provenance"]["law_index_digest"] != semantic_digest(doc["law_index"]):
        out.append(
            (
                F_LAWDIGEST,
                "$.provenance.law_index_digest",
                "is not the digest of law_index",
            )
        )
    if doc["subject"]["closure_digest"] != doc["provenance"]["closure_digest"]:
        out.append(
            (
                F_DIGEST,
                "$.provenance.closure_digest",
                "differs from subject.closure_digest",
            )
        )
    case_ids: set[str] = set()
    for ci, case in enumerate(doc["fixture_cases"]):
        loc = f"$.fixture_cases[{ci}]({case['id']})"
        if case["id"] in case_ids:
            out.append((F_IDS, loc, "duplicate case id"))
        case_ids.add(case["id"])
        laws = set(case["source_law_refs"])
        for ref in case["source_law_refs"]:
            if ref not in indexed:
                out.append(
                    (
                        F_LAWRES,
                        f"{loc}.source_law_refs",
                        f"{ref} resolves to no law_index entry",
                    )
                )
        when = case["when"]
        mode = when["mode"]
        # when shape
        if mode == "single":
            if "operation" not in when or "request" not in when or "steps" in when:
                out.append(
                    (
                        F_SINGLE,
                        f"{loc}.when",
                        "single when needs operation and request and no steps",
                    )
                )
        else:
            steps = when.get("steps") or []
            minimum = 2 if mode == "parallel" else 1
            if "operation" in when or "request" in when or len(steps) < minimum:
                out.append(
                    (
                        F_GROUP,
                        f"{loc}.when",
                        f"{mode} when needs >= {minimum} steps and no top-level operation",
                    )
                )
        given_steps = case["given"]["steps"]
        wsteps = _when_steps(when)
        observations = case["expect"]["observations"]
        # ids
        step_ids: list[str] = [s["id"] for s in given_steps] + [
            s.get("id") for s in wsteps
        ]
        obs_ids = [o["id"] for o in observations]
        all_ids = step_ids + obs_ids
        if len(all_ids) != len(set(all_ids)):
            out.append((F_IDS, loc, "duplicate step or observation id"))
        assertion_ids = [a["id"] for a in case["expect"]["assertions"]]
        if len(assertion_ids) != len(set(assertion_ids)):
            out.append((F_IDS, loc, "duplicate assertion id"))
        # invocation context
        context_holders = (
            [(f"given.{s['id']}", s) for s in given_steps]
            + [("when", when)]
            + [(f"when.{w.get('id')}", w) for w in (when.get("steps") or [])]
            + [(f"expect.{o['id']}", o) for o in observations]
        )
        for where, holder in context_holders:
            if "context" not in holder:
                continue
            ctx = holder["context"]
            if (where.startswith(("given.", "expect."))) and holder.get(
                "kind"
            ) != "interface_action":
                out.append(
                    (
                        F_CTX,
                        f"{loc}.{where}",
                        "context on a step that is not a Gate action",
                    )
                )
            if _walk_special(ctx):
                out.append(
                    (
                        F_CTX,
                        f"{loc}.{where}.context",
                        "context value is a reference, not a literal",
                    )
                )
            budget = ctx.get("budget_ms")
            if "budget_ms" in ctx and not (
                isinstance(budget, int) and not isinstance(budget, bool) and budget >= 0
            ):
                out.append(
                    (
                        F_CTX,
                        f"{loc}.{where}.context.budget_ms",
                        f"{budget!r} is not a non-negative integer",
                    )
                )
        # given-step preconditions: flat {dotted path: literal} maps
        for s in given_steps:
            if "precondition" not in s:
                continue
            pre = s["precondition"]
            bad = [
                k
                for k, v in pre.items()
                if not (isinstance(k, str) and k.strip())
                or isinstance(v, dict)
                or _walk_special(v)
            ]
            if not pre or bad:
                out.append(
                    (
                        F_PRECOND,
                        f"{loc}.given.{s['id']}.precondition",
                        f"not a flat map of paths to literals (offending keys {bad})",
                    )
                )
        # forbidden operations anywhere
        used_ops = (
            [s["operation"] for s in given_steps]
            + [w.get("operation") for w in wsteps]
            + [o["operation"] for o in case["expect"]["observations"]]
        )
        for op in used_ops:
            if op in forbidden:
                out.append((F_FORBID, loc, f"forbidden action {op} names an operation"))
        # operations
        for s in given_steps:
            if s["kind"] == "harness_control":
                control = controls.get(s["operation"])
                if control is None:
                    out.append(
                        (
                            F_HCTL,
                            f"{loc}.given.{s['id']}",
                            f"{s['operation']} is not a declared harness control",
                        )
                    )
                elif control["kind"] == "fault_injection":
                    req = s["request"]
                    if not (
                        set(req) == {"port_method", "code", "after_effect"}
                        and isinstance(req.get("port_method"), str)
                        and isinstance(req.get("code"), str)
                        and req.get("after_effect") in ("before", "after")
                    ):
                        out.append(
                            (
                                F_FAULT,
                                f"{loc}.given.{s['id']}",
                                "fault request must be {port_method, code, after_effect: before|after}",
                            )
                        )
            if s["kind"] == "interface_action" and s["operation"] not in actions:
                out.append(
                    (
                        F_OP,
                        f"{loc}.given.{s['id']}",
                        f"{s['operation']} is not an interface action",
                    )
                )
            if s["kind"] == "port_fixture" and s["operation"] not in port_contracts:
                out.append(
                    (
                        F_PORT,
                        f"{loc}.given.{s['id']}",
                        f"{s['operation']} is not a setup-port contract",
                    )
                )
        for s in wsteps:
            if s.get("operation") not in actions:
                out.append(
                    (
                        F_OP,
                        f"{loc}.when.{s.get('id')}",
                        f"{s.get('operation')} is not an interface action",
                    )
                )
        for o in observations:
            if o["kind"] == "harness_observation":
                if o["operation"] not in harness_obs:
                    out.append(
                        (
                            F_HOBS,
                            f"{loc}.expect.{o['id']}",
                            f"{o['operation']} is not a declared harness observation",
                        )
                    )
                continue
            action = actions.get(o["operation"])
            if action is None or action["effect_class"] != "read_observation":
                out.append(
                    (
                        F_OBS,
                        f"{loc}.expect.{o['id']}",
                        f"{o['operation']} is not a read_observation action",
                    )
                )
        # $from sources: control steps only with a result contract; never harness observations
        opaque_controls = {
            s["id"]
            for s in given_steps
            if s["kind"] == "harness_control"
            and not (controls.get(s["operation"]) or {}).get("result_contract_ref")
        }
        harness_obs_ids = {
            o["id"] for o in observations if o["kind"] == "harness_observation"
        }
        for holder in list(given_steps) + list(wsteps) + list(observations):
            for name, ref in _walk_special(holder.get("request")):
                if (
                    name == "$from"
                    and isinstance(ref, dict)
                    and ref.get("step") in opaque_controls | harness_obs_ids
                ):
                    out.append(
                        (
                            F_FROMCTL,
                            f"{loc}.{holder.get('id')}",
                            f"$from names {ref.get('step')}, which has no contract-typed result",
                        )
                    )
        # $from references: earlier steps only, not own parallel group
        order: list[str] = [s["id"] for s in given_steps]
        visible: set[str] = set()
        for s in given_steps:
            for name, ref in _walk_special(s["request"]):
                if name == "$from" and (
                    not isinstance(ref, dict) or ref.get("step") not in visible
                ):
                    out.append(
                        (
                            F_FROM,
                            f"{loc}.given.{s['id']}",
                            f"$from {ref!r} is not an earlier step",
                        )
                    )
            visible.add(s["id"])
        group_visible = set(visible)
        for s in wsteps:
            for name, ref in _walk_special(s.get("request")):
                if name != "$from":
                    continue
                allowed = group_visible if mode == "parallel" else visible
                if not isinstance(ref, dict) or ref.get("step") not in allowed:
                    out.append(
                        (
                            F_FROM,
                            f"{loc}.when.{s.get('id')}",
                            f"$from {ref!r} is not an earlier step",
                        )
                    )
            if mode != "parallel":
                visible.add(s.get("id"))
        for o in observations:
            for name, ref in _walk_special(o["request"]):
                allowed = visible | {w.get("id") for w in wsteps}
                if name == "$from" and (
                    not isinstance(ref, dict) or ref.get("step") not in allowed
                ):
                    out.append(
                        (
                            F_FROM,
                            f"{loc}.expect.{o['id']}",
                            f"$from {ref!r} is not an earlier step",
                        )
                    )
        order.extend(s.get("id") for s in wsteps)
        # assertions
        when_ids = {s.get("id") for s in wsteps}
        given_ids = {s["id"] for s in given_steps}
        for a in case["expect"]["assertions"]:
            aloc = f"{loc}.expect.assertions.{a['id']}"
            if a["law_ref"] not in laws:
                out.append(
                    (
                        F_LAW,
                        aloc,
                        f"law_ref {a['law_ref']} is not a source_law_ref of the case",
                    )
                )
            target = a["target"]
            kind, ref, pred = target["kind"], target.get("ref"), a["predicate"]
            if kind == "step" and ref not in when_ids:
                out.append(
                    (
                        F_TARGET,
                        aloc,
                        f"step target {ref!r} is not a when step"
                        + (" (it is a given step)" if ref in given_ids else ""),
                    )
                )
            if kind == "observation" and ref not in obs_ids:
                out.append(
                    (F_TARGET, aloc, f"observation target {ref!r} is not declared")
                )
            if kind == "group" and mode == "single":
                out.append((F_TARGET, aloc, "group target in a single when"))
            if (pred == "count_where") != (kind == "group"):
                out.append((F_GROUPPRED, aloc, f"predicate {pred} on {kind} target"))
            operand = a.get("operand")
            if pred == "result_contract_is":
                expected_contracts = set(problems)
                if kind == "step":
                    op = next(
                        (s.get("operation") for s in wsteps if s.get("id") == ref), None
                    )
                    if op in actions:
                        expected_contracts.add(actions[op]["result_contract_ref"])
                elif kind == "observation":
                    op = next(
                        (o["operation"] for o in observations if o["id"] == ref), None
                    )
                    if op in actions:
                        expected_contracts.add(actions[op]["result_contract_ref"])
                    if op in harness_obs:
                        expected_contracts.add(harness_obs[op]["result_contract_ref"])
                if operand not in expected_contracts:
                    out.append(
                        (
                            F_CONTRACT,
                            aloc,
                            f"{operand!r} is not the target's result or a problem contract",
                        )
                    )
            if pred in OPERAND_FREE and "operand" in a:
                out.append((F_SUT, aloc, f"{pred} takes no operand"))
            if pred == "count_where":
                problem = _count_where_problem(operand)
                if problem:
                    out.append((F_COUNT, aloc, problem))
                continue
            for name, sref in _walk_special(operand):
                if name == "$observed":
                    if pred not in RELATIONAL or kind == "group":
                        out.append(
                            (
                                F_OBSERVED,
                                aloc,
                                f"$observed in non-relational predicate {pred}",
                            )
                        )
                    elif not isinstance(sref, dict) or sref.get("step") not in (
                        set(order) | set(obs_ids)
                    ):
                        out.append(
                            (
                                F_OBSERVED,
                                aloc,
                                f"$observed {sref!r} names no step or observation",
                            )
                        )
                    elif sref.get("step") == ref and sref.get("path", "") == target.get(
                        "path", ""
                    ):
                        out.append(
                            (
                                F_OBSERVED,
                                aloc,
                                "$observed names the assertion's own target value",
                            )
                        )
                else:
                    out.append(
                        (
                            F_SUT,
                            aloc,
                            f"operand uses {name}; expected values are literals or $observed",
                        )
                    )
        # disposition
        listed = case["id"] in unresolved_index
        if case["disposition"] == "unresolved":
            entry = unresolved_index.get(case["id"])
            if (
                entry is None
                or entry["result"] == "resolved"
                or not case.get("blocked_by")
            ):
                out.append(
                    (
                        F_UNRES,
                        loc,
                        "unresolved case must be listed in unresolved and name blocked_by",
                    )
                )
        else:
            if case.get("blocked_by") or listed:
                out.append(
                    (
                        F_EXEC,
                        loc,
                        "executable case has blocked_by or is listed in unresolved",
                    )
                )
    for ref in unresolved_index:
        if ref not in case_ids:
            out.append(
                (F_UNRES, "$.unresolved", f"case_ref {ref} names no fixture case")
            )
    return out


# --- conformance IR rules ----------------------------------------------------
def conformance_ir_violations(
    doc: dict, schema: dict, fixture_ir: dict
) -> list[Violation]:
    out = _shape(doc, schema)
    if out:
        return out
    cases = {c["id"]: c for c in fixture_ir["fixture_cases"]}
    laws = {e["law_ref"]: e for e in fixture_ir["law_index"]}
    citing = {
        ref: [
            c["id"] for c in fixture_ir["fixture_cases"] if ref in c["source_law_refs"]
        ]
        for ref in laws
    }
    digest = semantic_digest(fixture_ir)
    for where in ("subject", "provenance"):
        if doc[where]["fixture_ir_digest"] != digest:
            out.append(
                (
                    C_FDIGEST,
                    f"$.{where}.fixture_ir_digest",
                    "is not the digest of the consumed fixture IR",
                )
            )
        if doc[where]["closure_digest"] != fixture_ir["subject"]["closure_digest"]:
            out.append(
                (
                    C_MDIGEST,
                    f"$.{where}.closure_digest",
                    "differs from the fixture IR closure digest",
                )
            )
    profile = doc["fixture_profile"]
    absent_unknowns = [
        u for u in doc["unknowns"] if u["kind"] == "fixture_profile_absent"
    ]
    if profile["status"] == "absent":
        if profile["profile_refs"] or len(absent_unknowns) != 1:
            out.append(
                (
                    C_PROFILE_ABSENT,
                    "$.fixture_profile",
                    "absent profile needs no refs and one typed unknown",
                )
            )
        for oi, ob in enumerate(doc["obligations"]):
            if "profile_hint" in ob:
                out.append(
                    (
                        C_PROFILE_ABSENT,
                        f"$.obligations[{oi}]",
                        "profile_hint with no declared profile",
                    )
                )
    elif not profile["profile_refs"] or absent_unknowns:
        out.append(
            (
                C_PROFILE_DECLARED,
                "$.fixture_profile",
                "declared profile needs refs and no absent unknown",
            )
        )
    per_law: dict[str, int] = {ref: 0 for ref in laws}
    listed = {u["obligation_ref"]: u for u in doc["unresolved"]}
    ids: set[str] = set()
    for oi, ob in enumerate(doc["obligations"]):
        loc = f"$.obligations[{oi}]({ob['id']})"
        if ob["id"] in ids:
            out.append((C_IDS, loc, "duplicate obligation id"))
        ids.add(ob["id"])
        witnesses = ob["witnessed_by"]
        governing = set(ob["governing_refs"])
        law = None
        if len(ob["governing_refs"]) != 1 or ob["governing_refs"][0] not in laws:
            out.append(
                (
                    C_PERLAW,
                    loc,
                    f"governing_refs {ob['governing_refs']} is not exactly one law_index entry",
                )
            )
        else:
            ref = ob["governing_refs"][0]
            per_law[ref] += 1
            law = laws[ref]
            if witnesses != citing[ref]:
                out.append(
                    (
                        C_WITNESSALL,
                        loc,
                        f"witnessed_by {witnesses} is not the citing cases {citing[ref]}",
                    )
                )
            for field, expected in (
                ("subject_class", law["law_kind"]),
                ("observable_semantics", law["statement"]),
                ("verification_class", law["verification_class"]),
            ):
                if ob[field] != expected:
                    out.append(
                        (C_DERIVED, loc, f"{field} is not the law's {expected!r}")
                    )
        for w in witnesses:
            case = cases.get(w)
            if case is None:
                out.append((C_WITNESS, loc, f"witness {w} is not a fixture case"))
                continue
            if not governing & set(case["source_law_refs"]):
                out.append((C_TRACE, loc, f"witness {w} shares no governing ref"))
        replay = ob["verification_class"] == VERIFICATION_EXECUTABLE
        plan = ob.get("execution_plan")
        if not replay and (ob["disposition"] != "unresolved" or plan is not None):
            out.append(
                (
                    C_VCLASS,
                    loc,
                    f"{ob['verification_class']} obligation must be unresolved with no execution_plan",
                )
            )
        known = [cases[w] for w in witnesses if w in cases]
        must_be_unresolved = any(
            c["disposition"] == "unresolved" for c in known
        ) or not any(c["disposition"] == "executable" for c in known)
        if replay and must_be_unresolved and ob["disposition"] != "unresolved":
            out.append(
                (C_UNRES, loc, "obligation has an unresolved or no executable witness")
            )
        if (
            replay
            and not must_be_unresolved
            and len(known) == len(witnesses)
            and ob["disposition"] != "executable"
        ):
            out.append(
                (
                    C_EXEC,
                    loc,
                    "every witness is executable, so the obligation is executable",
                )
            )
        if ob["disposition"] == "unresolved":
            entry = listed.get(ob["id"])
            if entry is None or entry["result"] == "resolved":
                out.append(
                    (C_LISTED, loc, "unresolved obligation not listed in unresolved")
                )
        elif ob["id"] in listed:
            out.append((C_LISTED, loc, "executable obligation listed in unresolved"))
        needs_plan = replay and bool(witnesses)
        if needs_plan != (plan is not None):
            out.append(
                (
                    C_PLAN,
                    loc,
                    "a fixture_replay obligation with witnesses needs a plan; any other has none",
                )
            )
        if plan is not None:
            if sorted(plan["cases"]) != sorted(witnesses) or len(plan["cases"]) != len(
                set(plan["cases"])
            ):
                out.append(
                    (
                        C_PLAN,
                        f"{loc}.execution_plan",
                        "plan cases differ from witnessed_by",
                    )
                )
            extra = set(plan) - PLAN_KEYS
            if extra:
                out.append(
                    (C_NEUTRAL, f"{loc}.execution_plan", f"plan names {sorted(extra)}")
                )
        for key in (
            "expected",
            "expected_result",
            "observed_result",
            "evidence_result",
        ):
            if key in ob:
                out.append((C_SUT, loc, f"obligation carries {key}"))
    for ref, count in per_law.items():
        if count != 1:
            out.append(
                (
                    C_PERLAW,
                    "$.obligations",
                    f"law {ref} has {count} obligations, not one",
                )
            )
    for ref in listed:
        if ref not in ids:
            out.append((C_LISTED, "$.unresolved", f"{ref} names no obligation"))
    return out


# --- harness surface, closure and product-file rules -------------------------
def harness_surface_violations(doc: dict, schema: dict) -> list[Violation]:
    out = _shape(doc, schema)
    if out:
        return out
    refs = [c["control_ref"] for c in doc["harness_controls"]] + [
        o["observation_ref"] for o in doc["harness_observations"]
    ]
    for ref in sorted({r for r in refs if refs.count(r) > 1}):
        out.append((H_UNIQ, "$", f"{ref} is declared more than once"))
    for c in doc["harness_controls"]:
        loc = f"$.harness_controls({c['control_ref']})"
        port = c.get("target_port_ref")
        if c["kind"] == "fault_injection" and not port:
            out.append((H_PORT, loc, "fault injection names no target_port_ref"))
        if port and c["kind"] not in ("fault_injection", "internal_setup"):
            out.append((H_PORT, loc, f"{c['kind']} control names a target port"))
    for group, key in (
        ("harness_controls", "control_ref"),
        ("harness_observations", "observation_ref"),
    ):
        for entry in doc[group]:
            problem = implementation_ref_problem(entry["implementation_ref"])
            if problem:
                out.append((H_IMPL, f"$.{group}({entry[key]})", problem))
    return out


def implementation_ref_problem(value: str) -> str | None:
    """None for <repository-relative POSIX path>[::<top-level symbol>] that stays inside the repository."""
    match = IMPLEMENTATION_REF.match(value)
    if not match:
        return f"{value!r} is not <path>[::<symbol>]"
    path = match.group("path")
    if path.startswith("/") or "\\" in path:
        return f"{path!r} is not a repository-relative POSIX path"
    depth = 0
    for part in path.split("/"):
        if part in ("", "."):
            continue
        depth = depth - 1 if part == ".." else depth + 1
        if depth < 0:
            return f"{path!r} escapes the repository"
    if depth == 0:
        return f"{path!r} names no file"
    return None


def fixture_harness_violations(fixture_ir: dict, harness: dict) -> list[Violation]:
    """The fixture IR's harness lists are the surface's entries without implementation_ref."""

    def strip(entries: list[dict]) -> list[str]:
        return sorted(
            json.dumps(
                {k: v for k, v in e.items() if k != "implementation_ref"},
                sort_keys=True,
            )
            for e in entries
        )

    out: list[Violation] = []
    surface = fixture_ir["interface_surface"]
    if fixture_ir["subject"]["product_ref"] != harness["product_ref"]:
        out.append(
            (F_HSURF, "$.subject.product_ref", "harness surface is another product's")
        )
    for key in ("harness_controls", "harness_observations"):
        if sorted(json.dumps(e, sort_keys=True) for e in surface[key]) != strip(
            harness[key]
        ):
            out.append(
                (
                    F_HSURF,
                    f"$.interface_surface.{key}",
                    "differs from the product harness surface entries",
                )
            )
    return out


def closure_digest(manifest: dict) -> str:
    """closure_digest of product_manifest.schema.yaml#closure_digest_definition."""
    body = json.loads(json.dumps(manifest))
    body.pop("manifest_digest", None)
    body.pop("closure_digest", None)
    if isinstance(body.get("conformance"), dict):
        body["conformance"].pop("compilation", None)
    return semantic_digest(body)


def manifest_closure_violations(manifest: dict) -> list[Violation]:
    out: list[Violation] = []
    compilation = (manifest.get("conformance") or {}).get("compilation")
    if compilation is not None and (
        "closure_digest" not in manifest
        or not (
            isinstance(compilation, dict)
            and {"fixture_ir_digest", "conformance_ir_digest"} <= set(compilation)
        )
    ):
        out.append(
            (
                M_RECORD,
                "$.conformance.compilation",
                "compilation needs closure_digest and both IR digests",
            )
        )
    if "closure_digest" in manifest and manifest["closure_digest"] != closure_digest(
        manifest
    ):
        out.append(
            (M_CLOSURE, "$.closure_digest", "is not the closure digest of the manifest")
        )
    return out


def fixture_closure_violations(fixture_ir: dict, manifest: dict) -> list[Violation]:
    expected = closure_digest(manifest)
    if fixture_ir["subject"]["closure_digest"] != expected:
        return [
            (
                F_CLOSURE,
                "$.subject.closure_digest",
                "is not the consumed manifest's closure digest",
            )
        ]
    return []


def resolve_product_file(
    ref: str, digest: str, repository_spec: dict, files: dict[str, bytes]
) -> tuple[str, str]:
    """("resolved", path) or ("refused", <product_file_resolution refusal code>).

    files maps repository-relative paths to raw bytes; nothing else is read.
    """
    groups = ((repository_spec.get("source_surfaces") or {}).get("authoritative")) or {}
    entries = [e for g in groups.values() for e in (g or []) if isinstance(e, dict)]
    matches = [e for e in entries if e.get("coordinate") == ref]
    if not matches:
        return "refused", "product_file_ref_unresolved"
    if len(matches) > 1:
        return "refused", "product_file_ref_ambiguous"
    path = matches[0].get("path")
    if not isinstance(path, str) or implementation_ref_problem(path):
        return "refused", "product_file_path_escapes_repository"
    normal = posixpath.normpath(path)
    if normal not in files:
        return "refused", "product_file_ref_unresolved"
    if digest != "sha256:" + hashlib.sha256(files[normal]).hexdigest():
        return "refused", "product_file_digest_mismatch"
    return "resolved", normal


_MISSING = object()


def resolve_path(value: Any, path: str) -> Any:
    """Value at a dotted path (numeric segments index arrays); _MISSING when absent."""
    if path in ("", None):
        return value
    node = value
    for segment in str(path).split("."):
        if isinstance(node, dict) and segment in node:
            node = node[segment]
        elif isinstance(node, list) and segment.isdigit() and int(segment) < len(node):
            node = node[int(segment)]
        else:
            return _MISSING
    return node


def _clause_holds(value: Any, predicate: str, operand: Any) -> str:
    """pass | fail | error for one scalar predicate over a resolved-or-_MISSING value."""
    if predicate == "is_present":
        return "pass" if value is not _MISSING else "fail"
    if predicate == "is_absent":
        return "pass" if value is _MISSING else "fail"
    if predicate == "is_null":
        return "pass" if value is not _MISSING and value is None else "fail"
    if value is _MISSING or operand is _MISSING:
        return "error"
    try:
        held = {
            "equals": lambda: value == operand,
            "not_equals": lambda: value != operand,
            "greater_than": lambda: value > operand,
            "less_than": lambda: value < operand,
            "includes": lambda: isinstance(value, list) and operand in value,
            "excludes": lambda: isinstance(value, list) and operand not in value,
        }[predicate]()
    except (KeyError, TypeError):
        return "error"
    return "pass" if held else "fail"


def evaluate_assertion(
    assertion: dict, recorded: dict[str, Any], group: list[Any] | None = None
) -> str:
    """Reference evaluation of one assertion over recorded results: pass | fail | error.

    Relational predicates whose target or $observed path is absent are an error
    (F_EVAL). is_present / is_absent / is_null treat an absent path as a value,
    never an error (F_PRESENCE). count_where holds iff exactly `count` group
    members satisfy every where clause; a member whose clause path is absent
    does not satisfy that clause (F_COUNTEVAL).
    """
    pred = assertion["predicate"]
    operand = assertion.get("operand")
    if pred == "count_where":
        if group is None:
            return "error"
        satisfied = 0
        for member in group:
            if all(
                _clause_holds(
                    resolve_path(member, clause["path"]),
                    clause["predicate"],
                    clause.get("operand"),
                )
                == "pass"
                for clause in operand["where"]
            ):
                satisfied += 1
        return "pass" if satisfied == operand["count"] else "fail"
    target = assertion["target"]
    if target.get("ref") not in recorded:
        return "error"
    actual = resolve_path(recorded[target["ref"]], target.get("path", ""))
    if pred in OPERAND_FREE:
        return _clause_holds(actual, pred, None)
    if isinstance(operand, dict) and set(operand) == {"$observed"}:
        ref = operand["$observed"]
        if ref.get("step") not in recorded:
            return "error"
        operand = resolve_path(recorded[ref["step"]], ref.get("path", ""))
    return _clause_holds(actual, pred, operand)


# Kept for callers of the 1d3255e reference evaluator.
evaluate_relational = evaluate_assertion


def precondition_outcome(precondition: dict, result: Any) -> str:
    """hold | error: a precondition that does not hold is a setup error, never fail or pass."""
    for path, literal in precondition.items():
        value = resolve_path(result, path)
        if value is _MISSING or value != literal:
            return "error"
    return "hold"


def obligation_verdict(obligation: dict, case_outcomes: dict[str, str]) -> str:
    """Aggregate per-case outcomes (pass|fail) into an obligation verdict.

    Encodes an_unresolved_obligation_never_yields_a_pass_verdict and the
    verdict_rule const. An empty plan, a missing outcome, or any outcome other
    than pass or fail (including an unresolved case) is an error, never a pass.
    """
    if (
        obligation["disposition"] == "unresolved"
        or obligation.get("verification_class") != VERIFICATION_EXECUTABLE
        or "execution_plan" not in obligation
    ):
        return "unresolved"
    outcomes = [
        case_outcomes.get(c, "error") for c in obligation["execution_plan"]["cases"]
    ]
    if not outcomes:
        return "error"
    if any(o not in ("pass", "fail") for o in outcomes):
        return "error"
    if any(o == "fail" for o in outcomes):
        return "fail"
    return "pass"


# --- fixture-suite runner ----------------------------------------------------
def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _product_files(spec: dict) -> dict[str, bytes]:
    return {
        path: text.encode("utf-8") for path, text in (spec.get("files") or {}).items()
    }


def run_suite(fixtures: Path, schemas: Path) -> tuple[list[str], list[str]]:
    """Return (passes, failures) over positive/ and negative/ fixtures."""
    fschema = _load(schemas / "fixture_ir.schema.yaml")
    cschema = _load(schemas / "conformance_ir.schema.yaml")
    hschema = _load(schemas / "harness_surface.schema.yaml")
    tschema = _load(schemas / "product_topology.schema.yaml")
    mschema = _load(schemas / "product_manifest.schema.yaml")
    passes: list[str] = []
    failures: list[str] = []
    pos = fixtures / "positive"
    positive_fixture = _load(pos / "fixture_ir.yaml")
    positive_conf = _load(pos / "conformance_ir.yaml")
    positive_harness = _load(pos / "harness_surface.yaml")
    positive_manifest = _load(pos / "product_manifest.yaml")
    positive_files = _load(pos / "product_files.yaml")
    positive_evals = _load(pos / "evaluations.yaml")
    for label, found in (
        ("positive fixture_ir", fixture_ir_violations(positive_fixture, fschema)),
        (
            "positive conformance_ir",
            conformance_ir_violations(positive_conf, cschema, positive_fixture),
        ),
        (
            "positive harness_surface",
            harness_surface_violations(positive_harness, hschema),
        ),
        (
            "positive fixture_ir vs harness_surface",
            fixture_harness_violations(positive_fixture, positive_harness),
        ),
        (
            "positive product_manifest closure",
            manifest_closure_violations(positive_manifest),
        ),
        (
            "positive fixture_ir vs manifest closure",
            fixture_closure_violations(positive_fixture, positive_manifest),
        ),
    ):
        (failures if found else passes).append(f"{label}: {found or 'no violations'}")
    files = _product_files(positive_files)
    for item in positive_files["refs"]:
        got = resolve_product_file(
            item["ref"], item["digest"], positive_files["repository_spec"], files
        )
        if got == ("resolved", item["expected_path"]):
            passes.append(f"positive product file {item['ref']}: resolved to {got[1]}")
        else:
            failures.append(f"positive product file {item['ref']}: {got}")
    for item in positive_evals["evaluations"]:
        if "precondition" in item:
            got = precondition_outcome(item["precondition"], item["result"])
        else:
            got = evaluate_assertion(
                item["assertion"], item.get("recorded") or {}, item.get("group")
            )
        if got == item["expected_outcome"]:
            passes.append(f"positive evaluation {item['id']}: {got}")
        else:
            failures.append(
                f"positive evaluation {item['id']}: got {got}, expected {item['expected_outcome']}"
            )
    covered: set[str] = set()
    for path in sorted((fixtures / "negative").glob("*.yaml")):
        case = _load(path)
        kind = case["document"]
        if kind in ("evaluation", "precondition"):
            if kind == "evaluation":
                got = evaluate_assertion(
                    case["assertion"], case.get("recorded") or {}, case.get("group")
                )
            else:
                got = precondition_outcome(case["precondition"], case["result"])
            if got == case["expected_outcome"] and got not in ("pass", "hold"):
                passes.append(
                    f"negative {path.name}: evaluated to {got} under {case['violates']}"
                )
                covered.add(case["violates"])
            else:
                failures.append(
                    f"negative {path.name}: evaluated to {got}, expected {case['expected_outcome']}"
                )
            continue
        if kind == "verdict":
            obligation = positive_conf["obligations"][case["obligation_index"]]
            obligation = _apply(obligation, case.get("obligation_mutation") or [])
            got = obligation_verdict(obligation, case["case_outcomes"])
            if got == case["expected_verdict"] and got != "pass":
                passes.append(
                    f"negative {path.name}: aggregated to {got} under {case['violates']}"
                )
                covered.add(case["violates"])
            else:
                failures.append(
                    f"negative {path.name}: aggregated to {got}, expected {case['expected_verdict']}"
                )
            continue
        if kind == "product_file":
            spec = _apply(positive_files, case.get("mutation") or [])
            got = resolve_product_file(
                case["ref"],
                case["digest"],
                spec["repository_spec"],
                _product_files(spec),
            )
            if got == ("refused", case["expected_refusal"]):
                passes.append(
                    f"negative {path.name}: refused {got[1]} under {case['violates']}"
                )
                covered.add(case["violates"])
            else:
                failures.append(
                    f"negative {path.name}: got {got}, expected refusal {case['expected_refusal']}"
                )
            continue
        fixture_ir = _apply(positive_fixture, case.get("fixture_ir_mutation") or [])
        if kind == "conformance_ir":
            doc = _apply(positive_conf, case["mutation"])
            found = conformance_ir_violations(doc, cschema, fixture_ir)
        elif kind == "harness_surface":
            found = harness_surface_violations(
                _apply(positive_harness, case["mutation"]), hschema
            )
        elif kind == "fixture_harness":
            harness = _apply(positive_harness, case.get("harness_mutation") or [])
            found = fixture_harness_violations(fixture_ir, harness)
        elif kind == "closure":
            manifest = _apply(positive_manifest, case.get("manifest_mutation") or [])
            found = manifest_closure_violations(manifest) + fixture_closure_violations(
                fixture_ir, manifest
            )
        elif kind == "fixture_ir":
            found = fixture_ir_violations(
                _apply(positive_fixture, case["mutation"]), fschema
            )
        else:
            failures.append(f"negative {path.name}: unknown document kind {kind}")
            continue
        rules = {v[0] for v in found}
        if case["violates"] in rules:
            passes.append(f"negative {path.name}: rejected under {case['violates']}")
            covered.add(case["violates"])
        else:
            failures.append(
                f"negative {path.name}: expected {case['violates']}, got {sorted(rules) or 'ACCEPTED'}"
            )
    for rule in (
        FIXTURE_RULES_CHECKED
        + FIXTURE_RULES_EVALUATED
        + FIXTURE_RULES_CROSS
        + CONFORMANCE_RULES_CHECKED
        + HARNESS_RULES_CHECKED
        + TOPOLOGY_RULES_CHECKED
        + MANIFEST_RULES_CHECKED
    ):
        if rule not in covered:
            failures.append(f"rule without a falsifying fixture: {rule}")
    for label, declared, known in (
        (
            "fixture_ir",
            set(fschema["semantic_rules"]),
            set(
                FIXTURE_RULES_CHECKED
                + FIXTURE_RULES_EVALUATED
                + FIXTURE_RULES_CROSS
                + FIXTURE_RULES_EXTERNAL
            ),
        ),
        (
            "conformance_ir",
            set(cschema["semantic_rules"]),
            set(CONFORMANCE_RULES_CHECKED + CONFORMANCE_RULES_EXTERNAL),
        ),
        (
            "harness_surface",
            set(hschema["semantic_rules"]),
            set(HARNESS_RULES_CHECKED + HARNESS_RULES_EXTERNAL),
        ),
    ):
        if declared != known:
            failures.append(f"{label} rule set drift: {sorted(declared ^ known)}")
    for label, declared, known in (
        (
            "product_topology",
            set(tschema["semantic_rules"]),
            set(TOPOLOGY_RULES_CHECKED),
        ),
        (
            "product_manifest",
            set(mschema["semantic_rules"]),
            set(MANIFEST_RULES_CHECKED),
        ),
    ):
        if not known <= declared:
            failures.append(f"{label} rules not declared: {sorted(known - declared)}")
    if (
        set((tschema.get("product_file_resolution") or {}).get("refusals") or {})
        != REFUSALS
    ):
        failures.append("product_topology product_file_resolution refusal codes drift")
    return passes, failures


def _apply(base: Any, mutations: list[dict]) -> Any:
    """Apply [{op: set|delete|append, path: [keys/indices], value}] to a deep copy."""
    doc = json.loads(json.dumps(base))
    for m in mutations:
        *parents, last = m["path"]
        node = doc
        for key in parents:
            node = node[key]
        if m["op"] == "set":
            node[last] = m["value"]
        elif m["op"] == "delete":
            del node[last]
        elif m["op"] == "append":
            node[last].append(m["value"])
        else:
            raise ValueError(f"unknown mutation op {m['op']}")
    return doc


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    args = parser.parse_args(argv)
    passes, failures = run_suite(args.fixtures, args.schemas)
    for line in passes:
        print("PASS", line)
    for line in failures:
        print("FAIL", line)
    print(f"{len(passes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
