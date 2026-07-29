# AUDIT — Quantum-L9/.github findings and fixes

Evidence-based, per the Leverage kernel: confirmed facts are cited; everything else
is labeled UNKNOWN. Full API tree access was unavailable when this was compiled —
treat item ordering as leverage-ranked hypothesis, and re-verify against the live
repo before merging.

## Finding 1 — PR template at wrong path (leverage_score: 5, backbone_candidate)

**Confirmed**: `PULL_REQUEST_TEMPLATE.md` is at repo root
(github.com/Quantum-L9/.github/blob/main/PULL_REQUEST_TEMPLATE.md), not at
`.github/pull_request_template.md` inside the `.github` folder.

**Why it matters**: GitHub only serves org-wide default PR templates from the
nested path. A root-level file may render for the `.github` repo's own PRs but does
**not** propagate to the other ~28 repos in the org. Every PR across the
constellation is currently missing whatever governance this template intended to
enforce.

**Fix shipped**: `.github/pull_request_template.md` at the correct nested path,
carrying forward Problem/Risk/Evidence/Gates structure consistent with the
`pr-template-kit` already delivered in this thread.

**Future acceleration**: every repo's next PR inherits governance with zero
per-repo setup. **Existing amplification**: repos with no local override
immediately gain structure they previously lacked.

## Finding 2 — No canonical CODEOWNERS (leverage_score: 4.5)

**Confirmed**: no CODEOWNERS file surfaced in any search across the org's public
surface. **Inference, not confirmed**: this likely means zero automatic reviewer
assignment org-wide — UNKNOWN whether a private/undiscovered copy exists per repo.

**Why it matters**: without CODEOWNERS, review routing is tribal knowledge, which
is exactly the "unclear ownership" friction pattern your own framework flags in
`pass_4_canonicalization`.

**Fix shipped**: `.github/CODEOWNERS` with placeholder team slugs
(`@Quantum-L9/maintainers`, `governance`, `infra`, `ci-cd`, `security`) — **these
slugs are UNKNOWN and must be confirmed against actual GitHub org teams before
merge**, or CODEOWNERS silently fails validation.

## Finding 3 — SECURITY.md duplicated per repo (leverage_score: 4)

**Confirmed**: `SECURITY.md` found on `Quantum-L9/Cursor-Governance`, containing
org-wide-scoped policy language ("applies to all repositories in the Quantum-L9
... organization") — meaning the same text is likely copy-pasted per repo rather
than inherited from one canonical source.

**Why it matters**: 29 near-identical copies is the "duplicated concepts /
scattered configs" pattern — a single edit (e.g. disclosure window change) requires
N manual edits and inevitably drifts.

**Fix shipped**: canonical `SECURITY.md` in `.github` (this repo). Note: unlike PR
templates, `SECURITY.md` in `.github` **does** auto-serve as the org-wide fallback
security policy shown on every repo's Security tab that lacks its own — this is a
genuine one-shot canonicalization, no distribution mechanism needed.

## Finding 4 — CONTRIBUTING.md is a manual, non-idempotent clone step
(leverage_score: 4)

**Confirmed**: current instructions are "clone Cursor-Governance alongside your
target repo" as a 3-step manual process.

**Why it matters**: this is human-executed setup friction repeated per repo, per
contributor, per machine — the opposite of a reusable primitive, and it has no
CI-verifiable outcome.

**Fix shipped**: `CONTRIBUTING.md` rewritten around `scripts/bootstrap.sh`, a
single idempotent command replacing the manual clone. **Note**: `bootstrap.sh`
ships as a starter — it currently only reports what it would do; wiring it to your
actual governance-hook installation is the next concrete step, flagged rather than
faked.

## Finding 5 — No cross-repo distribution mechanism (leverage_score: 5,
constellation multiplier)

**Confirmed by structural necessity, not direct evidence**: templates
(`pull_request_template.md`, issue forms, `SECURITY.md`) auto-propagate from
`.github`. **Workflows do not.** With 29 repos, any workflow fix made only in
`.github` has zero effect elsewhere until distributed.

**Fix shipped**: `.github/workflows/distribute-defaults.yml` — an org-fan-out
workflow enumerating all non-archived repos via the Org Repos API. **Shipped as
dry-run intentionally**: it lists distribution targets in the job summary but does
not yet open PRs, since that requires an `ORG_DISTRIBUTION_TOKEN` with
`repo:write` scope across 29 repos — a decision your governance owner should make
explicitly, not one this kit should make silently.

## What was NOT fixed (per "what_not_to_do_yet")

- **Issue forms** — UNKNOWN whether `ISSUE_TEMPLATE/` exists in this repo. Not
  touched here to avoid overwriting an unverified asset; use the
  `issue-template-kit` delivered earlier in this thread once presence is confirmed.
- **CODEOWNERS team slugs** — shipped as placeholders on purpose. Guessing real
  team names risks silently misrouting review requests, which is a worse outcome
  than an admittedly-fake placeholder.
- **Wiring `distribute-defaults.yml` to actually open PRs** — deferred until token
  scope is a deliberate governance decision, not a default in a starter kit.

## Verification steps once merged

```bash
gh api repos/Quantum-L9/.github/contents/.github/pull_request_template.md
gh api repos/Quantum-L9/.github/contents/.github/CODEOWNERS
gh repo view Quantum-L9/some-other-repo --json securityPolicyUrl
```


---

# REVISION — v2.0.0

Finding 5 was re-architected after verifying GitHub's inheritance model.

**What changed**: v1 proposed `distribute-defaults.yml`, a recurring fan-out pushing
files to 29 repos. That was wrong. It would have required standing write access to
the whole org, forever, to solve a problem inheritance and `workflow_call` already
solve with no credentials.

**Corrected**: community health files inherit live from this repo's `main`.
Workflow logic is consumed by reference via `workflow_call` at `@v1`. Only
`CODEOWNERS` and a 12-line caller are physically copied, once, by
`seed-governance.yml`.

**Impact on findings 1, 3, 4**: they were never token-blocked. They go live the
moment this merges.


---

# PATCH — v2.0.1

Self-audit of v2.0.0 found three items described in review but absent from the pack.
All three are now shipped.

1. **Literal tag commands** — `docs/DISTRIBUTION.md` step 4 described moving the
   `v1` tag but gave no runnable commands. Added immutable-tag-plus-moving-alias
   commands, and the warning to force-move `v1` rather than delete it (deletion
   breaks every caller until it reappears).

2. **`secrets: inherit`** — absent entirely. Called workflows do not receive caller
   secrets automatically. Harmless today since both callees use only the automatic
   `GITHUB_TOKEN`, but the failure mode is silent (empty string, confusing auth error
   at point of use). Now documented in `docs/DISTRIBUTION.md` Appendix A and as a
   commented line in `templates/governance-caller.yml`.

3. **Actions access policy** — the highest-consequence gap. A consumer repo with
   Actions disabled, or `allowed_actions: local_only`, fails a cross-repo
   `workflow_call` before any step executes, with an error that does not indicate the
   cause. Now Appendix B, plus `preflight.sh` section 5, which classifies every repo
   as OK / LOCAL_ONLY / DISABLED / allow-list before seeding.

**Assessment**: items 1 and 2 were documentation debt. Item 3 was a genuine rollout
trap — it would have surfaced as a batch of confusing red X's across seeded repos
with no obvious cause. Caught pre-deploy.
