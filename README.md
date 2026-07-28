# Quantum-L9 — org defaults & governance

Canonical, inheritance-first governance for the Quantum-L9 constellation.

## Status of the five findings

| # | Finding | Fix | Propagation | Token |
| --- | --- | --- | --- | --- |
| 1 | PR template was at repo root, so it never propagated | `.github/pull_request_template.md` | Inherited | No |
| 2 | No canonical CODEOWNERS | `.github/CODEOWNERS` + `templates/CODEOWNERS.repo` | Seeded once | Yes |
| 3 | SECURITY.md duplicated per repo | canonical `SECURITY.md` | Inherited | No |
| 4 | CONTRIBUTING.md was a manual clone step | rewritten + `scripts/bootstrap.sh` | Inherited | No |
| 5 | No cross-repo mechanism | `workflow_call` callees + 12-line caller | By reference | No |

Four of five need **no credentials at all**. See `docs/DISTRIBUTION.md`.

## Layout

```
.github/
├── pull_request_template.md        # inherited org-wide  ← finding 1
├── CODEOWNERS                      # governs THIS repo   ← finding 2
└── workflows/
    ├── governance-pr.yml           # workflow_call callee ← finding 5
    ├── governance-issue.yml        # workflow_call callee
    └── seed-governance.yml         # dispatch-only, seeds the 2 non-inheritable files
templates/
├── CODEOWNERS.repo                 # copied into each repo
└── governance-caller.yml           # 12-line caller, pinned @v1
SECURITY.md                         # inherited org-wide  ← finding 3
CONTRIBUTING.md                     # inherited org-wide  ← finding 4
docs/
├── AUDIT.md                        # findings + evidence
└── DISTRIBUTION.md                 # what the token does and does not block
scripts/
├── preflight.sh                    # read-only verification, run first
└── bootstrap.sh
```

## Before you merge

```bash
./scripts/preflight.sh
```

It checks that every `@Quantum-L9/<team>` slug in CODEOWNERS actually exists (an
unresolvable owner makes the rule silently inert), that this repo is public, and
which repos have local overrides that block inheritance.

## Preflight coverage

`./scripts/preflight.sh` is read-only and checks five things:

1. Every `@Quantum-L9/<team>` slug in CODEOWNERS resolves to a real org team — an
   unresolvable owner makes the rule silently inert.
2. This repo is public, without which nothing inherits.
3. Which repos already have `CODEOWNERS` / the governance caller (seed idempotency).
4. Which repos hold local overrides that block inheritance.
5. **Actions policy per repo** — a `local_only` or disabled-Actions repo will fail a
   cross-repo `workflow_call` before any step runs. See `docs/DISTRIBUTION.md`
   Appendix B.

## Placeholders — resolved at integration

The pack shipped with unverified placeholder slugs (`@Quantum-L9/maintainers`,
`governance`, `infra`, `ci-cd`, `security`). At integration time the live org was
queried (`gh api orgs/Quantum-L9/teams`): only **`platform`** exists. All CODEOWNERS
rules in `templates/CODEOWNERS.repo` now use `@Quantum-L9/platform` (+ `@cryptoxdog`
on blast-radius paths), matching this repo's existing `.github/CODEOWNERS`.

## Integration notes (v2.0.1 → live repo)

- `.github/CODEOWNERS` — the repo already had a canonical copy with real teams;
  the pack's placeholder version was **not** installed over it.
- `.github/pull_request_template.md` — owned by PR #15 (pr-template-kit), which
  ships a superset of the pack's template (adds *Changes by intent* + the
  `pr-files.yml` bot). Finding 1's fix (nested path) is satisfied there.
- `ISSUE_TEMPLATE/` — owned by PR #16 (issue-template-kit), per the pack's own
  "what not to do yet" guidance.
- `SECURITY.md` / `CONTRIBUTING.md` — merged: existing detail retained, pack's
  canonical-single-source clause, disclosure timeline, and bootstrap-first setup added.
