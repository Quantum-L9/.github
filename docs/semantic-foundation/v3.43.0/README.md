# Semantic Foundation v3.43.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.43.0 makes `semantics/repository_registry.yaml` organization-complete (ADR-040). Every repository the Quantum-L9 GitHub organization hosts, archived and forked ones included, must be registered; leaving one out is a violation, never an implied membership. Each entry remains an explicit admission decision with an explicit RepositoryClass. This is lane L1 of campaign L9-ORG-MEMORY-SSOT-01; ADR-040 is its candidate decision record and does not admit itself.

Successor to the v3.42.1 candidate (registration of `l9-state`).

## Bounded delta

- `semantics/repository_registry.yaml`: superseding global rules, the `organization_completeness` block, three downstream obligations, and 27 admitted repositories (26 `current`, `golden-repo` `retired` because GitHub reports it archived).
- `scripts/validate-semantics.py` RC-023: pinned census 33 → 60, pinned lifecycle for `golden-repo`, an id-folding check for every entry (`dot-github` grandfathered), the superseding rules and the completeness block pinned, organization-admitted entries checked by shape (`rc023_org_entry_problems`). RC-023-NEG grows from 70 to 99 cases.
- `ops/registry-completeness.js` and `.github/workflows/registry-completeness.yml`: the observational org-completeness check.
- `ops/register-org-repository.py`, `ops/org-admission.js` and the `admit` job in `.github/workflows/auto-seed-new-repo.yml`: a new repository's admission PR.
- ADR-040 (candidate).

## Membership is not constellation participation

A registry entry is organization membership only. It assigns no ProductKind, admits no Node and confers no participation in the constellation, which `Constellation.Gate` and `Gate_SDK` define (ADR-011, `semantics/product_kinds.yaml`).

## Downstream

The registry is the single list. Consumers re-project: `Quantum-L9/l9-graphiti-memory` (pinned corpus `9b27869`, 32 repositories) projects `l9.repository-view/memory-namespace-l9@1` into memory write grants, and `Quantum-L9/Cursor-Governance` (projection pinned at `496842b`, 33 repositories) refreshes its bundle. Neither keeps a list of its own.

## Outstanding Unknowns

- No organization webhook dispatches `repo_created` today, so a new repository's admission PR is opened when a birth dispatches it or an operator runs `auto-seed-new-repo.yml` with `target_repo`. The daily completeness check is the detector until then.
- Whether the org secret `GH_TOKEN` lists every private repository and can open a PR on `.github` is unverified here, as in ADR-039.

## Authority

`Quantum-L9/.github` owns this ledger. The organization listing and the `organization_admission` marker are evidence and confer no authority (L9-EVIDENCE-001). Nothing here grants mutation, publication, merge, admission, deployment or execution authority. Admission of v3.43.0 requires the repository owner's explicit decision for this exact subject.
