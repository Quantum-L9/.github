# Agent Runbook — Deploy Quantum-L9 `.github` v3.1

## Mission

Deploy this pack into `Quantum-L9/.github`, activate every **advisory** capability,
and prove the deployment. Do not enable any blocking control. Do not add, proxy, or
modify CI owned by `l9-ci-sdk` or `l9-ci-core`.

## Invariants

The agent MUST preserve all of these:

1. `governance-pr.yml` has `strict.default: false`.
2. `governance-issue.yml` never calls `core.setFailed`.
3. Every JSON ruleset has `"enforcement": "evaluate"`.
4. Push protection remains off. Secret-scanning alerts are on.
5. Dependabot may open PRs but nothing auto-merges them.
6. No workflow here runs pytest, Ruff, Pyright, Semgrep, CodeQL, tests, lint, build,
   or CI remediation. Those belong to `l9-ci-sdk`, `l9-ci-core`, and
   `l9-ci-debt-resolver`.
7. Never overwrite a target repo's existing CODEOWNERS, governance caller, or
   dependabot config without reviewing and merging its intent.
8. Never push directly to `main`; use one deployment PR.
9. Never print the GitHub App private key or installation token.
10. If any invariant fails, stop and report. Do not improvise an enforcing fallback.

## Inputs

| Input | Required | Value |
| --- | --- | --- |
| Organization | yes | `Quantum-L9` |
| Defaults repository | yes | `Quantum-L9/.github` |
| Pack directory | yes | this extracted `dot-github/` folder |
| Pilot filter | yes | `l9-` unless the operator supplies a narrower repo name |
| GitHub CLI auth | yes | org-owner/admin token for setup operations |
| GitHub App | for seeding | Contents R/W + Pull requests R/W on selected repos |

The deployment agent needs `git`, `gh`, `jq`, `bash`, and `python3`.

## Phase 0 — Authenticate

```bash
export ORG=Quantum-L9
export REPO=.github
gh auth status
gh api user --jq .login
gh api orgs/$ORG --jq '{login,plan:.plan.name}'
```

Stop if authentication cannot read the organization and `Quantum-L9/.github`.
Record the authenticated actor and plan in the deployment evidence.

## Phase 1 — Prepare clean checkout

```bash
WORK=$(mktemp -d)
gh repo clone "$ORG/$REPO" "$WORK/repo"
cd "$WORK/repo"
git fetch --all --tags --prune
DEFAULT=$(gh repo view "$ORG/$REPO" --json defaultBranchRef --jq .defaultBranchRef.name)
git checkout "$DEFAULT"
git pull --ff-only origin "$DEFAULT"
git status --porcelain
```

Stop if the checkout is dirty. Create a deployment branch:

```bash
BRANCH="feat/governance-v3.1"
git switch -c "$BRANCH"
```

## Phase 2 — Inspect before overlay

Do not blindly replace the repository. Capture and review differences first:

```bash
PACK=/absolute/path/to/extracted/dot-github
rsync -ain --delete-excluded "$PACK/" ./ | tee "$WORK/overlay-plan.txt"
```

Before copying, inspect these collision-sensitive paths:

```bash
for p in \
  .github/CODEOWNERS \
  .github/pull_request_template.md \
  .github/ISSUE_TEMPLATE \
  SECURITY.md CONTRIBUTING.md README.md; do
  [[ -e "$p" ]] && echo "EXISTING: $p"
done
```

Rules:

- Preserve unrelated existing files.
- For a collision, merge intent; do not take either side wholesale.
- Remove obsolete `distribute-defaults.yml` if it exists. v3.1 uses inheritance,
  reusable workflows, and one-time seeding instead of recurring fan-out.
- Do not add any CI execution workflow.

Overlay without deleting unrelated repository content:

```bash
rsync -a "$PACK/" ./
rm -f .github/workflows/distribute-defaults.yml
```

## Phase 3 — Resolve real team slugs

Pack CODEOWNERS entries may still contain placeholders. List real slugs:

```bash
gh api "orgs/$ORG/teams" --paginate --jq '.[].slug' | sort
```

Resolve each of these in both `.github/CODEOWNERS` and
`templates/CODEOWNERS.repo`:

```text
maintainers
governance
ci-cd
infra
security
```

If a specialized team does not exist, use one verified fallback team for all
patterns. Never leave an unresolved slug. Verify:

