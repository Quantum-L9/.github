# Staged workflows — pr-template-kit v1.0.0

These two workflow files could not be committed directly to `.github/workflows/`
because the automation token used for this deployment lacks the `workflows`
permission. They are byte-identical to the kit files (sha256 verified against
`MANIFEST.json`).

## Promote (run locally with a normal user token)

```bash
git mv workflows-staged/pr-files.yml .github/workflows/pr-files.yml
git mv workflows-staged/pr-gates.yml .github/workflows/pr-gates.yml
git rm workflows-staged/README.md && rmdir workflows-staged 2>/dev/null || true
git commit -m "ci(pr): promote staged PR hygiene workflows"
git push
```

## Checksums (sha256)

| File | sha256 |
|------|--------|
| pr-files.yml | b7185315e54714b0897f9ddcd6ddc90957bd63f7c37cb1e61940523be742fec9 |
| pr-gates.yml | 6ab39da76f4c4d411710d403c58575e930d3f49cc37cee3d4224590ac391ea04 |

See `docs/DEPLOY.md` for the full rollout runbook (permissions, distribution
via `workflow_call`, required status checks, warn-only rollout, rollback).
