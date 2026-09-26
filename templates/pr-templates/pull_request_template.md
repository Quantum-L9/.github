<!-- Managed by Quantum-L9/.github (templates/pr-templates/pull_request_template.md).
     The next org seed PR replaces local edits to this file — change it there.
     Checked by .github/workflows/governance.yml, which runs Quantum-L9/.github
     governance-pr.yml. Check a body before opening the PR:
       node ops/check-pr-body.js body.md   (in a Quantum-L9/.github checkout) -->

## Problem

<!-- REQUIRED. The error, bug, or gap this fixes, in your own words (30+ characters).
     Lead with the symptom a human saw; paste the traceback, failing assertion, or log line.
     The block below is a placeholder: it does not count until you replace or delete it. -->

```
paste the error / failing output here, or delete this block and describe the gap
```

Closes #

## Fix

<!-- What you changed to make the problem above go away. Note alternatives you rejected and why. -->

## Risk

<!-- Tick exactly one. This routes how hard reviewers look. -->

- [ ] Low — additive, reversible, no data or contract change
- [ ] Medium — touches shared code, config, or a public interface
- [ ] High — breaking change, migration, IAM/network, or irreversible

Blast radius:
Rollback:

## Evidence

<!-- REQUIRED. Show the problem is gone: paste real command output in a ``` block,
     or link the CI run (https://github.com/<owner>/<repo>/actions/runs/<id>).
     "Tests pass" is not evidence. The block below is a placeholder and does not count. -->

```
$ pytest -q
$ ruff check . && pyright
```

## Gates

<!-- Tick each box that is true. Leave a box unchecked only with a reason on the
     same line, after a separator (—, --, :, or n/a). The reason needs at least
     four letters of its own; a bare "n/a" or "—" fails the check. Example:
     - [ ] Regression test added that fails without this fix — n/a: docs-only change -->

- [ ] Regression test added that fails without this fix
- [ ] No secrets, tokens, or customer data in code, tests, fixtures, or logs
- [ ] `semgrep` clean, or findings triaged below
- [ ] New IAM / workflow permissions are least privilege and enumerated
- [ ] Third-party actions pinned to a full commit SHA
- [ ] Public interface change is documented and versioned
- [ ] Observability exists for the new path (metric, log, trace, or alert)

## Reviewer focus

<!-- Where to look hardest. Trade-offs accepted. Deferred follow-ups, with issue links. -->

## Changes by intent

<!-- One line per file you meant to touch, with the reason: `path — why`.
     This is your contract with the reviewer; the Files touched list below is the
     actual diff, so an unexplained file there is usually a stray debug edit, a
     committed artifact, or scope creep. Delete any heading that stays empty. -->

**Added**
- `path/to/new_file.py` — why this file needs to exist

**Modified**
- `path/to/existing.py` — what changed in it and why

**Deleted**
- `path/to/dead.py` — why it is safe to remove

## Files touched

<!-- Filled in automatically only where .github/workflows/pr-files.yml runs
     (Quantum-L9/.github). Everywhere else, delete this section. -->

<!-- FILES-TOUCHED:START -->
_pending — the bot fills this in on push_
<!-- FILES-TOUCHED:END -->
