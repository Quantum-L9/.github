# GitHub settings as code

The operator does not click GitHub settings. This directory declares them, and
the factory's `settings-apply.yml` (Quantum-L9/l9-repo-template, engine
`tools.l9_settings` in Quantum-L9/l9-ci-core) brings live state to it with the
existing repo-birth App.

| File | Declares |
| --- | --- |
| `settings.schema.json` | Shape of every file here |
| `org.yml` | The organization, the applier binding, and who owns org rulesets (`rulesets/`) |
| `repos/<repository>.yml` | One repository: visibility, merge settings, Actions access and default workflow permissions, environments, repository rulesets |

## Rules

- `UNKNOWN` means not declared. It was unreadable when the file was populated,
  or it is undecided. The applier never writes an `UNKNOWN` setting. Replace it
  with a value only from an observation or a decision.
- Secret and variable values are never declared. An environment may list
  `required_secrets` by name. The applier checks that those names are present.
- A repository that has no file here is not managed.
- Repository rulesets are matched by name. A live ruleset not listed is
  reported as unmanaged and never deleted. Environments are never deleted.
- Organization rulesets are declared in `rulesets/` and are not redeclared here.
- Merge settings here are observed live values. `ops/validate-settings.py`
  prints every disagreement with `policies/repo-settings.yml` as `CONFLICT`
  and does not reconcile them.

## Apply

`settings-apply.yml` runs daily, and on dispatch with `dry_run` (default `true`)
and an optional repository filter. It reads live state and prints the plan. It
writes only when `dry_run` is `false`. It fails closed if any declared setting
cannot be read.

## Validate

`python3 ops/validate-settings.py` (offline). Run by `make validate` through
`ops/validate-starters.sh`.
