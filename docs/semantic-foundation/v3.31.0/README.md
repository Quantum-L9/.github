# Semantic Foundation v3.31.0

Status: **CORRECTIVE SUCCESSOR CANDIDATE**

v3.31.0 gives every field of every pattern in `semantics/architecture_patterns.yaml` one kind. Two fields had two kinds:

- one edge in `l9.pattern/reference-model-conformance@1` named two targets in a list, while every other edge names one node;
- `l9.pattern/authority-candidate-admission@1` declared `lifecycle` as a bare state list, while `l9.pattern/dependency-package@1` declares it as an object.

A closed source-field grammar cannot describe a field whose kind varies, so payload schemas for `l9.projection/architecture-intelligence@1` could not be synthesized.

## Bounded delta

Successor to v3.30.0 (ADR-027, Quantum-L9/.github#218, candidate), stacked on it; no file that v3.30.0 changes is touched here.

- `semantics/architecture_patterns.yaml`:
  - In `l9.pattern/reference-model-conformance@1`, the edge `conformance_runner compares [reference_model, candidate_implementation]` becomes two edges, `conformance_runner compares reference_model` and `conformance_runner compares candidate_implementation`.
  - In `l9.pattern/authority-candidate-admission@1`, the `lifecycle` state list moves under `lifecycle.stages`, the key `semantics/lifecycle.yaml` uses for an ordered state list. The states and their order are unchanged.
  - Both patterns keep their identifiers `@1`. `l9.pattern/dependency-package@1`, whose `lifecycle` RC-029 pins, is unchanged.
- ADR-028.

## Evidence

Candidate schema synthesis was run against `Quantum-L9/.github@9488d8f31a5ddbde8f1d3c3aaf57d17f21f62b88` with 23 candidate grammars (Quantum-L9/l9-semantic-compiler-engine#29). Drafting the 24th, for `architecture_patterns`, failed. An exhaustive scan of all 24 sources found exactly two mixed-kind fields, both in this ledger: `$.patterns[4].structure.edges[*].to` (`string` and `string_list`) and `$.patterns[*].lifecycle` (`object` and `string_list`). At this release the same scan finds none. This evidence motivates the candidate; it is not law.

## Outstanding Unknowns and findings

- No release check pins that a pattern field has one kind across patterns.
- Whether the two changes are of representation only (as ADR-028 holds), or material changes needing `@2` successors, is the owner's decision at admission.
- Schema synthesis for `architecture-intelligence@1` is still blocked in the compiler: projecting the profile's 45 `vocabulary` selections exceeds the candidate projection work budget. That is compiler work, outside this release.

## Authority

`Quantum-L9/.github` owns this ledger. This candidate does not admit itself, and it grants no producer, compiler or consumer any mutation, publication, merge, admission, deployment, or runtime authority.
