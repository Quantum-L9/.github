# Deploy

## 1. Place the files

If your org already has a `.github` repository:

```bash
./scripts/install.sh /path/to/org/.github
cd /path/to/org/.github
git checkout -b feat/pr-templates
git add .github docs
git commit -m "feat(pr): org-wide PR template with intent reconciliation and gates"
git push -u origin feat/pr-templates
```

If it does not exist, create a **public** repository named exactly `.github` in the
org first, then run the same steps. A private `.github` repo will not serve PR
templates org-wide.

Merge to the default branch. Templates take effect on the next PR opened in any
repo that has no local override.

## 2. Grant the workflows what they need

`pr-files.yml` edits the PR body, so it needs `pull-requests: write`. Confirm at
**Org → Settings → Actions → General**:

- Workflow permissions: *Read repository contents and packages permissions*
  (the workflows declare their own elevated scopes explicitly)
- Allow GitHub Actions to create and approve pull requests: not required

Both workflows are already scoped with a minimal top-level `permissions:` block and
pin third-party actions to full commit SHAs.

## 3. Distribute the workflows

Workflows in the `.github` repo do **not** run for other repositories. Only the
templates propagate. Pick one:

**Option A — reusable workflow (recommended).** Move the job bodies into
`workflow_call` workflows here, then each repo adds a three-line caller:

```yaml
name: PR hygiene
on:
  pull_request:
    types: [opened, edited, synchronize, reopened, ready_for_review]
jobs:
  hygiene:
    uses: YOUR_ORG/.github/.github/workflows/pr-gates.yml@v1
```

**Option B — sync.** Copy `.github/workflows/pr-*.yml` into each repo with a
scheduled sync job or a tool like `repo-file-sync-action`.

Tag this repo `v1` and let callers pin the tag, so you can iterate on `main`
without breaking every repo at once.

## 4. Make the checks required

Per repo, or org-wide via a **ruleset** on the default branch:

- Require a pull request before merging
- Required status checks: `PR gates / check`, `PR files touched / annotate`
- Require branches to be up to date before merging

Roll out in warn-only mode first: comment out the `core.setFailed(...)` lines in
both workflows, watch a week of real PRs, then re-enable. Turning hard failures on
day one trains people to bypass rather than comply.

## 5. Validate

```bash
# from a repo with the workflows installed
gh pr create --fill --draft            # drafts are skipped by both workflows
gh pr ready
gh pr view --json body -q .body        # confirm the Files touched block was written
gh run list --workflow "PR gates"
```

Expected: an untouched template fails gates with an empty **Problem**, no **Risk**
box checked, and no **Evidence**. That failure is the smoke test.

## Rollback

Revert the merge commit on this repo's default branch. Templates stop being applied
immediately for new PRs; existing PR bodies are unaffected. Remove the required
status checks from any ruleset first, otherwise open PRs will block on a check that
no longer runs.
