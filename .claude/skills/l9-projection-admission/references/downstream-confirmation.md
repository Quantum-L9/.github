<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: downstream-contract
version: 2.0.0
status: active
-->

# Confirming downstream usability

"Usable downstream" means the real producer compiles the admitted semantics to PASS at a protected `main` revision, and every byte it emitted verifies on its own. The producer is the `l9-semantic-compiler-engine` CLI, `l9-semantic-compiler`. A consumer then bundles, verifies and replays that output. Reading the YAML proves none of this, and neither does the compiler's own `result: pass`.

## Producer run (what `check_admission_closure.py --compiler-src` does)

1. **Exact producer.** The compiler checkout must be a git checkout with no tracked changes and no untracked files (an untracked `src/json.py` would shadow an import). `--compiler-revision <sha>` pins it further. Otherwise the run is not an exact revision: a non-git checkout is UNRESOLVED, and a dirty one fails.
2. `projection-coordinates --authority-root <checkout> --revision <sha> --repository Quantum-L9/.github --profile <projection ref>` prints the pinned `projection_profile {ref, digest}` and `sources [{ref, digest}]`.
3. `project <request>` takes a request with schema `l9.semantic-projection-request/v1`, carrying `authority {repository, root, revision}`, the pins and `output_root`.
4. `compose <request>` takes a request with schema `l9.semantic-composition-request/v1`, carrying `composition_profile {ref, digest}` and `components` (the projection artifact paths). The CLI has no coordinates command for compositions. The digest is the sha256 of the profile record's canonical JSON (sorted keys, `(",", ":")` separators, UTF-8), and the script computes it.
5. The whole run happens twice, into `run-1/` and `run-2/` under `--output-root`.

An artifact counts only with `result: pass` **and** an explicitly empty `unresolved_criteria`. A missing list is not empty. Exit 3 or `result: unknown` is not usable: read `unresolved_criteria` and fix the cause, never the declaration.

The authority checkout must be clean at the revision you name. DOWNSTREAM_USABLE also requires `HEAD == origin/main` (`head_is_main`).

## Independent verification (`verify_admission_evidence.verify_outputs`)

Every emitted file is re-read from disk and checked against the authority tree, not against the compiler's summary.

| Check | Projection artifact | Composition artifact | Receipt |
| --- | --- | --- | --- |
| Bytes | sha256 of the file equals the reported `content_digest` | same | `receipt_digest` recomputes and equals the reported one |
| Envelope | `schema: l9.projection-artifact/v1`; `projection_digest` recomputes and equals the reported digest | `schema: l9.composed-projection/v1`; `composition_digest` recomputes | `result: pass`, `coverage: complete`, `unresolved_criteria: []`, every criterion `pass` or `not_applicable` |
| Provenance | profile digest is `digest(profile record)` at HEAD; `source_digest` is the sha256 of the source file at HEAD; the compiler's pins agree | `composition_profile` digest at HEAD; each component's projection digest, source ref and source digest equal the verified projection's | `output`, `profile` and `inputs` (including `revision` and source `path`) are exactly this artifact's |
| Coverage | emitted sources are exactly the profile's *registered* sources (independent of the compiler's pins) | components are exactly the verified projections, with no duplicate; each component's `source_class` is the class its source is bound to in the registry, never the artifact's own label | |
| Selection | the payload **equals** the exact record-preserving selection of the source, recomputed independently with the `l9.selector/v1` semantics. Every field, value and record is compared, in source order. | the payload is exactly `{registered source class: verified component payload}`. A deep-merge composition cannot be recomputed here, so it fails closed. | |
| Payload schema | the compiler's native interpreter (`passes.validate.schema_violations`) reports no violation, **and** strict typed const/enum equality holds, so a `1` never passes a Boolean `true` | same, against the composition schema | |

**Negative controls.** For each verified artifact, the gate corrupts one mechanism at a time and re-seals the self-digest. It then requires rejection by that mechanism's own check. The mechanisms are:

- projections: source digest, profile digest, an unsealed payload edit, a dropped selected record, an altered selected value, and a removed schema-required field;
- compositions: a duplicate component, a missing component, a relabelled namespace, an altered namespace payload, and a component digest.

A control that is accepted fails downstream.

**Replay.** `run-1/` and `run-2/` must hold the same files with the same bytes, excluding the gate's own `requests/`.

Real-repository evidence (main `9488d8f`, compiler `18215ae`): `l9.projection/authority-resolution@1` and `l9.compose/authority-resolution@1` produced 4 projections and 1 composition. All of them verified, 19 controls were rejected, and 10 files replayed byte-identically.

## Consumer side (`docs/PROJECTION_PUBLICATION.md`)

- A consumer commits a bundle (`projections/`, `receipts/`, `composed.json`, lock) and verifies it without running the producer. A failure there is `REJECTED`, `STALE` or `BLOCKED`.
- Production is attested only by **trusted replay**. The consumer's default-branch workflow checks out this repository at the lock's authority revision and the producer at its revision, confirms both are on protected `main`, regenerates the bundle, and compares it byte for byte.
- The current consumers live in `Cursor-Governance` (`.github/workflows/l9-projection-bundle-verify.yml`, `l9-projection-bundle-trusted-replay.yml`, `generated/governance/<profile>/`). Binding a consumer is that repository's change, through its own release process, never this one's.

## Wording discipline

| You observed | Say |
| --- | --- |
| Gate verdict `DOWNSTREAM_USABLE` | "admitted and compiles to verified PASS at main `<sha>` with compiler `<sha>`" |
| Projection PASS on a candidate branch | "rehearsal PASS at `<sha>`, not admitted" |
| Consumer bundle verified | "verified, not admitted" (unless the gate also says ADMITTED) |
| Trusted replay green in a consumer | "production attested by replay at `<sha>`" |
