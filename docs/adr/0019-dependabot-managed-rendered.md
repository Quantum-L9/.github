# ADR-0019: dependabot.yml is managed and rendered per repository root

## Status

Accepted (revised 2026-11-03: automated weekly seed and restore, npm;
revised 2026-11-05: weekly sweep paused, every manual seed restores, and
`.github/CODEOWNERS` joins the managed seed paths;
revised 2026-11-11: safe-only, every ecosystem ignores semver-major bumps;
revised 2026-11-11: dependency-lane decision recorded, with no App or secret,
and posture unchanged until the lane ships)

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
   root shape and the vendored Core list. Distribute it as a seed file like
   the templates, and keep it in sync automatically through the weekly sweep.
4. **Fetch Core's list live at render time.** This adds a network dependency
   to every seed and Preview, and an unpinned input. Rejected in favour of a
   digest-pinned vendored copy.
5. **Number this record `ADR-019-*.md` and index it in `docs/adr/README.md`.**
   Rejected. `scripts/validate-semantics.py` SC-008 counts `ADR-*.md` against
   the Semantic Foundation release record (18 accepted ADRs), and the HASHES
   inventory covers `README.md`. Either change needs a Semantic Foundation
   release. This is a domain decision, so it uses the domain template's
   `NNNN-short-title.md` form.
6. **A per-repository overlay merged into the render (revision 2026-11-11,
   considered for the dependency lane).** This would be a consumer file such as
   `.l9/dependabot.overlay.yaml` adding ignores and groups to the managed
   bytes. Rejected:
   - Its one candidate consumer, `l9-meta-injector`, kept a hand-written file
     to group updates so that one maintainer rebind covered a whole group
     (its ADR-056). Its ADR-093 retired the committed per-PR evidence that
     needed rebinding.
   - The safe-only revision above already ignores the majors that file held
     back.
   - An overlay would make every render depend on an extra consumer read, for
     no consumer that needs it. A rule every repository needs is a fragment
     change here, as Consequences already says.

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
  - `npm` when a root `package.json` exists.

  Nested manifests are out of scope.
- **Ignores:**
  - The `uv`, `pip`, `npm` and `pre-commit` entries ignore exactly the names Core
    lists under that ecosystem in `core-owned-tools.json`. The list is
    vendored at `policies/vendor/l9-ci-core/core-owned-tools.json`. Its
    commit and sha256 are recorded in
    `policies/dependabot/core-owned-tools.source.json` and checked on every
    render.
  - `github-actions` ignores `Quantum-L9/l9-ci-core*`, `Quantum-L9/l9-ci-sdk*`
    and `Quantum-L9/.github*`.
  - **Safe-only (revision 2026-11-11, operator decision):** every ecosystem's
    ignore list ends with `dependency-name: "*"` and
    `update-types: ["version-update:semver-major"]`, so Dependabot proposes
    only minor and patch bumps. A major is a deliberate upgrade with a code
    review, not a weekly PR: Quantum-L9/Cognitive.Engine.Graphs#429 (openai
    1.x → 3.46.0) and #431 (actions/github-script 8 → 9) are the cases that
    prompted it. Dependabot applies `ignore` to security updates too, so a
    vulnerability fixed only in a new major surfaces as a Dependabot alert,
    not a PR; alerts are unaffected.
- **Settings in every entry:** weekly on Monday, `open-pull-requests-limit: 2`,
  `chore(deps)` prefix, `cooldown.default-days: 7`, a minor/patch group, and no
  `labels`.
- **Mode:** MANAGED-RENDERED. It is a seed file (`MANAGED_SEED_PATHS` in
  `ops/build-seed-payload.js`). Every seed entrypoint (`seed-governance.yml`,
  `auto-seed-new-repo.yml`, `ops/sync-org-files.sh`) adds the file when
  missing and restores it when it differs from the render for the repository's
  shape, in one advisory PR per repository. Every other seed path stays
  missing-only, except `.github/CODEOWNERS`, the other managed seed path, and
  nothing merges without review. `continuous-sync.yml` remains the manual,
  on-demand restore (Preview by default, Apply only on an explicit
  `dry_run=false`).
