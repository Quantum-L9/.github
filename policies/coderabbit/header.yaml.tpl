# Rendered by Quantum-L9/.github ops/render-coderabbit.js; do not edit by hand.
# ADR: docs/adr/0020-coderabbit-central-config-seeded.md
#
# The same bytes are the organization central configuration (repository
# Quantum-L9/coderabbit, `.coderabbit.yaml` at its root) and the missing-only
# seed written to a consumer root where none exists; an existing consumer file
# (its own path_instructions, tools) is never replaced. With `inheritance:
# true` on both levels CodeRabbit merges lists repository entries first, then
# appends the unique central entries.
#
# reviews.path_filters is EXCLUSIONS ONLY. An exclusion (`!`) always wins, and
# a single pattern without `!` turns the whole list into an allowlist, so every
# file it does not name is skipped. Add a `!` pattern or nothing.
# Tests and docs are reviewed: never exclude them.
inheritance: true
reviews:
  path_filters:
    {{path_filters}}
