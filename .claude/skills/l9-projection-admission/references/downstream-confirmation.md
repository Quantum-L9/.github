<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: downstream-contract
version: 1.0.0
status: active
-->

# Confirming downstream usability

"Usable downstream" means the real producer, `l9-semantic-compiler-engine:` CLI `l9-semantic-compiler`, compiles the admitted semantics to PASS at a protected `main` revision. A consumer then bundles, verifies and replays that output. Reading the YAML proves none of this.

## Producer run (what `scripts/check_admission_closure.py --compiler-src` does)

1. `projection-coordinates --authority-root <checkout> --revision <sha> --repository Quantum-L9/.github --profile <projection ref>` prints the pinned `projection_profile {ref, digest}` and `sources [{ref, digest}]`.
2. `project <request>` takes a request with schema `l9.semantic-projection-request/v1`, carrying `authority {repository, root, revision}`, the pins and `output_root`. Every artifact must report `result: pass`.
3. `compose <request>` takes a request with schema `l9.semantic-composition-request/v1`, carrying `composition_profile {ref, digest}` and `components` (the projection artifact paths). The CLI has no coordinates command for compositions. The digest is the sha256 of the profile record's canonical JSON (sorted keys, `(",", ":")` separators, UTF-8), and the script computes it.
4. Exit 3 or `result: unknown` is not usable. Read `unresolved_criteria` and fix the cause; never the declaration.

The checkout must be clean at the revision you name. The script refuses tracked changes and reports `head_is_main`, and DOWNSTREAM_USABLE requires `HEAD == origin/main`.

## Consumer side (`docs/PROJECTION_PUBLICATION.md`)

- A consumer commits a bundle (`projections/`, `receipts/`, `composed.json`, lock) and verifies it without running the producer. A failure there is `REJECTED`, `STALE` or `BLOCKED`.
- Production is attested only by **trusted replay**. The consumer's default-branch workflow checks out this repository at the lock's authority revision and the producer at its revision, confirms both are on protected `main`, regenerates the bundle, and compares it byte for byte.
- The current consumers live in `Cursor-Governance` (`.github/workflows/l9-projection-bundle-verify.yml`, `l9-projection-bundle-trusted-replay.yml`, `generated/governance/<profile>/`). Binding a consumer is that repository's change, through its own release process, never this one's.

## Wording discipline

| You observed | Say |
| --- | --- |
| Gate verdict `DOWNSTREAM_USABLE` | "admitted and compiles to PASS at main `<sha>`" |
| Projection PASS on a candidate branch | "rehearsal PASS at `<sha>`, not admitted" |
| Consumer bundle verified | "verified, not admitted" (unless the gate also says ADMITTED) |
| Trusted replay green in a consumer | "production attested by replay at `<sha>`" |
