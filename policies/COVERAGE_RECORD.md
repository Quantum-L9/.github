# Coverage record: not PASS

Lane F. Stacked on Quantum-L9/.github#270 head `a846d617d5554a00572412e13e5c70f6135aed7e`.
Read at 2026-11-19T15:35Z. This record does not change a ruleset. An empty owner trust root, a required step that is not yet on the default branch, and an admin bypass stay open. None of those is PASS.

## Predecessor dispositions

| Lane | Record | Head | Disposition |
| --- | --- | --- | --- |
| A | Quantum-L9/.github#269 | `fe4084ca80909f2a40e78bf8e5bc89a54753f45b` | candidate, admission false, trust root empty |
| B | Quantum-L9/.github#270 | `a846d617d5554a00572412e13e5c70f6135aed7e` | BLOCKED, no owner key and no default-branch release |
| C | Quantum-L9/Cursor-Governance#1042 | `4abca8c4ac96e822425e03a7139be2e5080bfc42` | merged; report-only pin, not an action denial |
| M | Quantum-L9/L9-Ops-MCP#45 | `0ab84fa5d10e06aaf149caead725843f729354de` | commit URL fails closed; published base is still the unrelated branch |
| E | Quantum-L9/l9-ci-core#277 | `7459d6b5958df9456c6664baf0d4bf8df14a4094` | required job calls the pinned verifier; a live pass is still impossible |

## Live ruleset 21895545

Repository ruleset on Quantum-L9/.github, name "L9 canonical CI required", enforcement active. Conditions are only `ref_name.include = ~DEFAULT_BRANCH`. Bypass actor OrganizationAdmin, mode always. Required check `Analyze (central Core)`, `strict_required_status_checks_policy` false, `do_not_enforce_on_create` true. Workflow `.github/workflows/org-ci.yml` at `refs/heads/main`, repository_id 1285564308.

## Source `rulesets/l9-canonical-ci-required.json`

`repository_name.exclude` contains `.github`. `bypass_actors` is empty. `strict_required_status_checks_policy` is true. The same workflow path, ref, repository_id, and check name are present.

The source and the live ruleset disagree on repository exclusion, bypass actors, and strict status checks. This lane does not edit either one. The source exclusion means the committed org ruleset does not claim to govern `.github`. The live repository ruleset is attached to `.github` and still does not prove a bad pull request cannot merge: OrganizationAdmin bypasses it, strict is false, and the required job that ran for lane E did not execute the new fail-closed step.

## Live ruleset 20855699

Repository ruleset on Quantum-L9/Cursor-Governance, name "main-protection", enforcement active. Bypass actor EnterpriseOwner, mode always. Required checks: Lint and Type Check, Test Suite, Root-file append-only gate, governance-self-check, repo-hygiene. `strict_required_status_checks_policy` true. `require_code_owner_review` false. `required_approving_review_count` 0. Required review thread resolution true. Deletion and non-fast-forward are denied.

## Not changed

No ruleset mutation. No new CI script. `.github` is not called covered by the source ruleset that excludes it. The owner admission and the signer remain open.
