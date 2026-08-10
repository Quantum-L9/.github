# Copilot Content Exclusion Policy

This document is the source of truth for Copilot content exclusion rules.
These rules are configured in **Org Settings → Copilot → Content Exclusion**
(not a file — GitHub does not support file-based exclusion config).

## Active Exclusions

Configure these paths in the Org Settings UI:

```
# Environment files (may contain secrets or secret-shaped values)
**/.*env*
**/.env.example
**/.env.local

# Proprietary security testkits (internal IP)
l9-assurance/packages/l9-agent-security-testkit/**
l9-assurance/packages/l9-security-testkit/**

# Infrastructure secrets and credentials
l9-infra/**
infisical-config/**

# CI SDK internals (implementation detail, not for suggestion)
l9-ci-sdk/src/internal/**
```

## Rationale

Content exclusion prevents Copilot from indexing or suggesting code from
sensitive paths. This is distinct from `.gitignore` (which controls what's
committed) and from `copilot-instructions.md` (which shapes suggestions but
doesn't block indexing).

## Maintenance

When adding a new sensitive repository or path:
1. Update this document (source of truth)
2. Apply the change in Org Settings → Copilot → Content Exclusion
3. Exclusions take effect within minutes for new Copilot sessions
