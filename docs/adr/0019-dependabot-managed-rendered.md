# ADR-0019: dependabot.yml is managed and rendered per repository root

## Status

Proposed

**Date:** 2026-10-15
**Deciders:** Quantum-L9 platform owners (merge of the PR that adds this record)
**Related:** CG-TOOLCHAIN-SSOT lane 3; Quantum-L9/l9-ci-core#212 (Core-owned
tools list, merged at `b5acce06a9f4439739f31435804671c571f44661`);
Quantum-L9/l9-ci-sdk#105 (SDK cedes tool selection, ADR 0017 there);
issue #132 (labels)

---

## Context and Problem Statement

`.github/dependabot.yml` was distributed as one verbatim file: github-actions
only, the same bytes for every repository. The seeders write it missing-only.
`continuous-sync.yml` restores it to those exact bytes when it drifts. Three
problems follow:

- A Preview or Apply in a repository that legitimately added `uv`, `pip` or
  `pre-commit` entries plans to delete them.
- Nothing stops a consumer's Dependabot from bumping the tool versions Core
  owns (`toolchain-lock.json`), or the Core, SDK and `.github` action pins
  that only Core or continuous-sync may move.
- The documents disagreed. `REPO_BIRTH_PROFILES.md` said "never overwritten".
  `DISTRIBUTION.md` described the restore to exact org bytes.

## Decision Drivers

- Tool versions are Core-owned: `l9-ci-core` `.l9/architecture.yaml`
  (`consumer_repository_may_not_own: central tool versions`) and
  `install-consumer-ci` ("Versions are not Dependabot-owned").
- Consumers do not select a Core or SDK revision: Core
  `.l9/release-plane.yaml` (`core_revision_selection_allowed: false`,
  `sdk_revision_selection_allowed: false`).
- One builder: the seeders, continuous-sync and the CLI must compare against
  and write the same bytes.
- Fail closed: an unreadable repository must never be planned as if it had
  no ecosystems.
- No consumer CI, governance pack or toolchain installer is distributed from
  this repository.

## Considered Options

1. **Keep the verbatim copy.** Every restore wipes legitimate ecosystems.
   Consumers keep bumping Core-owned tools.
2. **Seed missing-only, never restore.** No convergence. The ignores for
   Core-owned tools reach only newly born repositories.
3. **Managed and rendered (chosen).** Render from fragments, the repository's
   root shape and the vendored Core list. Seed missing-only, and restore
   through a manual continuous-sync.
4. **Fetch Core's list live at render time.** This adds a network dependency
   to every seed and Preview, and an unpinned input. Rejected in favour of a
   digest-pinned vendored copy.
5. **Number this record `ADR-019-*.md` and index it in `docs/adr/README.md`.**
   Rejected. `scripts/validate-semantics.py` SC-008 counts `ADR-*.md` against
   the Semantic Foundation release record (18 accepted ADRs), and the HASHES
   inventory covers `README.md`. Either change needs a Semantic Foundation
   release. This is a domain decision, so it uses the domain template's
   `NNNN-short-title.md` form.

## Decision Outcome

**Chosen option:** "Managed and rendered". It is the only option that keeps
consumers' legitimate ecosystems while enforcing Core ownership of tool
versions through the existing single builder.

- **Renderer:** `ops/render-dependabot.js`. The fragments are in
  `policies/dependabot/*.yml.tpl`. The output is deterministic: LF, one
  trailing newline, no timestamp or SHA.
- **Shape:** the repository root only, read at the pinned base. It produces:
  - `github-actions` always.
  - `uv` when `uv.lock` exists. The uv updater also rewrites plain root
    `requirements*.txt` pins, so `pip` is not added beside it.
  - Otherwise `pip`, when a root `requirements*.txt` or a PEP 621
    `pyproject.toml` (`[project]` table) exists.
  - `pre-commit` when `.pre-commit-config.yaml` exists.

  Nested manifests are out of scope.
- **Ignores:**
  - The `uv`, `pip` and `pre-commit` entries ignore exactly the names Core
    lists under that ecosystem in `core-owned-tools.json`. The list is
    vendored at `policies/vendor/l9-ci-core/core-owned-tools.json`. Its
    commit and sha256 are recorded in
    `policies/dependabot/core-owned-tools.source.json` and checked on every
    render.
  - `github-actions` ignores `Quantum-L9/l9-ci-core*`, `Quantum-L9/l9-ci-sdk*`
    and `Quantum-L9/.github*`.
- **Settings in every entry:** weekly on Monday, `open-pull-requests-limit: 2`,
  `chore(deps)` prefix, `cooldown.default-days: 7`, a minor/patch group, and no
  `labels`.
- **Mode:** MANAGED-RENDERED. The seeders write it missing-only.
  `continuous-sync.yml` restores it to the render for the repository's shape
  when it drifts. That workflow is manual-only: Preview by default, Apply only
  on an explicit `dry_run=false`.
- **Opt-out:** `.l9/no-sync` is the only opt-out. Exceptions in
  `policies/mandatory-files.yml` are not consulted by continuous-sync, as
  before.
- **Self-config:** `.github` runs its own render.
  `ops/test-render-dependabot.js` asserts `.github/dependabot.yml` equals the
  render for this repository's root.

### Consequences

- Good:
  - A restore converges a repository on the render for its own shape, so
    legitimate ecosystems survive.
  - Core-owned tools and Core/SDK/`.github` pins are no longer scheduled for
    bumps anywhere the file is managed.
- Bad:
  - A consumer's hand-tuned entries are replaced on Apply. The remedies are
    `.l9/no-sync` or a change to the fragments here.
  - Dependency names for `pre-commit` are the hook `repo:` URL exactly as
    written. A consumer writing a different URL spelling is not matched.
- Neutral:
  - Moving Core's list means a commit, a sha256 and new bytes in one change,
    the same discipline as `ops/governance-v1-pin.txt`.

## Links

- Fragments, renderer and tests: `policies/dependabot/`,
  `ops/render-dependabot.js`, `ops/test-render-dependabot.js`,
  `ops/fixtures/dependabot/`.
- Distribution modes: `docs/DISTRIBUTION.md`, `docs/REPO_BIRTH_PROFILES.md`,
  `docs/BOUNDARIES.md`.
- Dependabot evidence used for the keys and names (dependabot-core `main` and
  docs.github.com, 2026-10-15):
  - pre-commit dependency names are the hook `repo:` value (`file_parser.rb`).
  - `ignore` matching is a case-insensitive `*` glob (`update_config.rb`,
    `wildcard_matcher.rb`).
  - github-actions sub-path and reusable-workflow names start with
    `owner/repo`, so `owner/repo*` covers them.
  - `cooldown.default-days` takes 1–90. GitHub Actions and pre-commit support
    only `default-days`.
