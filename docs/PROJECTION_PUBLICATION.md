# Projection publication

`scripts/publish-projection.py` moves producer-emitted semantic projections
from the Semantic Compiler to the `projections` branch of this repository.
It is separate from governance distribution (`docs/DISTRIBUTION.md`): Manual
Update and Manual Seed do not call it, and it does not call them.

**Status: implemented, not activated.** No workflow runs it, and the remote
`projections` branch does not exist. See [Activation](#activation).

## Roles

| Component | Role | Never |
| --- | --- | --- |
| `Quantum-L9/.github` `main` | Canonical sources, profiles, contracts, and this publisher | Holds generated projections |
| `l9-semantic-compiler` | Produces the artifact/receipt pair (`semantics/vocabulary.yaml` gives it the `projection` role) | Publishes |
| `scripts/publish-projection.py` | Verifies a pair, stages it, advances `projections` | Runs the compiler, executes selectors, builds or repairs a pair |
| `Quantum-L9/.github` `projections` | Immutable pairs plus a transport index | Holds authority |
| Consumers (e.g. the coding agent's `verify_canonical_binding.py`) | Verify independently | Run the producer |

## Scope

One profile and source class:
`l9.projection/cursor-governance-operating-plane@1` / `invariants`
(`l9.source/invariants@1`, selector `$.invariants[?(@.scope=="global")]`).
A class with more than one selector, or with a declared reshape, has no
producer-defined payload shape and is refused as `UNSUPPORTED_SOURCE_CLASS`.

## Trust

- **Revision pin.** Every command takes `--revision`, a 40-hex canonical
  `main` SHA. It must come from an independent record of canonical `main`
  (for example `gh api repos/Quantum-L9/.github/commits/main --jq .sha`),
  never from a receipt, the index, or the checkout being checked. The
  authority checkout must have origin `Quantum-L9/.github`, and the pin must
  be contained in a fetched `origin` ref; otherwise the run is `BLOCKED`.
- **Law bytes** are read from the pinned commit's objects, never from the
  working tree or index.
- **Digests** use the producer's conventions, recomputed here: sha256 of raw
  source bytes, and sha256 of canonical JSON (sorted keys, compact, UTF-8)
  for the payload, the profile entry, and the receipt.
- **Receipts are unsigned.** A verified pair proves digest integrity and the
  producer role. It does not authenticate the producer. Every index record
  says `producer_authentication: unauthenticated_unkeyed_receipt`.
- **Compiler revision** is recorded as `caller_asserted`.

## Layout of `projections`

```
index.json
pairs/<source_class>/<receipt digest hex>/projection.json
pairs/<source_class>/<receipt digest hex>/receipt.json
```

Pair bytes are exactly the producer's files. `index.json` is a transport
locator (`transport_format: quantum-l9-github/projections-index@1`), not
semantic law. Per `<profile>#<source_class>` it records the current pair
(path, file sha256s, projection and receipt digests, source and profile
digests, authority revision, compiler name/version/revision) and every
prior current pair under `history`. `previous_publication` names the parent
commit; a commit cannot name itself, so the publication coordinate is the
commit a consumer resolved.

## Commands

```bash
PIN=$(gh api repos/Quantum-L9/.github/commits/main --jq .sha)   # independent record
AUTH=/path/to/Quantum-L9-.github   # fetched, HEAD == $PIN, clean semantics/

# 1. Pins for the producer
python3 scripts/publish-projection.py pins --authority-root "$AUTH" --revision "$PIN"

# 2. Producer (in its own checkout, at an exact compiler revision)
l9-semantic-compiler project --authority-root "$AUTH" \
  --profile l9.projection/cursor-governance-operating-plane@1 --source-class invariants \
  --output-dir OUT --authority-revision "$PIN" \
  --expect-source-digest <source_digest> --expect-profile-digest <profile_digest>

# 3. Verify, then plan (writes nothing)
python3 scripts/publish-projection.py verify  --authority-root "$AUTH" --revision "$PIN" --pair-dir OUT/invariants/<hex>
python3 scripts/publish-projection.py publish --authority-root "$AUTH" --revision "$PIN" --pair-dir OUT/invariants/<hex> \
  --repo "$AUTH" --remote origin --compiler-revision <compiler sha>

# 4. Check a published commit (consumer side or post-publish)
python3 scripts/publish-projection.py check --authority-root "$AUTH" --revision "$PIN" --repo "$AUTH" --commit <publication sha>
```

`publish` only plans unless `--apply` is given.

## Publication rules

- **One commit.** The pair and the updated index land in one commit on the
  current tip, so the index is never published ahead of its pair. A run
  interrupted before the ref moves leaves the branch and index untouched.
- **Advance.** Locally by `git update-ref <ref> <new> <old>` (compare and
  swap). Remotely by a plain, non-force push after confirming the remote tip
  equals the base; the server refuses anything that is not a fast-forward.
  A lost race is `CONFLICT` (exit 5): re-run from the new tip. The publisher
  has no force, reset, or `+refspec` path.
- **Never creates the branch.** An absent target branch is
  `BLOCKED TARGET_REF_ABSENT`.
- **Immutable pairs.** Identical replay is `NOOP_IDENTICAL`. Different bytes
  at an existing pair path is `IMMUTABLE_PATH_COLLISION`. Prior pairs stay.
- **Unrelated revisions.** A newer pin whose source and profile digests are
  unchanged is `NOOP_UNCHANGED_SEMANTICS`; nothing is republished.
- **Material changes.** Published as the new current pair, only from a
  descendant of the current entry's revision (`ROLLBACK_REFUSED` otherwise),
  and only while the fetched canonical `main` tip still has the same source
  and profile digests (`STALE` otherwise).
- **Coherent reads.** `check` resolves one commit and reads the index and
  the pair from it, compares file hashes with the index, re-verifies the
  pair, and reports `CURRENT`, `STALE` (material change at the pin), or
  `REJECTED`.

Exit codes: 0 ok, 1 `REJECTED`, 2 usage, 3 `BLOCKED`, 4 `STALE`, 5 `CONFLICT`.

## Tests

`python3 scripts/test-publish-projection.py` (CI: `validate-starters.yml`,
semantics job). Disposable local git repositories only; pairs are a fixture
following the producer's documented conventions. A real producer pair is
exercised in the PR evidence, not in CI: the compiler repository is private.

## Activation

Not authorized by the implementation PR. Each item needs separate approval
and proof:

1. The Semantic Compiler `project` CLI merged and adopted at an exact SHA.
2. A publisher runner with read access to that compiler revision, and write
   access restricted to `refs/heads/projections`, with branch protection
   observed (not assumed). Compiler code must never run with that write
   credential.
3. An operator creates `projections` (the publisher will not).
4. A protected manual run publishes, then `check` and a clean consumer
   (`verify_canonical_binding.py`, no compiler import) reach `BOUND` and
   `CURRENT` at the published commit, with live negative controls.
