# Support

## Getting Help

### Primary: GitHub Issues

Open a GitHub Issue in the relevant repository using the appropriate template:

| Issue Type | Template |
|---|---|
| Bug report | [Bug Report](https://github.com/Quantum-L9/.github/issues/new?template=bug_report.yml) |
| Feature request | [Feature Request](https://github.com/Quantum-L9/.github/issues/new?template=feature_request.yml) |
| Governance violation | [Gov Violation](https://github.com/Quantum-L9/.github/issues/new?template=gov-violation.yml) |
| CI pipeline failure | [CI Failure](https://github.com/Quantum-L9/.github/issues/new?template=ci-failure.yml) |

### Secondary: GitHub Discussions

For questions, architectural discussions, and community input:
[github.com/Quantum-L9/.github/discussions](https://github.com/Quantum-L9/.github/discussions)

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
