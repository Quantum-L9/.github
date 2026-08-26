# Repo birth profiles

**Authority for what the organization requires.** How a repository is *born* is
owned by `Quantum-L9/l9-repo-template` (`make new-repo`). This repository owns
what the organization applies to it.

## The distinction that makes this work

The organization does not copy every `.github` file into every repository. It
applies every capability that is **applicable** to that repository's class.

| Mode | Meaning | Example |
|------|---------|---------|
| **INHERIT** | GitHub supplies it dynamically from `Quantum-L9/.github`. The repository must **not** carry a copy. | `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md` |
| **MATERIALIZE** | The repository must contain the file. Seeded missing-only. | `.github/CODEOWNERS`, `.github/dependabot.yml`, `.github/labels.yml` |
| **REMOTE APPLY** | GitHub API state, not a file. | labels, repository settings |
| **FORBID** | The repository must never carry this path. A payload that would write one throws. | `.github/workflows/l9-analysis.yml`, `.github/workflows/governance.yml` |

Spraying `.github` across every repository and then building a second
synchronizer to clean up the copies is the failure mode this replaces.

## Why FORBID exists

`Quantum-L9/l9-repo-template` fails closed on repo-local organization CI
distribution — `scripts/inventory_check.py` `DENY_CI_DISTRIBUTION` names
`.github/workflows/l9-analysis.yml`, `l9-lint-test.yml`, `on-org-update.yml`,
`governance.yml`, and `.github/governance/`. Its architecture states the reason:
organization CI targeting, versioning, and enforcement belong to `l9-ci-core`
and `l9-ci-control-plane`, not to the repository.

Seeding the historic default categories into a template-born repository writes
**11** of those paths. Every one makes `make verify` fail in the newborn. The
machinery was already 60–70% built; automating it without a class contract
would only have automated the contradiction faster.

## The contract

`policies/repo-classes.yml` (JSON-in-YAML, so Node reads it without `js-yaml`
and Python reads it with either `json.loads` or `yaml.safe_load`).

A repository declares its own class in `.l9/org-birth-profile.yaml`:

```yaml
schema: l9.org-birth-profile-marker/v1
profile: non_constellation_python
authority: Quantum-L9/.github
```

The organization honours what the repository declares. An absent, unreadable,
or unknown marker resolves to `default` — never to something **wider** than the
repository asked for.

## Classes

| Class | For | Seeds | Forbids |
|-------|-----|-------|---------|
| `default` | Unclassified repositories | The historic `DEFAULT_CATEGORIES` set, byte-for-byte | — |
| `non_constellation_python` | `l9-repo-template` offspring | `.github/CODEOWNERS`, `.github/dependabot.yml`, `.github/labels.yml` | org CI distribution (11 paths) |
| `self_governed` | Repos owning their complete CI/validation surface | nothing — capabilities apply through the API | org CI distribution + governance caller |

### Assigning a class without a commit in the repo

`overrides` in `policies/repo-classes.yml` maps a repository name to a class.
Precedence is **marker > overrides > default_class**: a repository's own
declaration always wins. `overrides` exists so the organization can classify a
repository that has not declared one yet — not to overrule one that has. An
override naming an undefined class fails at policy load, not at seed time.

`default` is a behavioral no-op, asserted in `ops/test-repo-class-profile.js`:
every sweep that ran before profiles existed keeps its exact payload. Adding a
class is how behavior changes — never by editing the default.

`labels` shows why a class beats a global default. `.github/labels.yml` is
*required* by `l9-repo-template` and *opt-in* org-wide. Both stay true because
the class, not the global category list, decides.

## Consumers

| Surface | Uses |
|---------|------|
| `ops/repo-class-profile.js` | resolver — load, parse marker, resolve, apply, waive |
| `ops/build-seed-payload.js` | `profile` option: class picks the categories; INHERIT drops, FORBID throws |
| `.github/workflows/auto-seed-new-repo.yml` | per-repo class resolution; reports the class per row |
| `.github/workflows/repo-birth-bootstrap.yml` | targeted REMOTE APPLY + attestation for one repo |
| `.github/workflows/enforce-policies.yml` | honours `mandatory_files_waive` |
| `l9-repo-template` `scripts/birth-runner/new_repo.py` | reads the same file to apply the profile locally, before creation |

## Birth is immediate, not hourly

`auto-seed-new-repo.yml` still sweeps hourly and still opens a PR — that is the
**repair** path for repositories that drift or predate their class.

A newborn does not wait for it. `make new-repo` dispatches
`repo-birth-bootstrap.yml` for exactly one repository and waits: labels and
settings are applied, then the **remote** is read back and attested. A birth
that only checks what it assembled locally has proved nothing about what GitHub
actually holds.

## Why seeder PRs were turning red

An audit of the seeder's own pull requests (2026-08-26) found five distinct
causes. Three were bugs in the distributed CI caller; two were consumer
invariants the seeder cannot satisfy by writing files.

| Cause | Symptom | Fix |
|-------|---------|-----|
| `pytest --cov` with no `pytest-cov` | `pytest: error: unrecognized arguments: --cov=.` — exit 4 | coverage flags are added only when an import probe finds the plugin |
| `mypy .` in a flat-layout repo | type-checks `tests/`, fixtures and vendored trees for the first time — 11 errors in `l9-ci-core` | `--exclude` for test/fixture dirs when `SOURCE_DIR` resolves to `.` |
| Unqualified job name | seeded `Lint and Type Check` collided with the consumer's own job of that name; one green and one red check under one context | renamed to `Python Lint and Type Check`, matching the existing `Python Test Suite` convention |
| Repo-local deny list | `l9-repo-template` fails closed on the seeded org-CI paths | `non_constellation_python` forbids them |
| Repo-local invariants | `l9-ci-core` bans write permissions in unlisted workflows; `l9-meta-injector` binds a committed report to a `git ls-files` digest, so **any** added file reddens its own `smoke` job | `self_governed` seeds no files at all |

The coverage bug had a specific history worth recording: an earlier hardening
removed an unpinned `pip install pytest-cov` fallback — correctly — but removed
the *probe* with it and left the four `--cov` flags in place. The gate written
to enforce "no unpinned plugin installs" forbade reading too. The rule is *do
not install an unpinned plugin*, not *do not look*, and
`ops/validate-starters.sh` now says so, while additionally failing a caller that
passes `--cov` with no probe, that probes through a pipe (`set -o pipefail`
turns `grep -q`'s early exit into 141), or that publishes an unqualified job
name.

Not every red check on a seeder PR was the seeder's. `SonarCloud Code
Analysis`, `declare-task`, and `Dependabot` are red on those repositories'
`main` branches too, and are out of scope here.

## Adding a class

1. Add it to `policies/repo-classes.yml` with all five keys.
2. Extend `ops/test-repo-class-profile.js` with the invariant that class exists
   to protect — in particular, any consumer-side deny list it must never write.
3. `bash ops/validate-starters.sh`.
4. Have the consuming template write the matching `.l9/org-birth-profile.yaml`.

The two repositories must agree in one direction only: upstream declares the
capability, downstream declares its class.
