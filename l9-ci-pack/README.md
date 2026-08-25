# L9 CI instantiation pack (v2)

Everything a consumer repo — human or agent — needs to fully instantiate
`l9-ci-core` **v2**, without browsing the `l9-ci-core` repo itself. Source of
truth is `Quantum-L9/l9-ci-core`: `docs/templates/` (analysis + Python lint +
governance YAMLs) and `presets/typescript/` (locked Biome contract + Node
lint caller). This pack is the synced org distribution copy (see
`ops/sync-v2-starters.sh`). The org seeder copies these files into consumers
(missing-only). Agents must not invent `biome.json` or `ci.yml`.

**Default seed (seeder `all`):** codeowners, dependabot (github-actions
only), governance caller, community-health (`CODE_OF_CONDUCT.md`,
`CONTRIBUTING.md`, `SECURITY.md`), numbered issue templates +
`ci-failure` / `seed-ci-failure` / `gov-violation` / `config.yml`, human +
agent PR templates, this pack. **Dropped dests:** `LICENSE`,
`.github/FUNDING.yml`, `SUPPORT.md`, `.github/labels.yml` (org
`sync-labels-all`), `.github/workflows/on-org-update.yml`,
`bug_report.yml`, `feature_request.yml`. Python `l9-lint-test.yml` is
written only when the consumer has `pyproject.toml` or
`requirements.txt`. Opt-in categories: `labels`, `on-org-update`.

