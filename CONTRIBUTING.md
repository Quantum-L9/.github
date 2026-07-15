# Contributing to Quantum-L9

## Governance Setup (Required Before First PR)
All contributors must wire their workspace to the CANONICAL_LAW.md symlink contract before making any commits. This is non-negotiable — CI validates symlink integrity.

### Quick Setup Checklist
```bash
# 1. Clone Cursor-Governance to the canonical local path
git clone https://github.com/Quantum-L9/Cursor-Governance.git ~/.cursor-governance

# 2. Run the workspace symlink setup script (idempotent)
bash ~/.cursor-governance/ops/scripts/setup_workspace_symlinks.sh

# 3. Validate symlinks are correct
bash ~/.cursor-governance/ops/scripts/validate_governance_symlinks.sh

# 4. Push first governance backup
bash ~/.cursor-governance/ops/scripts/backup_to_github.sh
```

These steps implement CANONICAL_LAW.md §2 (required symlinks) and §8 (setup checklist).
See: https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md

## Naming Conventions (CANONICAL_LAW.md §4)
| Prefix | Location |
|---|---|
| `l9-*` | GlobalCommands/skills/ only |
| `plasticos-*` | Repo `.claude/skills/` only |
| Repo rules | Repo `.cursor/rules/` only |

## CI Onboarding
Every Quantum-L9 repo runs CI via l9-ci-core kernels. Starter workflows are available in your repo's Actions tab → New workflow → By Quantum-L9.

## Anti-Patterns to Never Commit (CANONICAL_LAW.md §7)
The following patterns will be caught by CI and block merge:
- Creating a second GlobalCommands tree in any repo (`.cursor/governance/GlobalCommands`, `.cursor/skills`, etc.)
- Hard-resetting or force-pushing the Cursor-Governance SSOT clone
- Committing `.cursor-commands` symlink content into app repos (the symlink itself is allowed; its content lives in `~/.cursor-governance`)
