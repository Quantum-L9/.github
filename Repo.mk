# Repository implementation for Core Repository Execution V2 (make-v1).
#
# The root Makefile is the Core-owned make-v1 facade, reproduced byte-for-byte
# from Quantum-L9/l9-ci-core tools/l9_repo/facades/make-v1.mk; it defines
# help/setup/validate/check/test and includes this file. Everything this
# repository runs lives here. Do not redefine a facade target in this file.
#
#   make setup     repo-setup     the toolchain the gates need (node, git, curl,
#                                 PyYAML, jsonschema)
#   make validate  repo-validate  the complete local gate, unchanged: seed
#                                 payload suites, SHA pins, semantic closure
#   make check     repo-check     static subset: SHA-pin audit
#   make test      repo-test      test subset: ops/validate-starters.sh suites
#
# `make validate` stays the one complete local gate. Core runs all four phases
# in order, so check and test re-run subsets of validate there.
.PHONY: repo-setup repo-validate repo-check repo-test \
        activate preflight sync-labels sync-labels-all \
        seed-dry seed-apply birth-bootstrap birth-seed \
        apply-rulesets set-properties pin-actions audit-pins enforce-dry enforce-apply \
        clean

# ─── Core Repository Execution V2 phases ─────────────────────────────────────
# PyYAML for every python3 a gate runs: the system python3 when it has PyYAML,
# otherwise the .venv repo-setup creates. Recipes that reach python3 (directly,
# or through the ops/*.js suites that shell out to `python3`) start with
# $(USE_VENV), so a runner whose python3 lacks PyYAML (Core) sees the same one.
USE_VENV = if [ -x .venv/bin/python3 ]; then export PATH="$(CURDIR)/.venv/bin:$$PATH"; fi;

repo-setup: ## Check node and git; provide a PyYAML + jsonschema interpreter (.venv if needed)
	@set -euo pipefail; \
	for tool in node git python3 curl; do \
	  command -v "$$tool" >/dev/null 2>&1 || { echo "❌ $$tool not found — make validate cannot run" >&2; exit 1; }; \
	done; \
	if ! python3 -c 'import yaml, jsonschema' >/dev/null 2>&1 \
	   && ! { [ -x .venv/bin/python3 ] && .venv/bin/python3 -c 'import yaml, jsonschema' >/dev/null 2>&1; }; then \
	  python3 -m venv .venv; \
	  .venv/bin/pip install --disable-pip-version-check --only-binary=:all: "pyyaml==6.0.2" "jsonschema==4.23.0"; \
	fi

repo-check: ## Static check: audit this repo for floating action refs
	@bash ops/audit-sha-pins.sh

repo-test: repo-setup ## Test suites: seed payload, birth profiles, workflow and PR-body contracts
	@$(USE_VENV) bash ops/validate-starters.sh

# ─── One-Shot Activation ─────────────────────────────────────────────────────
activate: ## Run full activation (secret scanning, rulesets, labels, seed, preflight)
	@bash ops/activate-all.sh

# ─── Validation ──────────────────────────────────────────────────────────────
preflight: ## Run preflight health check (read-only)
	@bash scripts/preflight.sh

repo-validate: repo-setup ## Validate seed payload, birth profiles, SHA pins, and semantic-foundation closure
	@set -euo pipefail; $(USE_VENV) \
	bash ops/validate-starters.sh; \
	bash ops/audit-sha-pins.sh; \
	if python3 -c 'import yaml' >/dev/null 2>&1; then \
	  PY=python3; \
	else \
	  python3 -m venv .venv; \
	  .venv/bin/pip install --disable-pip-version-check --only-binary=:all: "pyyaml==6.0.2"; \
	  PY=.venv/bin/python; \
	fi; \
	"$$PY" scripts/validate-semantics.py

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
apply-rulesets: ## Apply org rulesets (advisory: evaluate; canonical CI: active)
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
	@rm -f /tmp/requirements-consumer-ci.txt
	@echo "clean"
