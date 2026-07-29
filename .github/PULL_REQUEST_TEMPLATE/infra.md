## Problem

<!-- The operational symptom, cost line, alert, or capability gap driving this change. -->

```
paste the alert, error, or cost/quota evidence here
```

Closes #

## Environments

- [ ] dev
- [ ] staging
- [ ] prod

## Plan

<details><summary><code>terraform plan</code></summary>

```
paste plan output here
```

</details>

- [ ] Plan reviewed; no unexpected destroy or replace
- [ ] No drift against live state
- [ ] State backend and locking unchanged, or migration documented below

## Risk

- [ ] Low — additive resource, no traffic path, trivially destroyable
- [ ] Medium — modifies an in-use resource, brief or zero downtime
- [ ] High — destroy/replace, data store, IAM, network boundary, or DNS

Resources created:
Resources modified:
Resources destroyed or replaced:
Expected downtime:
Blast radius:

## Rollback

Procedure:
Data-loss risk on rollback:
Backup or snapshot taken:

## Gates

- [ ] IAM least privilege; no wildcard actions or resources
- [ ] Secrets from Secrets Manager or SSM; no literals, no tfvars in git
- [ ] Network exposure unchanged, or new ingress justified below
- [ ] Encryption at rest and in transit enforced
- [ ] Tagging and cost allocation applied
- [ ] Monitoring and alerting cover the new resources
- [ ] Module version pinned; provider constraints unchanged or bumped deliberately

## Reviewer focus

## Changes by intent

<!-- `path — why`. Paths in backticks. Reconciled against the diff by CI. -->

**Added**
**Modified**
**Deleted**

## Files touched

<!-- FILES-TOUCHED:START -->
_pending — the bot fills this in on push_
<!-- FILES-TOUCHED:END -->
