# Support

## Getting Help

### Primary: GitHub Issues

Open a GitHub Issue in the relevant repository using the appropriate template:

| Issue Type | Template |
|---|---|
| Bug | [Bug](https://github.com/Quantum-L9/.github/issues/new?template=1-bug.yml) |
| Feature | [Feature](https://github.com/Quantum-L9/.github/issues/new?template=2-feature.yml) |
| Task | [Task](https://github.com/Quantum-L9/.github/issues/new?template=3-task.yml) |
| Incident | [Incident](https://github.com/Quantum-L9/.github/issues/new?template=4-incident.yml) |
| CI failure | [CI failure](https://github.com/Quantum-L9/.github/issues/new?template=ci-failure.yml) |
| Seed / auto-seed CI failure | [Seed CI failure](https://github.com/Quantum-L9/.github/issues/new?template=seed-ci-failure.yml) |
| Governance violation | [Governance violation](https://github.com/Quantum-L9/.github/issues/new?template=gov-violation.yml) |

A filled-in example: [docs/issue-templates/EXAMPLE.md](docs/issue-templates/EXAMPLE.md).

### Questions

GitHub Discussions are not enabled for this organization. Ask on the PR or issue
you are working from; file a Task only for work with a known outcome — a question
filed as a bug is the most common way an issue tracker rots.

## Automated Governance

Many governance tasks are handled automatically. Before opening an issue:

- **Missing CODEOWNERS/dependabot?** → Wait for the weekly `continuous-sync.yml` PR
- **Labels missing?** → Wait for the weekly `sync-labels-all.yml` run (Monday)
- **Repo settings wrong?** → Wait for the weekly `enforce-policies.yml` run (Wednesday)
- **Need to sync CI?** → Run `make sync-ci` or wait for `dispatch-template-update.yml`

## Out of Scope

The following are **not supported** through Quantum-L9 channels:
- General AI/ML questions unrelated to Quantum-L9 infrastructure
- Debugging third-party tools (GitHub Actions runners, PyPI, npm registry)
- Questions already answered in [CANONICAL_LAW.md](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
- Requests to bypass CI gates or CODEOWNERS requirements
- Requests to opt out of governance without creating `.l9/no-sync`

## Response Expectations

| Channel | Expected Response Time |
|---|---|
| GitHub Issues (bugs, governance) | 2 business days |
| GitHub Issues (features) | 1 week |
| GitHub Discussions | Best effort |
| Security vulnerabilities | See [SECURITY.md](https://github.com/Quantum-L9/.github/blob/main/SECURITY.md) |
