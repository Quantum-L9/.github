# Deploy

## 1. Place the files

```bash
./scripts/install.sh /path/to/org/.github
cd /path/to/org/.github
git checkout -b feat/issue-templates
git add .github docs && git commit -m "feat(issues): org-wide issue forms, taxonomy, triage"
git push -u origin feat/issue-templates
```

The repository must be named exactly `.github` and be **public** for org-wide
defaults. Merge to the default branch; forms appear on the next new issue in any
repo without its own `ISSUE_TEMPLATE/` directory.

Note the override semantics: a repo with even one local form ignores **all** org
defaults. There is no merge. If a repo needs one extra form, copy the whole set.

## 2. Fix the placeholders in config.yml

`contact_links` ships with `YOUR_ORG` placeholders. Replace all three:

```bash
grep -rl YOUR_ORG .github | xargs sed -i '' 's/YOUR_ORG/acme/g'   # macOS
```

Confirm the security advisory URL resolves, and that private vulnerability
reporting is enabled org-wide (**Settings → Code security → Private vulnerability
reporting**). The link is the only thing standing between you and a zero-day filed
as a public issue.

## 3. Create the labels

Triage writes `sev:*`, `priority:*`, `scope:*`, `regression`, `breaking`, `env:prod`,
`area:ci`, and `security:possible-leak`. `addLabels` creates missing labels silently
with a random color, so seed them deliberately:

```bash
./scripts/sync-labels.sh acme/agentkit
# or across the org
gh repo list acme --json nameWithOwner -q '.[].nameWithOwner' \
  | xargs -n1 ./scripts/sync-labels.sh
```

## 4. Distribute the workflows

Workflows in `.github` do **not** run for other repos — only the templates
propagate. Convert `issue-triage.yml` to `workflow_call` and have each repo add a
caller pinned to a tag:

```yaml
on:
  issues:
    types: [opened, edited, reopened]
jobs:
  triage:
    uses: YOUR_ORG/.github/.github/workflows/issue-triage.yml@v1
```

## 5. Validate

```bash
gh issue create --template 1-bug.yml            # forms are prefilled by name
gh issue view <n> --json labels -q '.labels[].name'
gh run list --workflow "Issue triage"
```

Field parsing depends on the rendered `### <Label>` headings, which come from the
form's `attributes.label` values. **If you rename a label, update the matching
`field('…')` call in the workflow.** Test matrix worth running once:

- S1 bug → expect `sev:S1` + `priority:P0`
- bug with "Last known good" filled → expect `regression`
- feature with Scope XL → expect `scope:XL` + a design-doc comment
- paste `AKIA` + 16 chars into a body → expect `security:possible-leak` and a failed run

## Rollback

Revert the merge commit. Forms stop being offered immediately; existing issues and
labels are untouched. Remove workflow callers from consumer repos first, otherwise
they will fail on a missing reusable workflow.
