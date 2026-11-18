# L9 Operator Doctrine + Strategic Intent + Alignment | v1.0.0 admission handoff

**Decision:** The operator approved the predecessor v0.6.1 content for admission and authorized this v1 packaging. The *only* repository payload is `repo-overlay/`. It contains the operator-owned v1 Doctrine, v1 Intent, one operator-scoped selection profile, five role views including a restricted Coding Agent view, one local consumer-binding catalog, and a precise operator adoption/subject record. **No GitHub write has been performed.**

## What to push to `Quantum-L9/.github`

Copy **only the contents of** `repo-overlay/` into the root of the private `.github` checkout on a new branch. Paths begin `strategy/`. Do not copy `support/` as sources of truth. Review and push under the repository's governed publication path, then merge only with its normal acceptance checks. The authoritative records are the two YAMLs under `strategy/`. The three YAMLs under `strategy/alignment/` are *operator-scoped candidate-to-consumer design sources*, not new global `semantics/` ledgers and not operational access controls.

### Exact v1 source files

- `strategy/OPERATOR_DOCTRINE.yaml`
- `strategy/operator_strategic_intent.yaml`
- `strategy/alignment/operator_alignment.profile.yaml`
- `strategy/alignment/agent_views.yaml`
- `strategy/alignment/consumer_bindings.yaml`

`strategy/OPERATOR_RELEASE_MANIFEST.json` binds their SHA-256 content, and `strategy/ADMISSION.md` states the operator decision, precedence, activation limits, and frozen `.github` authority observations.

## Critical identity distinctions

- **Approved:** v0.6.1 exact predecessor (SHA-256 `43ff7370dc9e4f126b6f914babb57990efdc20a927569cff5b0ea91908d04c78`) as the subject; authorized source version normalization to v1.0.0 and repository preparation.
- **Retained as proposed:** five additional non-selected Doctrine Core Values. Their listing is not adoption.
- **Still not executed:** producer integration for operator-owned sources, live `/lcto`/`/architect`/`/planner`/Meta Planner bindings, coding-agent ACL isolation, real agent behavioral scenarios, GitHub push/merge, Memory cutover.
- **Not within this admission:** modifications to `.github/semantics/`, registered domain profiles, compiler laws, provider permissions, Plan Graph, or an extra graph writer.

## Local verification

From the extracted ZIP root, run `python support/tools/validate_v1.py`. It performs read-only source hashes, Doctrine-to-Intent revision closure, privileged selection allowlists, Coding Agent restricted-view assertions, generator determinism, predecessor semantic-preservation comparisons and negative test probes. This is **package admission readiness**, not runtime, producer, target CI or independent historical-source certification.

`support/evidence/` contains the original unchanged v0.6.1 ZIP and revision map; `support/tests/` retains all 55 existing behavioral scenario *specifications*.

## What happens after your push

1. Re-run local checks against the exact branch contents. Recheck the `.github` main revision, repository admission and publication controls. If the chosen adoption path is a PR, the formal decision should reference the exact file-set digest from the release manifest.
2. The accepted repository revision becomes the private operator-owned *source*; consumers still must verify applicability and authorization, rather than fetching Doctrine directly by default.
3. Separately implement and verify operator-source views and host ACLs, then activate one consumer at a time. The actual compiler and runtime proofs are **not** part of this ZIP.

**Note:** The global `l9-projection-admission` skill targets additions to `.github/semantics/` and a Semantic Foundation release. Using that procedure here would wrongly globalize personal operator content. This v1 package is designed for private, operator-owned `strategy/` admission instead.
