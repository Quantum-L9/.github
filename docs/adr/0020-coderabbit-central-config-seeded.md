# ADR-0020: CodeRabbit config is rendered once, central, and seeded missing-only

## Status

Accepted

**Date:** 2026-11-11
**Deciders:** Quantum-L9 platform owners (merge of the PR that adds this record)
**Related:** ADR-0019 (`dependabot.yml` managed and rendered); cryptoxdog/IB-Odoo_19
PR #468 (the allowlist bug this prevents)

---

## Context and Problem Statement

CodeRabbit reviewed no files in cryptoxdog/IB-Odoo_19. Its `.coderabbit.yaml`
mixed include patterns with `!` exclusions in `reviews.path_filters`.
CodeRabbit's documented semantics
(docs.coderabbit.ai/configuration/path-instructions, "How path filters
combine") are:

- an exclusion (`!`) always wins;
- any pattern without `!` turns the list into an allowlist;
- "Use exclusions alone to keep other files eligible".

So one include pattern skipped every file it did not name. The same shape is
in other Quantum-L9 repositories (code search: Cognitive.Engine.Graphs,
Enrichment.Inference.Engine, IdeaOS, Mack-5.0, l9-observability-core,
l9-pr-repair, l9-repo-template).

CodeRabbit's central configuration
(docs.coderabbit.ai/configuration/central-configuration and
configuration-inheritance) lives in an org repository named `coderabbit`, with
`.coderabbit.yaml` at its root, and CodeRabbit installed on that repository.
It applies only to repositories without their own file, unless both files set
`inheritance: true`. With inheritance, lists merge repository entries first,
then append the unique central entries. An org-wide enforced override is
Enterprise-only; the organization is on the Free plan.

## Decision Drivers

- Make the allowlist bug unrepresentable in what the org distributes.
- One render: the central file, the seed and this repository's own copy are
  the same bytes, as with `dependabot.yml` (ADR-0019).
- Repositories legitimately carry their own `path_instructions`, tools and
  review settings. Distribution must not overwrite them.
- No Enterprise-only mechanism.

## Considered Options

1. **Central file only.** Reaches only repositories with no file of their own.
   Every repository that has one, or adds one later without
   `inheritance: true`, silently loses the shared exclusions.
2. **Managed seed (`MANAGED_SEED_PATHS`).** Every seed would replace a
   repository's `.coderabbit.yaml` with the org render, deleting its
   `path_instructions` and tool settings on each restore. The only remedy
   would be `.l9/no-sync`, which also drops the CODEOWNERS and dependabot
   restores. Rejected: the clobbering cost is real and recurring, and
   inheritance already delivers the shared part.
3. **Central file plus a missing-only seed (chosen).** The central file
   carries the shared exclusions. A repository without a file is seeded the
   same render, which sets `inheritance: true`, so later local additions still
   merge with the central list.

## Decision Outcome

**Chosen option:** "Central file plus a missing-only seed".

- **Renderer:** `ops/render-coderabbit.js`, the `ops/render-dependabot.js`
  discipline: pure, `fs` injected, repository-relative paths, LF with exactly
  one trailing newline, byte-identical on every runner, fail closed on a
  missing or malformed fragment, a `require.main` CLI.
- **Fragments:** `policies/coderabbit/header.yaml.tpl` and the named
  `policies/coderabbit/path-filters/*.txt` (one pattern per line; never a
  directory sweep).
- **Contract:** top-level `inheritance: true` (the header is refused without
  it); `reviews.path_filters` is exclusions only. A fragment pattern without a
  leading `!` throws, as does a duplicate, a pattern with whitespace, a
  double negation (`!!glob`, which a glob engine may read as an include) and a
  match-everything exclusion (`!**`, `!*`, `!**/*`), which would silence
  review entirely.
  Patterns use `**/` so they match at any depth. Tests and docs are never
  excluded.
- **Generic only:** the fragments carry only exclusions valid for any
  repository (installed dependencies, build output, caches, generated files,
  lockfiles, archives), each one depth-independent segment. No repository
  name or repository-specific path enters the renderer, the fragments or the
  central file; a repository's own exclusions go in its own
  `.coderabbit.yaml`, which `inheritance: true` merges with the central one.
  The test pins the exact reviewed set and the one-segment shape. Patterns are double-quoted because a bare leading `!` is a YAML
  tag.
- **Seed:** category `coderabbit` writes `.coderabbit.yaml` at the consumer
  root. It is in `DEFAULT_CATEGORIES` and in every class that materializes
  `dependabot` (`default`, `org_seeded_self_governed`,
  `non_constellation_python`); `self_governed` receives neither. It is not in
  `MANAGED_SEED_PATHS`: an existing file is kept, whatever its bytes, and
  `continuous-sync.yml` never restores it.
- **Central:** the render is the content of `Quantum-L9/coderabbit`
  `.coderabbit.yaml`. Creating that repository and installing CodeRabbit on it
  are operator steps.
- **Self-config:** this repository's `.coderabbit.yaml` is the render
  (`node ops/render-coderabbit.js > .coderabbit.yaml`).
  `ops/test-render-coderabbit.js` asserts the equality, the include-pattern
  refusal, validity against `https://coderabbit.ai/integrations/schema.v2.json`
  (vendored at `policies/vendor/coderabbit/schema.v2.json`, its sha256 pinned
  in `policies/coderabbit/schema.v2.source.json` and checked before python3
  `jsonschema` validates against it; no network access), and seed-payload
  inclusion.

### Consequences

- Good:
  - No org-distributed file can carry an include pattern.
  - New repositories born without a `.coderabbit.yaml` get the exclusions
    locally and from the central file.
  - Repository-specific review settings are never overwritten.
- Bad:
  - Existing `.coderabbit.yaml` files are untouched. Each must add
    `inheritance: true` (or be removed) to receive the central exclusions, and
    those with include patterns keep the allowlist bug until fixed in their
    own repositories.
  - Repositories born from `l9-repo-template` (class
    `non_constellation_python`) are not "new repositories without a file":
    the template ships its own `.coderabbit.yaml`, without
    `inheritance: true`. Every repository created from it keeps that file, is
    never seeded, and does not receive the central exclusions until
    `l9-repo-template`'s `.coderabbit.yaml` sets `inheritance: true` (or is
    removed). That template change is a cross-repository operator step,
    tracked with creating `Quantum-L9/coderabbit`.
  - The vendored schema can lag CodeRabbit's published one. It changes only by
    a reviewed refresh of the copy and its digest together, so an upstream
    schema change never turns the gate red for an unrelated pull request.
- Neutral:
  - A change to the exclusions reaches inheriting repositories when the new
    render is committed to `Quantum-L9/coderabbit`; seeded copies keep their
    bytes, and their own list is merged first, so the shared entries still
    append.
  - Removing an exclusion is not symmetric. A seeded copy is the full render
    at seed time and is never refreshed, and an exclusion always wins, so an
    exclusion deleted centrally stays in force in every repository seeded
    before the deletion. Retiring one org-wide also needs a change in each
    seeded repository's own `.coderabbit.yaml`.

## Links

- Renderer, fragments, test: `ops/render-coderabbit.js`, `policies/coderabbit/`,
  `ops/test-render-coderabbit.js`.
- Distribution: `docs/DISTRIBUTION.md`, `docs/REPO_BIRTH_PROFILES.md`,
  `docs/BOUNDARIES.md`.
- Numbered `NNNN-*.md`, not `ADR-*.md`, and not indexed in `docs/adr/README.md`,
  for the reason ADR-0019 option 5 records (SC-008 and the HASHES inventory).
