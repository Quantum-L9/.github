# Repo birth profiles

**Authority for what the organization requires.** How a repository is *born* is
owned by `Quantum-L9/l9-repo-template` (`make new-repo`). This repository owns
what the organization applies to it.

## The distinction that makes this work

The organization does not copy every `.github` file into every repository. It
applies every capability that is applicable to that repository's class.

| Mode | Meaning | Example |
| --- | --- | --- |
| **INHERIT** | GitHub supplies it from `Quantum-L9/.github`. The repository must not carry a copy. | `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md` |
| **MATERIALIZE** | The repository must contain the file. Seeded missing-only. | `.github/CODEOWNERS`, `.github/dependabot.yml`, `.github/labels.yml` |
| **REMOTE APPLY** | GitHub API state, not a file. | labels, repository settings |
| **FORBID** | The repository must never carry this path. A payload that would write one throws. | `.github/workflows/l9-analysis.yml`, `.github/workflows/governance.yml` |

## Why FORBID exists

`l9-repo-template` fails closed on repo-local organization CI distribution.
`scripts/inventory_check.py` `DENY_CI_DISTRIBUTION` names
`.github/workflows/l9-analysis.yml`, `l9-lint-test.yml`, `on-org-update.yml`,
`governance.yml`, and `.github/governance/`. Organization CI targeting belongs
to `l9-ci-core`, not to the repository.

The copy-first seed category `on-org-update` is retired and throws in
`ops/build-seed-payload.js`. Governed classes still list those
destinations under `forbid`, so a payload that names one fails in
`ops/repo-class-profile.js` even if a category regression tried to write it.

## The contract

`policies/repo-classes.yml` (JSON-in-YAML, so Node reads it without `js-yaml`
and Python reads it with either `json.loads` or `yaml.safe_load`).

A repository declares its own class in `.l9/org-birth-profile.yaml`:

```yaml
schema: l9.org-birth-profile-marker/v1
profile: non_constellation_python
authority: Quantum-L9/.github
```

The organization honours what the repository declares. An absent marker
resolves through `overrides`, then `default_class`. It never resolves to
something wider than the repository asked for.

## Classes

Path lists live in `policies/repo-classes.yml`. Every class remote-applies
labels and repository settings.

| Class | For | Materialize (`seed_categories`) | Inherit | Forbid |
| --- | --- | --- | --- | --- |
| `default` | No marker and no override | `codeowners`, `dependabot`, `governance`, `community-health`, `issue-templates`, `pr-templates` | nothing | nothing |
| `non_constellation_python` | `l9-repo-template` offspring | `codeowners`, `dependabot`, `labels` | `CODE_OF_CONDUCT.md`, `FUNDING.yml`, issue templates, PR templates | org CI distribution paths, the governance caller, retired CI pin files |
| `self_governed` | `l9-ci-core`, `l9-meta-injector` | nothing | community-health files, `FUNDING.yml`, issue templates, PR templates | org CI distribution paths and the governance caller |

`default` reproduces `DEFAULT_CATEGORIES` in `ops/build-seed-payload.js`.
`ops/test-repo-class-profile.js` asserts that. Adding a class is how behavior
changes. Editing `default` is not.

`labels` is opt-in for `default` and materialized for
`non_constellation_python`. `.github/labels.yml` is required by
`l9-repo-template` and not part of the org-wide default seed. The class
decides.

### Assigning a class without a commit in the repo

`overrides` in `policies/repo-classes.yml` maps a repository name to a class.
Precedence is **marker > overrides > default_class**. A repository's own
declaration wins. `overrides` classifies a repository that has not declared
one yet. An override naming an undefined class fails at policy load.

### An explicit declaration fails closed

| Marker state | Result |
| --- | --- |
| absent | override, else `default_class` |
| present, known class | that class |
| present, unparseable | **ERROR — skipped and reported. Never `default`.** |
| present, unknown class | **ERROR — skipped and reported. Never `default`.** |

`default` is the widest payload, so falling back to it on a malformed marker
turns a typo into a broad seed. An explicit declaration that cannot be honored
is a fault to fix.

Absence is not malformation. A repository that never declared a class has made
no statement to contradict, so the override map and then the default apply.

The seeder probes the marker's existence before reading it. A failed fetch and
an absent file are otherwise indistinguishable, and treating a transient fetch
error as absent is the same fail-open. `auto-seed-new-repo.yml` and
`enforce-policies.yml` both probe first. Only a genuinely absent marker reaches
the override and default path.

## Consumers

| Surface | Uses |
| --- | --- |
| `ops/repo-class-profile.js` | resolver — load, parse marker, resolve, apply, waive |
| `ops/build-seed-payload.js` | `profile` option: class picks the categories; INHERIT drops, FORBID throws |
| `.github/workflows/auto-seed-new-repo.yml` | per-repo class resolution; reports the class per row |
| `.github/workflows/repo-birth-bootstrap.yml` | targeted REMOTE APPLY for one repo |
| `.github/workflows/enforce-policies.yml` | honours `mandatory_files_waive` |
| `l9-repo-template` `scripts/birth-runner/new_repo.py` | reads the same file to apply the profile locally, before creation |

## Birth is immediate, not hourly

`auto-seed-new-repo.yml` still sweeps hourly and still opens a PR. That is the
repair path for repositories that drift or predate their class.

A newborn does not wait for it. `make new-repo` dispatches
`repo-birth-bootstrap.yml` for exactly one repository and waits: labels and
settings are applied, then the remote is read back.

## Adding a class

1. Add it to `policies/repo-classes.yml` with `seed_categories`, `inherit`,
   `forbid`, `remote_apply`, and `mandatory_files_waive`.
2. Extend `ops/test-repo-class-profile.js` with the invariant that class exists
   to protect — in particular, any consumer-side deny list it must never write.
3. `bash ops/validate-starters.sh`.
4. Have the consuming template write the matching `.l9/org-birth-profile.yaml`.

Upstream declares the capability. Downstream declares its class.
