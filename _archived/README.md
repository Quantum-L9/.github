# Archived

Retired artifacts, kept for history. Nothing under `_archived/` is seeded,
synced, validated, or read by any workflow or script: every seed path reads
from `templates/`, and this directory is outside it.

| Path | Retired | Why |
| --- | --- | --- |
| `templates/pr-templates/agent.md` | 2026-09-26 | Legacy agent/chore PR body. It was seeded to consumers as `.github/PULL_REQUEST_TEMPLATE/agent.md` so generated PRs would pass a check (`Enforce-PR-Policies`) that no longer exists. Agent PRs now use the one org template, `templates/pr-templates/pull_request_template.md`. `ops/test-build-seed-payload.js` fails if any seed payload carries `.github/PULL_REQUEST_TEMPLATE/*` again. |

Copies already seeded into consumer repositories are not deleted by any agent
(agents never delete consumer files; see `AGENTS.md`). They are no longer
distributed or refreshed.