- **Schedule (revision 2026-11-05):** the weekly `auto-seed-new-repo.yml`
  sweep (Monday 08:00 America/New_York, operator decision 2026-11-03) is
  paused by operator decision 2026-11-05. Seeding, and so restoration, runs
  only when dispatched until a seed PR is proven green and complete; the
  `schedule:` block stays in the workflow, commented, to re-enable. Until then
  a drifted render is restored by dispatching `seed-governance.yml`,
  `auto-seed-new-repo.yml` or `continuous-sync.yml`, never automatically.
- **CODEOWNERS (revision 2026-11-05):** `.github/CODEOWNERS` is the second
  managed seed path: the exact `policies/CODEOWNERS` bytes, seeded into every
  class, `self_governed` included, and restored when it differs, whether or
  not the repository carries a root `CODEOWNERS` (GitHub reads
  `.github/CODEOWNERS` first). The root file is never written.
- **Opt-out:** `.l9/no-sync` is the only opt-out. It keeps every seed
  missing-only for the managed files and makes continuous-sync skip the
  repository. Exceptions in
  `policies/mandatory-files.yml` are not consulted by continuous-sync, as
  before.
- **Dependency lane (revision 2026-11-11, operator decision; not yet
  implemented):** Dependabot pull requests become auto-merge eligible through a
  dependency lane owned by Core (`Quantum-L9/l9-ci-core`). A consumer adds no
  workflow and selects no Core revision.
  - **Eligibility:** semver-minor and semver-patch version updates to
    development dependencies, and security updates, after this render's 7-day
    cooldown. Runtime dependencies stay advisory until the lane has one month
    of clean history. Majors are never eligible; they are already ignored
    above.
  - **Gate:** the organization's required checks decide the merge. The lane
    only enables auto-merge. It never pushes a commit to a Dependabot branch:
    a branch that needs regenerated committed output fails its checks and
    waits for a maintainer.
  - **Credential: none beyond the built-in token.** The lane runs on the
    Dependabot pull request with the workflow's own `GITHUB_TOKEN`, raised to
    `contents: write` and `pull-requests: write`, and checks out no pull
    request code. It needs no GitHub App, organization secret or personal
    access token. A dedicated App was considered so the lane could push
    regenerated output; a push made with `GITHUB_TOKEN` starts no checks. It
    was rejected (operator decision 2026-11-11): with no per-PR generated
    evidence committed, what would still need regenerating is too rare to
    justify a credential.
  - **Enrollment:** `policies/repo-settings.yml` sets
    `allow_auto_merge: false` org-wide, and `enforce-policies.yml` restores it
    weekly. A repository joins the lane through an `allow_auto_merge: true`
    override there, applied through the API by that workflow and never by
    hand, in the same change that ships the lane.
  - **Posture until it ships:** the rendered header keeps `ADVISORY POSTURE`
    and nothing auto-merges. The header changes in the same change that ships
    the lane, so the render never promises behaviour that nothing performs.
- **Self-config:** `.github` runs its own render.
  `ops/test-render-dependabot.js` asserts `.github/dependabot.yml` equals the
  render for this repository's root.

### Consequences

- Good:
  - Every materializing repository converges on the render for its own shape
    without an operator run, and legitimate ecosystems survive.
  - Core-owned tools and Core/SDK/`.github` pins are no longer scheduled for
    bumps anywhere the file is managed.
- Bad:
  - A consumer's hand-tuned entries are proposed for replacement every week
    until the restore PR merges or the repository opts out. The remedies are
    `.l9/no-sync` or a change to the fragments here.
  - A weekly sweep is a slower backstop than the retired hourly one. Birth is
    unaffected: after its attestation `repo-birth-bootstrap.yml` dispatches
    `repo_created` for the newborn, so its seed PR opens immediately.
  - Dependency names for `pre-commit` are the hook `repo:` URL exactly as
    written. A consumer writing a different URL spelling is not matched.
- Neutral:
  - Moving Core's list means a commit, a sha256 and new bytes in one change,
    the same discipline as `ops/governance-v1-pin.txt`.
  - The dependency-lane revision changes no rendered byte and no fixture. It is
    the authority the Core lane will cite. Until that lane exists, every
    Dependabot pull request remains advisory.

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
