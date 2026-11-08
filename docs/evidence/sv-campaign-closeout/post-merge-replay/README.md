# Post-merge replay at `64d8b85`

Run on a clean checkout of `Quantum-L9/.github` `main` at `64d8b8598300f94c3201f26866f73be6895dab60`, 2026-11-08.

| Check | Result | File |
|---|---|---|
| Five SV source projections, producer `33e4c58` | 5/5 pass | `producer-summary-33e4c58.json` |
| SV composition | pass, digest `sha256:7e93f3af…08e38e7` (same as pre-merge), 4/4 `required_provenance` pass | same |
| Stage-context regression | 4/4 `required_provenance` pass; overall `unknown` from 8 unrelated `payload_schema` criteria | same |
| Second run, same producer | 29 artifact, receipt and summary files byte-identical; request files differ only in the absolute output path | `artifacts-33e4c58.sha256` |
| Compiler `main` 39a51b7 cross-check | identical artifacts and receipts | `producer-summary-39a51b7.json`, `artifacts-39a51b7.sha256` |
| Independent provenance verifier | PASS, 8/8 checks, against revision `64d8b85` | `provenance-verifier.json` |
| `l9-projection-admission --require downstream` | `DOWNSTREAM_USABLE`: registration, release (ADMITTED, current), validator and downstream pass | `admission-closure.json` |
| `scripts/validate-semantics.py` | exit 0, 59 PASS, 0 FAIL | `validate-semantics.log` |
| Run archive | the full 33e4c58 run output | `producer-run-33e4c58.tar.gz` |

`producer-summary-39a51b7.json` reports a `compiler_revision` of a local snapshot commit; see `../compiler-lock.yaml`. Absolute sandbox paths inside `admission-closure.json` and the archive are not portable.

This replay is producer-side. It is not consumer binding: consumers bind through their own release process.
