# Contributing to Quantum-L9

## Governance Setup Checklist {#governance-setup}

Before opening any pull request, verify each item:

- [ ] Cloned `Cursor-Governance` into your local workspace root
- [ ] Ran `setup_workspace_symlinks.sh` (see [§2 symlink contract](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md#2-symlink-contract))
- [ ] Validated symlinks resolve correctly: `ls -la .cursor/rules .cursor/skills .cursor/commands`
- [ ] Read [CANONICAL_LAW.md §8](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md#8) for workspace wiring requirements
- [ ] Reviewed [CANONICAL_LAW.md §7 Anti-Patterns](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md#7-anti-patterns) — never violate these
- [ ] All CI gates green (no bypassing required status checks)
- [ ] CODEOWNERS notified for blast-radius files

---

## Quick Setup (3 Steps)

```bash
# Step 1: Clone Cursor-Governance alongside your target repo
git clone https://github.com/Quantum-L9/Cursor-Governance.git

# Step 2: Run workspace symlink wiring
cd Cursor-Governance
bash scripts/setup_workspace_symlinks.sh

# Step 3: Validate symlinks
ls -la .cursor/rules .cursor/skills .cursor/commands
# Expected: all three resolve without error
```

Per [CANONICAL_LAW.md §2](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md#2-symlink-contract):
the workspace root must have `.cursor/` symlinks resolving to `Cursor-Governance/rules/`, `skills/`, and `commands/`.

---

## CI Gate Requirements

All pull requests are checked by the L9 v2 CI pipeline:

| Gate | Tool | Source |
|---|---|---|
| Lint + format | ruff (Python) / Biome (TypeScript) | `l9-lint-test.yml` via `l9-ci-core` |
| Type-check | mypy (Python) / tsc (TypeScript) | `l9-lint-test.yml` via `l9-ci-core` |
| Unit tests | pytest (Python) / vitest (TypeScript) | `l9-lint-test.yml` via `l9-ci-core` |
| Analysis pipeline | Semgrep + normalize + publish | `l9-analysis.yml` via `l9-ci-core` |
| Governance check | PR metadata quality | `governance-pr.yml` (advisory) |

Consumer repos use the centralized composite actions for setup:

```yaml
- uses: Quantum-L9/.github/actions/setup-python-hygiene@<sha>
- uses: Quantum-L9/.github/actions/setup-node-hygiene@<sha>
- uses: Quantum-L9/.github/actions/immutable-checkout@<sha>
```

> **Anti-patterns** ([§7](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md#7-anti-patterns)):
> Never duplicate logic across workflows. Never add business logic to thin callers.
> Never reference `@main` from workflow uses — always pin to full 40-char SHA.

---

## Branch Naming & Commit Conventions

- Branches: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`
- Commits: Conventional Commits format — `feat(scope): message`
- PRs targeting `main` require CODEOWNERS approval for blast-radius paths

---

## Org-Wide Automation (What Happens Automatically)

When you create a new repo or push code, the org governance system acts without
manual intervention:

| Event | Automation | Your Action |
| --- | --- | --- |
| New repo created | `auto-seed-new-repo.yml` opens a PR with CODEOWNERS + dependabot + governance caller | Merge the PR |
| Template changes in `.github` | `dispatch-template-update.yml` notifies your repo | Merge the auto-sync PR (if you have `on-org-update.yml`) |
| Governance files deleted | `continuous-sync.yml` opens a restoration PR | Merge or opt out (`.l9/no-sync`) |
| Repo settings drift | `enforce-policies.yml` auto-corrects | Nothing — settings are restored |
| Labels missing | `sync-labels-all.yml` adds them | Nothing — labels appear |

---

## Opting Out

Consumer repos can opt out of specific automation:

| Opt-out | How | Effect |
| --- | --- | --- |
| Drift remediation | Create `.l9/no-sync` | `continuous-sync.yml` skips this repo |
| Policy enforcement | Create `.l9/no-policy-enforcement` | `enforce-policies.yml` skips this repo |

---

## This Repo's Own CI

`Quantum-L9/.github` validates itself on every PR/push to `main`:

- **`validate-starters.sh`** — `l9-ci-pack/` completeness and `@main`-ref check
- **`actionlint`** — lints all workflow files for YAML/expression/shellcheck errors
- **`SHA-pin audit`** — every `uses:` ref must be pinned by full 40-char commit SHA
- **`properties.json schema validation`** — workflow-template metadata

---

## Kernel Authoring (l9-ci-core contributors only)

- Kernels must use `on: workflow_call` only
- `l9-self-ci.yml` must remain `on: pull_request/push` — **never convert to workflow_call** (circular dependency)
- SHA-pin discipline: force-update moving tag for backward-compatible changes; cut new major for breaking
- See [workflow-interface-registry.yml](https://github.com/Quantum-L9/.github/blob/main/workflow-interface-registry.yml) for the full kernel API contract
