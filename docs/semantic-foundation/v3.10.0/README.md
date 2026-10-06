# Semantic Foundation v3.10.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor defines what an L9 Strategic Plan means. It admits one canonical ledger, `semantics/strategic_plan_model.yaml`, which owns the meaning of Strategic Plan content: four Plan-owned primitives, five strategic relations, Affected Strategic Closure, and the boundary that separates a change in authoritative reality from a revision of strategy.

## Bounded delta

- Adds `semantics/strategic_plan_model.yaml` (`l9.strategic-plan-model/global@1`). It admits Strategic Goal, Strategic Target, Strategic Hypothesis, and Strategic Commitment; the relations `advances`, `enables`, `depends_on`, `conflicts_with`, and `supersedes`; and Affected Strategic Closure. It anchors to the existing Strategic Plan concept and Plan Keeper authority, reuses canonical `objective` and Strategic Intent without owning them, and reuses lifecycle supersession for `supersedes`.
- Registers the ledger in `semantics/canonical_sources.yaml`, classifies it once as a semantic catalog in `semantics/generic_compiler_manifest.yaml`, and adds five vocabulary terms deferring to it.
- Adds ADR-015 and RC-018 with a fail-closed negative-case batch.

## Non-goals

v3.10.0 adds no constitutional invariant, no contract, no artifact class, no schema, and no projection profile. It does not change `semantics/strategic_cognition_model.yaml` or `semantics/authority_model.yaml`. It defines no Strategic Plan schema, fields, identifiers, versions, relation endpoint typing, graph or hypergraph representation, temporal or horizon structure, confidence or probability model, closure algorithm, Plan Keeper or Reasoner runtime, prompts, model or provider selection, or actor binding. Representation is a later, separate decision.

## Authority

`Quantum-L9/.github` owns the global meaning of Strategic Plan content. The Plan Keeper owns the Strategic Plan itself within explicitly granted strategic authority, as admitted in v3.8.0. A store, runtime, or model that holds or computes strategic reasoning does not thereby own the Strategic Plan or its semantics.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.9.0/`. The predecessor release record remains immutable.
