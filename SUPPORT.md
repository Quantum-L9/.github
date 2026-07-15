# Support — Quantum-L9

## Runbooks
| Topic | Runbook |
|---|---|
| CI failures | l9-assurance `RUNBOOK.md` |
| Governance sync failures | CANONICAL_LAW.md §5 |
| Symlink validation | `bash .cursor-commands/ops/scripts/validate_governance_symlinks.sh` |
| SSOT hard reset (emergency) | `GOVERNANCE_SYNC_HARD_RESET=1 bash .cursor-commands/ops/scripts/governance_sync.sh` |
| Graphiti memory layer | CANONICAL_LAW.md §9 |

## Filing Issues
Use the appropriate issue template in any Quantum-L9 repository:
- **Bug:** Standard defect report
- **Feature:** New capability request
- **Governance Violation:** Reports of CANONICAL_LAW.md anti-patterns (§7)
- **CI Failure:** l9-ci-core kernel failures with workflow run link
