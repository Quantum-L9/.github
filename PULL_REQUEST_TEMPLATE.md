## PR Checklist — Quantum-L9 Governance

### Governance Validation
- [ ] Ran `bash .cursor-commands/ops/scripts/validate_governance_symlinks.sh` — no errors
- [ ] Checked CANONICAL_LAW.md §7 anti-patterns — no second GlobalCommands tree created
- [ ] `.cursor/governance/GlobalCommands` does NOT exist in this branch
- [ ] `.cursor-commands` is a symlink (not committed content)

### CI Pattern
- [ ] New workflows use thin-caller pattern (`uses: Quantum-L9/l9-ci-core/...@v1`), not inline logic
- [ ] All action `uses:` pins are full-length commit SHAs, not floating tags

### Supply Chain
- [ ] No new third-party actions added without SHA pinning
- [ ] No secrets logged or echoed in new steps
