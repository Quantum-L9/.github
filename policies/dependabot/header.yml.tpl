# Rendered by Quantum-L9/.github ops/render-dependabot.js; managed — local edits
# are restored; opt out with .l9/no-sync. ADR: docs/adr/0019-dependabot-managed-rendered.md
#
# Ecosystems follow this repository's root: github-actions always; uv when
# uv.lock exists, else pip when a root requirements*.txt or a PEP 621
# pyproject.toml exists; pre-commit when .pre-commit-config.yaml exists.
# Tools Core selects (Quantum-L9/l9-ci-core core-owned-tools.json) and the
# Core, SDK and .github action pins are ignored: they are not bumped here.
# ADVISORY POSTURE: this opens PRs only. No auto-merge, no major groups.
version: 2
updates:
