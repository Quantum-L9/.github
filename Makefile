.DEFAULT_GOAL := help
SHELL := /bin/bash
.PHONY: help activate preflight validate sync-core sync-labels sync-labels-all \
        seed-dry seed-apply birth-bootstrap birth-seed \
        apply-rulesets set-properties pin-actions audit-pins enforce-dry enforce-apply \
        dispatch clean

# ─── Info ────────────────────────────────────────────────────────────────────
help: ## Show all targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── One-Shot Activation ─────────────────────────────────────────────────────
activate: ## Run full activation (secret scanning, rulesets, labels, seed, preflight)
	@bash ops/activate-all.sh

# ─── Validation ──────────────────────────────────────────────────────────────
preflight: ## Run preflight health check (read-only)
	@bash scripts/preflight.sh

validate: ## Validate starters, pack integrity, and SHA pins
	@bash ops/validate-starters.sh
	@bash ops/audit-sha-pins.sh

# ─── Sync from l9-ci-core ────────────────────────────────────────────────────
sync-core: ## Sync l9-ci-pack from l9-ci-core at pinned SHA
	@test -n "$(REF)" || (echo "usage: make sync-core REF=<40-char-sha>" >&2; exit 2)
	@bash ops/sync-v2-starters.sh $(REF)

# ─── Fan-out Operations ──────────────────────────────────────────────────────
sync-labels: ## Sync org label taxonomy to one repo (REPO=owner/name)
	@test -n "$(REPO)" || (echo "usage: make sync-labels REPO=owner/name (org-wide: make sync-labels-all)" >&2; exit 2)
	@bash scripts/sync-labels.sh "$(REPO)"

sync-labels-all: ## Sync org label taxonomy to every active repo (weekly sweep, on demand)
	@gh workflow run sync-labels-all.yml

seed-dry: ## Dry-run: show which repos would be seeded
	@gh workflow run auto-seed-new-repo.yml -f dry_run=true

seed-apply: ## Seed governance files into all unseeded repos
	@gh workflow run auto-seed-new-repo.yml -f dry_run=false

# ─── Repo Birth ──────────────────────────────────────────────────────────────
birth-bootstrap: ## REMOTE APPLY + attest one newly created repo (REPO=name [CLASS=...])
	@test -n "$(REPO)" || (echo "usage: make birth-bootstrap REPO=<repo-name> [CLASS=<repo-class>]" >&2; exit 2)
	@gh workflow run repo-birth-bootstrap.yml \
		-f target_repo="$(REPO)" \
		-f repo_class="$(CLASS)" \
		-f dry_run=false

birth-seed: ## Seed one newly created repo's applicable files (REPO=name [CLASS=...])
	@test -n "$(REPO)" || (echo "usage: make birth-seed REPO=<repo-name> [CLASS=<repo-class>]" >&2; exit 2)
	@gh workflow run auto-seed-new-repo.yml \
		-f target_repo="$(REPO)" \
		-f repo_class="$(CLASS)" \
		-f dry_run=false

# ─── Rulesets ────────────────────────────────────────────────────────────────
apply-rulesets: ## Apply org rulesets (evaluate mode only)
	@bash ops/apply-rulesets.sh

# ─── Custom Properties ───────────────────────────────────────────────────────
set-properties: ## Auto-detect and set custom properties on all repos
	@bash ops/set-repo-properties.sh --apply

# ─── SHA Pinning ─────────────────────────────────────────────────────────────
pin-actions: ## Pin floating action refs to current SHA
	@bash ops/pin-actions-sha.sh

audit-pins: ## Audit this repo for floating action refs
	@bash ops/audit-sha-pins.sh

# ─── Policy Enforcement ──────────────────────────────────────────────────────
enforce-dry: ## Dry-run: show policy drift without fixing
	@gh workflow run enforce-policies.yml -f dry_run=true

enforce-apply: ## Enforce policies (auto-correct settings, report missing files)
	@gh workflow run enforce-policies.yml -f dry_run=false

# ─── Cross-Repo Dispatch ─────────────────────────────────────────────────────
dispatch: ## Notify all consumer repos of template changes
	@gh workflow run dispatch-template-update.yml

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean: ## Remove generated artifacts
	@rm -f /tmp/requirements-consumer-ci.txt
	@echo "clean"