> **Canonical "how Core works / how to plug in" doc:**
> [`Quantum-L9/l9-ci-core/AGENTS.md`](https://github.com/Quantum-L9/l9-ci-core/blob/main/AGENTS.md).
> Read this README for the copy-paste path; read `AGENTS.md` when you need
> ownership rules, ordering guarantees, or pinning rationale.

## 1. What "fully active Core" means

- **Governance + analysis** (`governance/*.yaml` + `workflows/l9-analysis.yml`)
  is the part that **publishes GitHub checks** — this is the L9 finding
  pipeline (semgrep → SDK normalize/validate → publish).
- **Lint templates** (`workflows/l9-lint-test.yml` /
  `workflows/l9-lint-test-node.yml`) are **optional hygiene**. Python tool
  *versions* come from
  `Quantum-L9/l9-ci-core/.github/actions/install-consumer-ci@v2` (no version
  literals for those tools, no copied pin file) — you own the config, not the
  versions. Node/TS is **Biome** (SDK `l9-biome-scan.yml`) + tsc + the repo
  test script, on the SHA-pinned Biome caller. Core does not call or gate on
  these; you own the `env:` block and `enforce-biome` flip. Do not add ESLint
  or Prettier as a second JS/TS/JSON owner.
- **Formatter contract** (`biome.json`, `.biomeignore`, `.editorconfig`,
  `.vscode/extensions.json`) is the locked Biome 2.5.8 contract from
  `presets/typescript/`. The seeder and `stamp.sh` never overwrite an
  existing `biome.json`. Extra path excludes may only be appended to
  `files.includes`.

## 2. Prerequisites

- Pin Core at **`7148fc73dcbf41367f5c5401432dc997b1f4f869`** (the current
  verified candidate; will become `@v2.0.0` once released). **Never `@main`.**
- **Never** copy the legacy `@v1` kernel starters for new work — see §9.

## 3. Universal steps (both languages)

1. Copy `governance/*.yaml` (all six files) → your repo's
   `.github/governance/`.
   ⚠️ **Format gotcha:** these are JSON-in-`.yaml` — the resolver parses them
   with `json.loads`. Double-quoted keys, no comments, no trailing commas.
2. Copy `workflows/l9-analysis.yml` → `.github/workflows/l9-analysis.yml`.
3. The analysis caller stack-selects `--config` (`p/python` vs
   `p/javascript`+`p/typescript`). If `.github/governance/` is missing
   it fails with check `governance-pack-missing`.
4. Grant `checks: write` **only** on the job that calls Core's
   `publish-analysis.yml` (already scoped that way in the template — do not
   widen it).

## 4. Python path

1. Do §3 above with `--config p/python`.
2. Copy `workflows/l9-lint-test.yml` → `.github/workflows/l9-lint-test.yml`.
3. Tune the `env:` block: `PYTHON_VERSION`, `SOURCE_DIR`, `TEST_DIR`,
   `COVERAGE_THRESHOLD`.

## 5. Node / TypeScript path

1. Do §3 above with `--config p/javascript --config p/typescript`.
2. Copy the locked formatter contract if absent: `biome.json`,
   `.biomeignore`, `.editorconfig`, `.vscode/extensions.json`.
   **Do not invent `biome.json`.** Prefer the org seeder
   (`categories=l9-ci-pack`) or `l9-ci-core/presets/typescript/stamp.sh`.
3. Copy `workflows/l9-lint-test-node.yml` →
   `.github/workflows/l9-lint-test-node.yml`.
4. Tune only the `env:` block (`NODE_VERSION`, `PACKAGE_MANAGER`,
   `HAS_TYPESCRIPT`). Leave `enforce-biome: false` until the tree is clean.
5. Biome owns JS/TS/JSON. Do not keep `.eslintrc*` / `eslint.config.*` as a
   second format authority. `tsconfig.json` remains the type-check SSOT.

The seeder replaces two **stock** `l9-lint-test-node.yml` files with this
caller:

- the old ESLint pack (workflow name `L9 Lint and Test (Node)` + job
  `ESLint` + `npx eslint`)
- the Biome caller that ran `tsc` / `Test Suite` with
  `cache: ${{ env.PACKAGE_MANAGER }}` (hard-fails on repos with no Node
  lockfile; remediating from Cursor-Governance#276)

`typecheck` and `Node Test Suite` skip when there is no root
`package.json`. Biome still runs. Customized Node lint workflows are
kept. When a stock caller **is** replaced, the values you tuned in step 4
(`NODE_VERSION`, `PACKAGE_MANAGER`, `SOURCE_DIR`, `HAS_TYPESCRIPT`) are
carried into the upgraded file — the upgrade never reverts them to the
pack defaults.

## 6. Profile matrix

| Profile | Event | sdk_profile | Default mode | semgrep required |
|---|---|---|---|---|
| `pr_fast` | `pull_request` | ci_fast | blocking | yes |
| `merge` | `push` | ci_fast | blocking | yes |
| `nightly` | `schedule` | ci_deep | advisory | no |
| `release` | `push` | ci_deep | blocking | yes |
| `supply_chain` | `schedule` | ci_deep | blocking | yes |

## 7. Rollout: shadow → advisory → blocking

Start a new provider or a stricter policy in `shadow` (runs, artifacts
retained as promotion evidence, **no** GitHub check), then promote per
`governance/promotion-policy.yaml`: `disabled → shadow → advisory →
blocking`. Change the mode in `governance/rule-modes.yaml` (`defaults` or a
`provider_overrides` entry).

## 8. Verification checklist

- [ ] `l9-analysis.yml` run resolves governance without error.
- [ ] Analysis artifact set uploaded (`raw/`, `l9/`, `metadata/`).
- [ ] GitHub check published for `blocking`/`advisory` modes, **or** shadow
      evidence retained for `shadow` mode.
- [ ] Lint/test template green, if adopted.

## 9. Do not use for new work

The org's existing `@v1` kernel starters (`workflow-templates/l9-pr-pipeline.yml`,
`l9-security.yml`, `l9-scorecard.yml`, `l9-sbom.yml`, `l9-pre-commit.yml`,
`l9-nightly.yml`, `l9-release.yml`, `l9-governance.yml`,
`l9-node-ts-monorepo.yml`) are **Legacy (frozen `@v1`)** — kept only so
already-imported wrappers keep resolving against the historical `l9-ci-core`
kernels. New work always starts here, from `l9-ci-pack/`.

Scorecard / SBOM / Gitleaks / pre-commit / a dedicated nightly-release kernel
have **no v2 `workflow_call` equivalent** — the v2 SDK does not implement
those providers yet. Do not re-add them as Core reusable workflows without an
explicit, authorized scope change (see `l9-ci-core/AGENTS.md` §1, "frozen
seven").

## 10. Dormant SDK capability (documented, not wired)

`gate evaluate`, `providers list/detect`, and `semgrep detect` exist in the
pinned SDK but are **not** wired into Core's `invoke-sdk` allowlist yet — see
`l9-ci-core/AGENTS.md` §7 for the full list and rationale. Do not depend on
them from a consumer workflow.
