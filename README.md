# Quantum-L9/.github

`semantics/` is the Semantic Foundation v3.5.0. This repository owns that
language for the organization. A domain repository owns the meaning of its own
capability. Do not copy this tree into a product repository. Cite the ledger's
`artifact_id`.

The release record is [`docs/semantic-foundation/v3.5.0/`](docs/semantic-foundation/v3.5.0/README.md).
The decisions are ADR-001 through ADR-012 in [`docs/adr/`](docs/adr/README.md).
Agent instructions for the language are [`AGENTS.md`](AGENTS.md).

**ProductTopology** is the product contract
(`semantics/product_topology.schema.yaml`). **ProductManifest** is the derived
realization of one topology (`semantics/product_manifest.schema.yaml`). A
manifest records what was resolved. It cannot rewrite its topology. The
compiler carries out decisions recorded in these ledgers
(`semantics/compiler_contract.yaml`). It does not invent product meaning.

## What a product declares

v3.5.0 admits two ProductKinds in `semantics/product_kinds.yaml`. Kind follows
consumption and deployment. It is not inferred from repository shape, package
format, provider, complexity, or the presence of a process.

| Kind | Consumption | Deployment |
| --- | --- | --- |
| Node | remote invocation | independent runtime |
| Dependency | installed, composed inside the consumer | consumer-bound |

SDK is not an admitted kind. Archetypes specialize a kind without redefining
it: `semantics/node_archetypes.yaml` and
`semantics/dependency_archetypes.yaml`.

Identity dimensions stay distinct in `semantics/identity_model.yaml`.
GovernanceProfile selects policy. ActorIdentity names who acted. Downstream
work consumes an assertion that matches
`semantics/identity_assertion.schema.yaml`.

Architecture patterns in `semantics/architecture_patterns.yaml` are composable
obligations. A pattern is not a complete architecture, and it does not create
semantic ownership. Provider identity does not define pattern identity.

```text
ProductTopology
    -> ProductKind + archetype
    -> requirement and capability closure
    -> architecture patterns, ports, adapters
    -> technology bindings
    -> conformance closure
    -> ProductManifest
    -> implementation IR
    -> target artifacts
    -> admission evidence
```

A downstream repository references these coordinates, declares its own
topology, and lets the semantic compiler derive what the profiles allow. The
direction is `.github` semantic authority, then product-owned topology, then
derived realization, then implementation.

Add a ledger here only when it retires a decision that would otherwise be
remade in every product ([ADR-010](docs/adr/ADR-010-ownership-boundaries-no-recipes.md)).
Register it in `semantics/canonical_sources.yaml`. Leave a material Unknown
explicit.

## Organization plane

The same repository still runs organization governance, control, and
distribution. That plane reports and remediates. It does not decide whether
code is correct, and it does not block a merge or a push until a control is
explicitly promoted. [`docs/BOUNDARIES.md`](docs/BOUNDARIES.md) is the scope
constraint. [`docs/ADVISORY.md`](docs/ADVISORY.md) is the promotion ladder.
[`docs/DISTRIBUTION.md`](docs/DISTRIBUTION.md) is how files reach other
repositories. [`docs/REPO_BIRTH_PROFILES.md`](docs/REPO_BIRTH_PROFILES.md) is
INHERIT, MATERIALIZE, REMOTE APPLY, and FORBID.

Canonical CI is `Quantum-L9/l9-ci-core` (`org-ci.yml`).

| Capability | Implementation | Mode |
| --- | --- | --- |
| Org rulesets | `rulesets/*.json` | `evaluate` |
| Governance seeding | `auto-seed-new-repo.yml` | PR, class-aware |
| Label sync | `sync-labels-all.yml` | additive |
| Drift remediation | `continuous-sync.yml` | PR |
| Policy enforcement | `enforce-policies.yml` | settings correction |
| SHA-pin audit | `audit-pins-org.yml` | report |
| Preflight | `preflight-scheduled.yml` | report |
| Template dispatch | `dispatch-template-update.yml` | event |
| Birth bootstrap | `repo-birth-bootstrap.yml` | REMOTE APPLY for one repo |
| Copilot governance | `.github/copilot-instructions.md` | advisory |
| Custom properties | `ops/properties-schema.json` | metadata |

Seeding is capability-scoped. A consumer declares its class in
`.l9/org-birth-profile.yaml`. `policies/repo-classes.yml` decides what that
class receives. An absent marker resolves to `default`. A FORBID hit throws.

| Marker | Effect |
| --- | --- |
| `.l9/no-sync` | Drift remediation skips the repo |
| `.l9/no-policy-enforcement` | Policy enforcement skips the repo |

`ops/activate-all.sh` refuses to set anything above `evaluate`.

## Layout

```text
semantics/          Semantic Foundation v3.5.0 — the language this repo owns
docs/adr/           ADR-001 … ADR-012
docs/semantic-foundation/v3.5.0/   release record
policies/           repo classes, settings, mandatory files, consumer CODEOWNERS, governance caller
rulesets/           org rulesets, evaluate only
ops/                activation, seed payload, birth, pin audit
.github/workflows/  organization-plane agents
```
