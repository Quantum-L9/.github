.DEFAULT_GOAL := help
SHELL := /bin/bash
.PHONY: help activate preflight validate sync-labels apply-rulesets set-properties \
        pin-actions audit-pins enforce-dry enforce-apply clean

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

validate: ## Validate boundary guards and SHA pins
	@bash ops/validate-starters.sh
	@bash ops/audit-sha-pins.sh

# ─── Fan-out Operations ──────────────────────────────────────────────────────
sync-labels: ## Sync org label taxonomy to all repos
	@bash scripts/sync-labels.sh --all

# ─── Rulesets ────────────────────────────────────────────────────────────────
apply-rulesets: ## Apply org rulesets (evaluate mode only)
	@bash scripts/apply-rulesets.sh

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

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean: ## Remove generated artifacts
	@echo "clean"
