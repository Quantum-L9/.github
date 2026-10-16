# Dependabot render fixtures

Each directory is one repository-root shape for `ops/render-dependabot.js`
(ADR `docs/adr/0019-dependabot-managed-rendered.md`).

- `root.json` lists the root file names and, when `pyproject.toml` is among
  them, its text. It stands in for the GitHub root listing so the tree holds
  no real manifests for the dependency graph to scan.
- `expected.yml` is the golden render, byte for byte.

`node ops/test-render-dependabot.js` renders every fixture twice and compares
both renders to `expected.yml`. Regenerate a golden only for an intended
template change, and review the diff.
