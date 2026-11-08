# Candidate source-field grammars: architecture-intelligence

**Status: candidate, owner review pending. Not canonical, not admitted, not registered.**
Nothing here is semantic authority. It is the governance input that `schema-synthesize`
(`Quantum-L9/l9-semantic-compiler-engine`) requires before it can generate payload schemas.
Admission of any part of it is the code owner's decision.

## What it targets

| Item | Value |
|---|---|
| Projection profile | `l9.projection/architecture-intelligence@1` |
| Composition profile | `l9.compose/architecture-intelligence@1` (namespaced, composes exactly that projection) |
| Output schemas | `l9.projection.architecture-intelligence/v1`, `l9.composed-projection.architecture-intelligence/v1` |
| Sources | 24 source classes, one grammar each |
| Authority revision | recorded in `grammar-draft-report.yaml` (`authority_revision`) |

Of every projection profile that selects a source `.github#217` (v3.29.0) changed, this is the
only one with a namespaced composition profile, so it is the only one `schema-synthesize` can
run on. The Stage 14/15 profiles that read #217's `l9.binding/python-gate-node@1`
(`stage-implementation@1`, `stage-target-artifacts@1`) have no composition profile; their
schemas cannot be synthesized until one is admitted.

## Two layers per grammar

| Layer | Content | Basis |
|---|---|---|
| Structural | `type`, `fields`, `items`, and `additional_properties: true` on every object | Scaffolded from the pinned source bytes by `tools/build_schema_grammar_candidate.py` in the compiler repository. Carries no normative constraint, is not independent evidence, and trivially admits the bytes it came from. |
| Normative | `required`, `const` | Only the entries in that tool's `OVERLAY`, each citing canonical text, recorded per grammar in `grammar-draft-report.yaml`. |

No `required`, `const`, `enum` or `min_items` is inferred from observed values. Every
object is declared open (`additional_properties: true`), because synthesis requires an
explicit declaration and open infers nothing from the keys observed; closing an object is
owner review. An empty list is drafted as `string_list` unless a
sibling occurrence shows a typed list; owner review must confirm each.

The only normative layer is #217's, on `product_manifest`: `$.properties` requires
`interfaces` and `effects`, and both have `type` `const: object` (ADR-026). Everything else an
owner wants enforced is review work.

## Files

| Path | Role |
|---|---|
| `grammars/<source_class>.yaml` | 24 source-field grammar candidates |
| `grammar-draft-report.yaml` | Authority revision, grammar digests, normative overlay, inexpressible paths (none) |
| `operation.yaml`, `dialect.yaml`, `bindings.yaml` | Governance candidates; the binding catalog pins the grammar commit |
| `RUN.md` | The compiler run, its exit code and result |

## Pins

The binding catalog pins the grammars' own commit, and a request pins the catalog's commit,
so the pack is written in two commits. A squash merge replaces both commits, so after merge
the catalog must be re-pinned to the merged revision (re-run the `catalog` phase) before a
request can name commits on `main`.

## Reproduce

From a compiler checkout, against a clone of this repository:

```bash
GH=/path/to/Quantum-L9/.github
python tools/build_schema_grammar_candidate.py grammars --github-root "$GH" --authority-revision "$AUTHORITY"
# commit the pack in $GH -> G1
python tools/build_schema_grammar_candidate.py catalog --github-root "$GH" --grammar-revision "$G1"
# commit -> G2
python tools/build_schema_grammar_candidate.py request --github-root "$GH" --governance-revision "$G2" \
  --compiler-revision "$(git rev-parse HEAD)" --compiler-executable-digest "sha256:<digest>" \
  --output /outside/any/worktree/request.yaml
l9-semantic-compiler schema-synthesize /outside/any/worktree/request.yaml
```

## Not established

Owner approval of any grammar; independence of the structural layer from the bytes it
describes; schemas for the Stage 14/15 profiles; compatibility with legacy producers and
consumers; admission.
