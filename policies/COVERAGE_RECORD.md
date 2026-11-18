# Coverage record: not PASS

Lane F. Stacked on Quantum-L9/.github#270 head `3e1f58e9342c4b1f98802efe061f1d287f1514f6`.
Read at 2026-11-18T19:33Z. This record does not change a ruleset. A missing signer, an unexecuted required step, and an admin bypass stay open. None of those is PASS.

## Predecessor dispositions

| Lane | Record | Head | Disposition |
| --- | --- | --- | --- |
| A | Quantum-L9/.github#269 | `ec3f5c6734530a3a90438a80827ebd8edd876734` | candidate, admission false |
| B | Quantum-L9/.github#270 | `3e1f58e9342c4b1f98802efe061f1d287f1514f6` | BLOCKED, no signer or in-toto layout |
| C | Quantum-L9/Cursor-Governance#1042 | `0000ac871b8cea0b37339ed76fc753cad1ef36ef` | consumer mirror, canonical false |
| M | Quantum-L9/L9-Ops-MCP#45 | `bccd9bb1d4e87822619929263ed7518fba8d60d4` | mirror pin; signature verification BLOCKED |
| E | Quantum-L9/l9-ci-core#277 | `01c095c7ea1b8e7cbe053ae6989e577c5dfa3ca6` | fail-closed step is in the file; the pull_request run of Analyze (central Core) (run 44379732178) succeeded without executing it |

## Live ruleset 21895545

Repository ruleset on Quantum-L9/.github, name "L9 canonical CI required", enforcement active. Conditions are only `ref_name.include = ~DEFAULT_BRANCH`. Bypass actor OrganizationAdmin, mode always. Required check `Analyze (central Core)`, `strict_required_status_checks_policy` false, `do_not_enforce_on_create` true. Workflow `.github/workflows/org-ci.yml` at `refs/heads/main`, repository_id 1285564308.

## Source `rulesets/l9-canonical-ci-required.json`

`repository_name.exclude` contains `.github`. `bypass_actors` is empty. `strict_required_status_checks_policy` is true. The same workflow path, ref, repository_id, and check name are present.

The source and the live ruleset disagree on repository exclusion, bypass actors, and strict status checks. This lane does not edit either one. The source exclusion means the committed org ruleset does not claim to govern `.github`. The live repository ruleset is attached to `.github` and still does not prove a bad pull request cannot merge: OrganizationAdmin bypasses it, strict is false, and the required job that ran for lane E did not execute the new fail-closed step.

## Live ruleset 20855699

Repository ruleset on Quantum-L9/Cursor-Governance, name "main-protection", enforcement active. Bypass actor EnterpriseOwner, mode always. Required checks: Lint and Type Check, Test Suite, Root-file append-only gate, governance-self-check, repo-hygiene. `strict_required_status_checks_policy` true. `require_code_owner_review` false. `required_approving_review_count` 0. Required review thread resolution true. Deletion and non-fast-forward are denied.

## Not changed

No ruleset mutation. No new CI script. `.github` is not called covered by the source ruleset that excludes it. The owner admission and the signer remain open.