```bash
for slug in $(grep -rhoE '@Quantum-L9/[a-z0-9-]+' \
  .github/CODEOWNERS templates/CODEOWNERS.repo | sed 's|@Quantum-L9/||' | sort -u); do
  gh api "orgs/$ORG/teams/$slug" --silent \
    && echo "OK $slug" \
    || { echo "INVALID $slug"; exit 1; }
done
```

## Phase 4 — Static validation

```bash
./scripts/preflight.sh | tee "$WORK/preflight-before.txt"
```

The preflight may report missing seeded files in target repositories; that is
expected before Phase 10. It must not report:

- Invalid CODEOWNERS team slugs.
- Private `.github` repository.
- Advisory posture drift.
- CI boundary violations.
- Shell or workflow syntax defects.

Run independent assertions:

```bash
bash scripts/verify-pack.sh | tee "$WORK/verify-pack.txt"
```

Stop on any failed assertion.

## Phase 5 — Open deployment PR

```bash
git add -A
git diff --cached --stat
git diff --cached --check
git commit -m "feat(governance): deploy advisory defaults v3.1"
git push -u origin "$BRANCH"
PR_URL=$(gh pr create \
  --repo "$ORG/$REPO" \
  --base "$DEFAULT" \
  --head "$BRANCH" \
  --title "feat(governance): deploy advisory defaults v3.1" \
  --body-file docs/DEPLOYMENT-PR.md)
echo "$PR_URL"
```

Review requirements for this deployment PR:

- A human verifies CODEOWNERS slugs.
- A human verifies every ruleset is `evaluate`.
- A human verifies push protection remains off.
- A human verifies no workflow duplicates `l9-ci-sdk`/`l9-ci-core`.
- Existing local policies are reconciled rather than silently discarded.

After approval, merge with the repository's normal merge method:

```bash
gh pr merge "$PR_URL" --squash --delete-branch
```

If the PR cannot merge, report the blocker. Do not bypass branch policy.

## Phase 6 — Create release tags

After merge, tag the exact merged commit:

```bash
git checkout "$DEFAULT"
git pull --ff-only origin "$DEFAULT"
MERGED_SHA=$(git rev-parse HEAD)

git tag -a v3.1.0 "$MERGED_SHA" -m "Quantum-L9 org governance v3.1.0"
git push origin v3.1.0
```

The consumer caller currently references `@v1`. Move that compatibility alias to
the reviewed release commit without deleting it:

```bash
git tag -fa v1 "$MERGED_SHA" -m "Quantum-L9 governance stable v1 -> v3.1.0"
git push origin refs/tags/v1 --force
```

Verify both tags resolve to the same commit:

```bash
test "$(git rev-list -n1 v3.1.0)" = "$(git rev-list -n1 v1)"
```

## Phase 7 — Activate inherited defaults

No command activates inheritance. Verify the `.github` repository is public:

```bash
gh repo view "$ORG/$REPO" --json visibility --jq .visibility
```

Expected: `PUBLIC`. Then test one repository known not to have local overrides:

```bash
TARGET=<pilot-repository>
for p in SECURITY.md CONTRIBUTING.md .github/pull_request_template.md; do
  if gh api "repos/$ORG/$TARGET/contents/$p" --silent 2>/dev/null; then
    echo "LOCAL OVERRIDE: $TARGET/$p — org default will not apply"
  else
    echo "INHERITS: $TARGET/$p"
  fi
done
```

Issue forms and community-health files are now available to repos without local
overrides. Local files win; do not delete them automatically.

## Phase 8 — Activate advisory secret detection

Run only the non-blocking form:

```bash
./scripts/enable-secret-scanning.sh | tee "$WORK/secret-scanning.txt"
```

**Never** pass `--with-push-protection` during v3.1 deployment. Verify:

```bash
gh api "orgs/$ORG" --jq '{
  secret_scanning: .secret_scanning_enabled_for_new_repositories,
  push_protection: .secret_scanning_push_protection_enabled_for_new_repositories,
  dependency_graph: .dependency_graph_enabled_for_new_repositories
}'
```

Acceptance:

- Secret-scanning alerts: enabled where plan/API support permits.
- Dependency graph: enabled for new repositories.
- Push protection: `false`.

If bulk enable is unavailable on the plan, record which repositories need manual
activation. Do not enable a blocking substitute.

## Phase 9 — Activate evaluate-only rulesets

Preview first:

```bash
DRY_RUN=1 ./scripts/apply-rulesets.sh | tee "$WORK/rulesets-dry-run.txt"
```

If the plan does not support `evaluate`, the script exits safely without creating
an active ruleset. Record `SKIPPED_PLAN_LIMIT`; do not fall back to `active`.

