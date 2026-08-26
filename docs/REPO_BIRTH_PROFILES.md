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

## Adding a class

1. Add it to `policies/repo-classes.yml` with all five keys.
2. Extend `ops/test-repo-class-profile.js` with the invariant that class exists
   to protect — in particular, any consumer-side deny list it must never write.
3. `bash ops/validate-starters.sh`.
4. Have the consuming template write the matching `.l9/org-birth-profile.yaml`.

The two repositories must agree in one direction only: upstream declares the
capability, downstream declares its class.
