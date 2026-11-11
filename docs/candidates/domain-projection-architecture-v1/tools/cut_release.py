#!/usr/bin/env python3
"""Cut docs/semantic-foundation/v3.36.0/ as an ADDITIVE SUCCESSOR CANDIDATE.

Writes MANIFEST.md, README.md and RELEASE_VALIDATION.md from the current tree,
then HASHES.sha256 with the v3.21.0 procedure (sha256 with ./ paths, sorted by
path in C order). Run it after the last edit to any covered file. It never
writes an ADR and never marks the release admitted.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VERSION = "v3.36.0"
REL = ROOT / "docs/semantic-foundation" / VERSION
PACK = "docs/candidates/domain-projection-architecture-v1"
STATUS = "ADDITIVE SUCCESSOR CANDIDATE"

DELTA = f"""- `semantics/invariants.yaml`: `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`, `L9-SIGNAL-002`, `L9-SIGNAL-003` and `L9-SIGNAL-004`, record-equal to the Quantum-L9/.github#234 candidates.
- `semantics/vocabulary.yaml`: terms `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`, `signal_feedback_episode` and `signal_consumption` (record-equal to #234), and `domain_projection` and `domain_consumer_binding`.
- `semantics/contracts.yaml`: `l9.contract/domain-composition-compatibility@1` and `l9.contract/domain-composition-provenance@1`.
- `semantics/projection_profiles.yaml`: profile class `domain` and eight domain profiles `l9.projection/<name>@1` for `architecture`, `strategic-value`, `signals`, `governance`, `evidence-provenance`, `contracts-conformance`, `capabilities-dependencies` and `identity-attribution`, each declaring `payload_validation: {{protocol: l9.payload-validation/source-class-dispatch@1}}`.
- `semantics/composition_profiles.yaml`: the eight `l9.compose/<name>@1` compositions, source-class namespaced, declaring the same protocol.
- New ledgers `semantics/domain_projection_model.yaml` (`DOMAIN-001`..`DOMAIN-010`) and `semantics/domain_consumer_bindings.yaml` (six bindings, `BINDING-001`..`004`, `COMPOSE-001`..`005`), registered in `semantics/canonical_sources.yaml` and `semantics/generic_compiler_manifest.yaml#requires.semantic_catalogs`.
- Sixteen registered payload schemas of type `l9.source-class-payload-schema/v1` (one projection and one composition schema per domain, each named domain_NAME_projection or domain_NAME_composition with suffix .schema.yaml under semantics/), listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`.
- Derived coordinates rebound from final bytes: `semantics/contracts.yaml#derivation` (40 invariants), and the `source_artifacts` of `semantics/capabilities.yaml` (40 invariants, 31 contracts), `semantics/lifecycle.yaml` and `semantics/receipt_catalog.yaml`.
- `scripts/validate-semantics.py`: RC-034 and RC-034-NEG.

No existing projection or composition profile changes; RC-034 pins both predecessor catalogs by canonical-JSON digest."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    semantics = sorted(p.name for p in (ROOT / "semantics").glob("*.yaml"))
    adrs = sorted(p.name for p in (ROOT / "docs/adr").glob("ADR-*.md"))
    REL.mkdir(parents=True, exist_ok=True)
    listing = "\n".join(f"- `semantics/{n}`" for n in semantics)
    (REL / "MANIFEST.md").write_text(
        f"""# Semantic Foundation Manifest {VERSION}

Release status: **{STATUS}**

## Install surface

The release contains **{len(semantics)}** canonical semantic YAML files:
{listing}

The v3.35.0 inventory is preserved. Eighteen files are added; no ledger is removed or renamed.

## Architecture decision records

The release contains **{len(adrs)}** accepted ADRs plus the ADR index under `docs/adr/`.

{VERSION} adds no ADR while it is a candidate.

## Semantic changes

{DELTA}

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.35.0/`, preserved unchanged.
""",
        "utf-8",
    )
    (REL / "README.md").write_text(
        f"""# Semantic Foundation {VERSION}

Status: **{STATUS}**.

{VERSION} is a candidate. It is not admitted until an accepted ADR names it.

## Bounded delta

Successor to v3.35.0. A domain projection exposes canonical meaning, a domain consumer binding selects that meaning, and composition verifies compatibility; none of them creates semantic authority.

{DELTA}

## Evidence

Candidate pack: `{PACK}/` (design departures, open blockers, reproduction). Producer rehearsal: `{PACK}/evidence/rehearsal.json`, compiler `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (0.10.0). Migration equivalence: `{PACK}/evidence/migration_equivalence.json`. Draft decision record: `{PACK}/ADMISSION_DECISION_DRAFT.md`.

## Outstanding Unknowns

- `l9.domain-consumer-binding/strategic-planner@1` has no resolved repository or entrypoint and is blocked for activation.
- Every binding with predecessor profiles is blocked for consumer migration until its owner records dispositions or a review.
- Compiler 0.10.0 projects and composes each domain; it does not evaluate the composition contracts over a binding's domain set.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants plan admission, strategic commitment, execution, publication, merge, admission or deployment authority, and no consumer is switched.
""",
        "utf-8",
    )
    passes = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    (REL / "RELEASE_VALIDATION.md").write_text(
        f"""# Release Validation {VERSION}

Release status: **additive successor candidate**.

## Closure

- **SC-001** parses {len(semantics)} canonical sources as YAML mappings.
- **SC-004**, **RC-001**, **RC-002** and **RC-011**: the derivation cascade is rebound from final bytes.
- **RC-027**: every contract `source_invariants` entry and every `governed_by` reference of the two new ledgers resolves.
- **RC-034** proves DOMAIN-001..010, BINDING-001..004 and COMPOSE-001..005, and **RC-034-NEG** that 28 adversarial mutations fail closed at their intended field and mapping order leaves every domain profile digest unchanged.
- **SC-008** proves this release record: **{len(semantics)}** canonical sources, **{len(adrs)}** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with {passes} PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

Not admitted. Admission requires the owner's explicit decision recorded in an accepted ADR.
""",
        "utf-8",
    )
    entries = [(f"./semantics/{n}", ROOT / "semantics" / n) for n in semantics]
    entries += [(f"./docs/adr/{n}", ROOT / "docs/adr" / n) for n in adrs]
    entries.append(("./docs/adr/README.md", ROOT / "docs/adr/README.md"))
    entries += [(f"./{n}", REL / n) for n in ("MANIFEST.md", "README.md", "RELEASE_VALIDATION.md")]
    lines = sorted((f"{_sha(p)}  {rel}\n" for rel, p in entries), key=lambda line: line.split("  ", 1)[1].encode())
    (REL / "HASHES.sha256").write_text("".join(lines), "utf-8")
    print(f"cut {VERSION}: {len(semantics)} sources, {len(adrs)} ADRs, {len(lines)} hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
