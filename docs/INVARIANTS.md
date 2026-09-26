# Governance invariants

Normative registry of the laws that govern how this repository interprets and
applies organization governance policy. Each law has a stable ID. IDs are never
renumbered or reused; a law that is retired keeps its row with a retired
status.

The decisions that create these laws are
[ADR-0001](./adr/0001-one-governance-brain.md) (one governance brain),
[ADR-0002](./adr/0002-versioned-governance-plan-compiler.md) (versioned
governance-plan compiler), and
[ADR-0003](./adr/0003-immutable-authority-binding.md) (immutable authority
binding).

`AC-*` identifiers name the acceptance proofs of campaign
`dotgithub-governance-compiler-v1`. **Status** records which slice makes the
law mechanically true: `Enforced (G1b)` is proven by a test in this repository
today; `Pending Gn` becomes enforced when slice Gn migrates its consumers;
`Review (every slice)` is held by architecture review of every campaign PR.

| ID | Law | Enforcement point | Proof | Status |
| --- | --- | --- | --- | --- |
| GOV-001 | `Quantum-L9/.github` is the single owner of organization governance policy interpretation. | Architecture review + code search | AC-ARCH-001 | Review (every slice) |
| GOV-002 | No workflow or script outside the compiler may independently resolve repo-class capability semantics after cutover. | Search gate | AC-ARCH-002 | Pending G5 |
| GOV-003 | `policies/repo-classes.yml` remains the repo-class capability SSOT. | Compiler tests | AC-CON-001 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-004 | The canonical compiler is `ops/compile-repo-governance.js`. | File contract | AC-CON-002 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-005 | Explicit malformed, unknown, prototype-named, or operator-contradicted class declarations fail closed and never widen to `default`. | Compiler and class tests | AC-ADV-001 — `ops/test-compile-repo-governance.js`, `ops/test-repo-class-profile.js` | Enforced (G1b) |
| GOV-006 | Class precedence remains marker > org override > default. | Existing + compiler tests | AC-REG-001 — `ops/test-repo-class-profile.js`, `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-007 | Default-class output remains backward compatible at this campaign boundary. | Golden parity | AC-REG-002 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-008 | `INHERIT` paths are not materialized by plan execution. | Compiler + integration tests | AC-BEH-001 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-009 | `FORBID` paths cannot appear in a valid materialization plan. | Compiler validation | AC-ADV-002 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-010 | A forbidden path present remotely is an attestation failure. | Targeted bootstrap | AC-INT-006 | Pending G5 |
| GOV-011 | `MATERIALIZE` writes only plan-declared entries and honors the plan write mode. | Seed adapters | ops/test-seed-plan-adapters.js; AC-BEH-002 | Enforced (G2) |
| GOV-012 | Manual filters may narrow execution but cannot widen the compiled plan. | Manual-seed / sync tests | ops/test-seed-plan-adapters.js, ops/test-sync-org-files.sh; AC-ADV-003 | Enforced (G2) |
| GOV-013 | Remote labels are applied only when enabled in the plan, and only from the exact plan label set. | Label adapters | ops/test-remote-apply-adapters.js; AC-BEH-003 | Enforced (G3) |
| GOV-014 | Remote settings are applied only from the fully resolved plan desired state. | Bootstrap / enforcement | ops/test-remote-apply-adapters.js; AC-BEH-004 | Enforced (G3) |
| GOV-015 | Effective mandatory-file waivers are identical across enforcement and reconciliation. | Compiler + workflow tests | AC-INT-003 | Pending G4 |
| GOV-016 | Drift repair cannot restore a file the effective class waives or forbids. | Continuous sync | AC-ADV-004 | Pending G4 |
| GOV-017 | Same authority SHA + same target identity and facts + same policy bytes yields a byte-identical canonical plan and digest. | Determinism test | AC-CON-003 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-018 | The plan digest excludes volatile run metadata. | Canonicalization test | AC-CON-004 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-019 | Every production plan names an exact 40-character authority SHA whose bytes — policy, templates, schema, and compiler code, including ignored files — produced it. | Schema + CLI provenance | AC-CON-005 — `ops/test-compile-repo-governance.js` (clean-clone CLI test) | Enforced (G1b) |
| GOV-020 | Targeted bootstrap refuses mutation on authority-SHA or plan-digest mismatch. | Workflow integration | AC-ADV-005 | Pending G5 |
| GOV-021 | One public targeted bootstrap entry point owns materialize + remote-apply + attestation orchestration after G5. | Workflow / Makefile contract | AC-ARCH-003 | Pending G5 |
| GOV-022 | Existing seed branch safety remains authoritative for branch mutation. | Regression test | ops/test-seed-workflow-branch-guard.js; AC-REG-003 | Enforced (G2) |
| GOV-023 | No compiler change may re-enable retired CI distribution. | Policy test + path search | AC-ADV-006 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-024 | This repository never becomes a code correctness, lint, test, scan, or remediation engine. | Boundary review ([`BOUNDARIES.md`](./BOUNDARIES.md)) | AC-ARCH-004 | Review (every slice) |
| GOV-025 | The compiler performs pure policy compilation from explicit facts; GitHub I/O belongs to adapters. | Module test / review | AC-ARCH-005 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-026 | Policy serialization changes must preserve parsed object semantics. | Before/after parity fixtures | AC-REG-004 — `ops/test-policy-serialization.js` (G1a) | Enforced (G1b) |
| GOV-027 | Materialization content entries are text-only, path-safe, relative, and carry a content SHA-256. | Schema / compiler tests | AC-ADV-007 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-028 | Plan consumers verify the schema before mutation. | Adapter tests | AC-ADV-008 | Pending G5 |
| GOV-029 | A plan is immutable transaction evidence, not a new durable policy database. | Architecture review | AC-ARCH-006 — `ops/test-compile-repo-governance.js` | Enforced (G1b) |
| GOV-030 | Open implementation discoveries do not authorize new governance owners or capability meanings. | Executor contract | AC-ARCH-007 | Review (every slice) |