If supported:

```bash
DRY_RUN=0 ./scripts/apply-rulesets.sh | tee "$WORK/rulesets-apply.txt"
gh api "orgs/$ORG/rulesets" --jq '.[] | {id,name,enforcement}'
```

Acceptance: every L9-created ruleset says `evaluate`. Stop and disable the ruleset
immediately if any says `active`.

## Phase 10 — Configure one-time seeding App

Create or reuse a GitHub App owned by Quantum-L9:

```text
Name: Quantum-L9 Governance Seeder
Repository permissions:
  Contents: Read and write
  Pull requests: Read and write
Organization permissions:
  Members: Read-only (only if team validation is moved into the workflow)
Installation scope:
  Selected pilot repositories first
Webhooks: disabled
```

Store configuration in `Quantum-L9/.github`:

```bash
# Never echo the private key. Provide the PEM file through a secure local path.
gh variable set GOVERNANCE_APP_ID --repo "$ORG/$REPO" --body "$APP_ID"
gh secret set GOVERNANCE_APP_PRIVATE_KEY --repo "$ORG/$REPO" < "$APP_PRIVATE_KEY_PEM"
```

Create environment `governance-distribution` and add required reviewers in the
GitHub UI. The agent must confirm the environment exists before dispatching:

```bash
gh api "repos/$ORG/$REPO/environments/governance-distribution"
```

Do not replace the App with a personal access token.

## Phase 11 — Pilot seed

First dispatch a dry run:

```bash
gh workflow run seed-governance.yml \
  --repo "$ORG/$REPO" \
  --ref "$DEFAULT" \
  -f mode=dry-run \
  -f repo_filter="${PILOT_FILTER:-l9-}"
```

Wait and inspect:

```bash
RUN_ID=$(gh run list --repo "$ORG/$REPO" --workflow seed-governance.yml \
  --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN_ID" --repo "$ORG/$REPO" --exit-status
gh run view "$RUN_ID" --repo "$ORG/$REPO" --log
```

Review the target list. Ensure archived repos, forks, and `.github` are absent.
Then dispatch `seed` for a narrow pilot — ideally one repository, not every `l9-`
repo at once:

```bash
export PILOT_FILTER=<exact-pilot-repository-name>
gh workflow run seed-governance.yml \
  --repo "$ORG/$REPO" \
  --ref "$DEFAULT" \
  -f mode=seed \
  -f repo_filter="$PILOT_FILTER"
```

The resulting PR must contain only:

```text
.github/CODEOWNERS
.github/workflows/governance.yml
.github/dependabot.yml
```

Review and merge that pilot PR normally. Validate afterward:

```bash
for p in .github/CODEOWNERS .github/workflows/governance.yml .github/dependabot.yml; do
  gh api "repos/$ORG/$PILOT_FILTER/contents/$p" --silent
  echo "OK $PILOT_FILTER/$p"
done
```

Open or edit a pilot PR and confirm the `Governance / pr` job completes with a
neutral/successful advisory result even when the description has findings. It must
not block merge.

## Phase 12 — Fleet seed

Only after the pilot behaves correctly:

```bash
gh workflow run seed-governance.yml \
  --repo "$ORG/$REPO" \
  --ref "$DEFAULT" \
  -f mode=dry-run \
  -f repo_filter=""
```

Review the complete target table, then:

```bash
gh workflow run seed-governance.yml \
  --repo "$ORG/$REPO" \
  --ref "$DEFAULT" \
  -f mode=seed \
  -f repo_filter=""
```

This opens PRs; it does not merge them. Review each collision-sensitive target.
For existing `dependabot.yml` or CODEOWNERS, the workflow skips when all managed
files already exist. Reconcile partial configurations manually rather than
replacing them wholesale.

## Phase 13 — Activate labels

Issue triage writes labels by exact name. Apply labels idempotently to `.github`
and to seeded repositories:

```bash
./scripts/sync-labels.sh "$ORG/$REPO"
./scripts/sync-labels.sh "$ORG/$PILOT_FILTER"
```

For fleet rollout, enumerate active non-fork repos and apply without deletion:

```bash
gh repo list "$ORG" --limit 200 --json name,isArchived,isFork \
  --jq '.[] | select(.isArchived==false and .isFork==false) | .name' \
| while read -r r; do
    ./scripts/sync-labels.sh "$ORG/$r"
  done
```

The script creates or edits known labels and never deletes unrelated labels.

## Phase 14 — Activate weekly report

The schedule activates after merge. Run it once immediately:

```bash
gh workflow run governance-report.yml --repo "$ORG/$REPO" --ref "$DEFAULT"
REPORT_RUN=$(gh run list --repo "$ORG/$REPO" --workflow governance-report.yml \
  --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$REPORT_RUN" --repo "$ORG/$REPO" --exit-status
gh issue list --repo "$ORG/$REPO" --label advisory --state open
```

Expected: one open issue titled `Governance posture (advisory, weekly)`. Repeated
runs update that issue instead of opening duplicates.

## Phase 15 — Final verification

Run preflight again from current `main`:

```bash
git checkout "$DEFAULT"
git pull --ff-only origin "$DEFAULT"
./scripts/preflight.sh | tee "$WORK/preflight-after.txt"
bash scripts/verify-pack.sh | tee "$WORK/verify-pack-after.txt"
```

Verify control states explicitly:

```bash
# rulesets — all must be evaluate or absent due to plan limits
gh api "orgs/$ORG/rulesets" --jq '.[] | select(.name|startswith("L9 advisory")) | [.name,.enforcement] | @tsv'

# blocking push protection must remain false
gh api "orgs/$ORG" --jq .secret_scanning_push_protection_enabled_for_new_repositories

# reusable alias and release tag must match
test "$(git rev-list -n1 v3.1.0)" = "$(git rev-list -n1 v1)"

# no duplicated CI execution in defaults workflows
! grep -rEi '\b(pytest|ruff|pyright|semgrep|codeql|npm test|tox)\b' .github/workflows/
```

## Acceptance checklist

Deployment is complete only when all applicable items are true:

- [ ] Deployment PR merged without bypassing policy.
- [ ] `.github` repository is public.
- [ ] All CODEOWNERS slugs resolve to real Quantum-L9 teams.
- [ ] `v3.1.0` and `v1` tags resolve to the merged commit.
- [ ] Governance PR workflow defaults to advisory.
- [ ] Issue triage never fails a workflow.
- [ ] Secret-scanning alerts are enabled where supported.
- [ ] Push protection remains off.
- [ ] Rulesets are `evaluate`, or skipped because the plan lacks evaluate mode.
- [ ] GitHub App is configured through protected environment review.
- [ ] Pilot seed PR merged and verified.
- [ ] Fleet seed PRs opened; none auto-merged.
- [ ] Dependabot opens PRs only; no auto-merge configuration exists.
- [ ] Labels exist where issue triage runs.
- [ ] Weekly governance report issue exists and updates in place.
- [ ] No CI execution duplicated from `l9-ci-sdk` or `l9-ci-core`.
- [ ] Final preflight reports no posture drift or boundary violation.

## Evidence artifact

The agent must produce `deployment-evidence.md` containing:

- Actor, UTC timestamp, org plan, deployment PR URL, merged SHA.
- `v3.1.0` and `v1` tag SHAs.
- Preflight before/after outputs or links.
- Secret-scanning state and explicit push-protection state.
- Ruleset IDs, names, and enforcement modes, or `SKIPPED_PLAN_LIMIT`.
- Seeder dry-run and pilot run URLs.
- Pilot PR URL and validation result.
- Fleet seed run URL and count of PRs opened/skipped/failed.
- Weekly report run URL and issue URL.
- Any local overrides or manual follow-ups.

Use `docs/DEPLOYMENT-EVIDENCE-TEMPLATE.md`. Do not declare success with omitted or
unknown acceptance items; mark them `NOT_APPLICABLE`, `SKIPPED_PLAN_LIMIT`, or
`BLOCKED` with the reason.

## Rollback

Rollback must preserve advisory availability:

1. Disable (do not delete) L9 rulesets:

   ```bash
   gh api "orgs/$ORG/rulesets" --jq '.[] | select(.name|startswith("L9 advisory")) | .id' \
   | while read -r id; do
       gh api -X PUT "orgs/$ORG/rulesets/$id" --input <(gh api "orgs/$ORG/rulesets/$id" | jq '.enforcement="disabled"')
     done
   ```

2. Repoint `v1` to the last known-good release tag; never delete it:

   ```bash
   git tag -fa v1 <last-known-good-tag> -m "rollback governance alias"
   git push origin refs/tags/v1 --force
   ```

3. Close unmerged fleet seed PRs. Merged seed files are harmless and advisory;
   revert them through normal PRs only if necessary.
4. Revert the deployment PR through a new PR. Do not force-push `main`.
5. Secret scanning is detection-only and normally should remain enabled during a
   rollback. Push protection was never enabled.
