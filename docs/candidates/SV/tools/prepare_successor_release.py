#!/usr/bin/env python3
"""Prepare the Strategic Value successor release record in a canonical admission checkout.

Owner decision D4: an independent successor release, numbered at admission. The release
number and ADR identity are selected here from the checkout's merged state, never typed in:

  version = next minor after the highest docs/semantic-foundation/vX.Y.Z in the checkout,
            skipping every version an earlier-queued open PR claims (D5)
  ADR     = next number after the highest docs/adr/ADR-NNN-*.md, skipping queued claims

Queued claims are passed explicitly (``--queued v3.30.0:ADR-027``) and recorded in the release
record, so the number is reproducible and visibly provisional until those PRs are admitted.
When the queue merges, refresh the admission branch from main and run this again: it selects
again from the new merged state.

The tool writes the ADR, its index line, and the four release documents. It generates
HASHES.sha256 with the v3.21.0 procedure, runs the native validator (exit 0 required) and
proves every predecessor release directory is byte-identical. It never commits, pushes or admits.

Usage:
  python3 tools/prepare_successor_release.py --checkout ADMISSION_CHECKOUT \\
      --queued v3.30.0:ADR-027 --queued v3.31.0:ADR-028 \\
      --compiler-revision SHA --date YYYY-MM-DD [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

PACK = Path(__file__).resolve().parents[1]
RELEASES = "docs/semantic-foundation"
VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
ADR_FILE = re.compile(r"^ADR-(\d{3})-.+\.md$")
ADR_SLUG = "strategic-value-foundation-and-composition-provenance-criteria"
ADR_TITLE = (
    "Strategic Value Foundation and Catalog-Declared Composition Provenance Criteria"
)
SV_FILES = (
    "semantics/strategic_value_model.yaml",
    "semantics/strategic_planner_value_projection.schema.yaml",
    "semantics/strategic_planner_value_composition.schema.yaml",
)


class Refused(Exception):
    """A precondition does not hold; nothing is reported as prepared."""


def git(checkout: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(checkout), *args], capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise Refused(f"git {' '.join(args)}: {done.stderr.strip()[:200]}")
    return done.stdout.strip()


def versions(checkout: Path) -> list[tuple[int, int, int]]:
    found = []
    for path in (checkout / RELEASES).iterdir():
        match = VERSION.match(path.name)
        if match and path.is_dir():
            found.append(tuple(int(x) for x in match.groups()))
    return sorted(found)


def adr_numbers(checkout: Path) -> list[int]:
    return sorted(
        int(m.group(1))
        for p in (checkout / "docs" / "adr").iterdir()
        if (m := ADR_FILE.match(p.name))
    )


def parse_queue(items: list[str]) -> tuple[set[str], set[int]]:
    claimed_versions, claimed_adrs = set(), set()
    for item in items:
        match = re.fullmatch(r"(v\d+\.\d+\.\d+):ADR-(\d{3})", item)
        if not match:
            raise Refused(f"--queued must look like v3.30.0:ADR-027, got {item!r}")
        claimed_versions.add(match.group(1))
        claimed_adrs.add(int(match.group(2)))
    return claimed_versions, claimed_adrs


def select(checkout: Path, queued: list[str]) -> dict:
    claimed_versions, claimed_adrs = parse_queue(queued)
    released = versions(checkout)
    if not released:
        raise Refused(f"no release directory under {RELEASES}")
    major, minor, _ = released[-1]
    predecessor = "v{}.{}.{}".format(*released[-1])
    candidate = minor + 1
    while f"v{major}.{candidate}.0" in claimed_versions:
        candidate += 1
    adrs = adr_numbers(checkout)
    adr = adrs[-1] + 1
    while adr in claimed_adrs:
        adr += 1
    return {
        "predecessor": predecessor,
        "merged_next_version": f"v{major}.{minor + 1}.0",
        "version": f"v{major}.{candidate}.0",
        "merged_next_adr": f"ADR-{adrs[-1] + 1:03d}",
        "adr": f"ADR-{adr:03d}",
        "queued_claims": sorted(queued),
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(checkout: Path) -> dict[str, str]:
    root = checkout / RELEASES
    return {
        str(p.relative_to(checkout)): sha256(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def overlay(name: str) -> dict:
    return yaml.safe_load((PACK / "overlays" / name).read_text(encoding="utf-8"))


def facts(checkout: Path) -> dict:
    semantics = sorted(p.name for p in (checkout / "semantics").glob("*.yaml"))
    invariants = [r["id"] for r in overlay("invariants_additions.yaml")["invariants"]]
    contracts = [r["id"] for r in overlay("contracts_additions.yaml")["contracts"]]
    terms = list(overlay("vocabulary_additions.yaml")["terms"])
    projection = overlay("projection_profile_additions.yaml")["projection_profiles"][0]
    composition = overlay("composition_profile_additions.yaml")["profiles"][0]
    provenance = overlay("composition_provenance_constraints.yaml")[
        "provenance_constraints"
    ]
    decision = yaml.safe_load(
        (PACK / "evidence" / "admission" / "owner-decision.yaml").read_text(
            encoding="utf-8"
        )
    )
    if decision.get("decision_status") != "OWNER_APPROVED_NOT_ADMITTED":
        raise Refused("owner-decision.yaml is not an approved, not-admitted decision")
    return {
        "semantics": semantics,
        "invariants": invariants,
        "contracts": contracts,
        "terms": terms,
        "projection": projection,
        "composition": composition,
        "provenance": provenance,
        "decision": decision,
    }


def adr_ranges(numbers: list[int]) -> str:
    runs, start = [], numbers[0]
    for prev, cur in zip(numbers, numbers[1:] + [None], strict=False):
        if cur != prev + 1:
            runs.append((start, prev))
            start = cur
    text = [
        f"ADR-{a:03d}" if a == b else f"ADR-{a:03d} through ADR-{b:03d}"
        for a, b in runs
    ]
    return text[0] if len(text) == 1 else ", ".join(text[:-1]) + " and " + text[-1]


def ruling(f: dict, decision_id: str) -> str:
    entry = next(d for d in f["decision"]["decisions"] if d["id"] == decision_id)
    return " ".join(entry["ruling"].split())


def write_adr(checkout: Path, sel: dict, f: dict, args) -> Path:
    path = checkout / "docs" / "adr" / f"{sel['adr']}-{ADR_SLUG}.md"
    if path.exists():
        raise Refused(f"{path.name} exists")
    approved = " ".join(
        next(d for d in f["decision"]["decisions"] if d["id"] == "D1-sv001-wording")[
            "approved_statement"
        ].split()
    )
    tokens = ", ".join(f"`{t}`" for t in f["provenance"]["definitions"])
    path.write_text(
        f"""# {sel["adr"]} — {ADR_TITLE}

**Status:** Candidate for semantic-foundation {sel["version"]}. The repository owner approved decisions D1-D5 on {args.date} as an explicit instruction in governed Claude Code session `session_017xwbxytavCYavKdhRr9a6n`. Owner approval of the decisions is not admission. Admission of {sel["version"]} is the acceptance gate, after the preceding numbered releases ({", ".join(sel["queued_claims"]) or "none"}) are admitted; this record does not admit itself.

## Context

Strategic Planning needs exact admitted Strategic Value semantics: objective-relative valuation against a feasible counterfactual baseline, an exhaustive causal accounting partition, and the evidence, uncertainty and authority boundaries of a quantitative Strategic Value claim. The candidate (Quantum-L9/.github#212, reduced in #215, closed out in #220) carried twenty candidate meanings. The reduction keeps two as new global invariants. The other eighteen are kept as traceable model text with unchanged contract obligations, governed by existing law.

Its composition profile declares four `required_provenance` tokens. The Semantic Compiler had no admitted criterion for any `required_provenance` token, so every composition declaring them (this one and `l9.compose/stage-context@1`) was reported `unknown` although each named fact was intact.

## Decision

1. **D1 — `L9-SV-001`.** The original SV-001 statement followed by the original SV-015 statement, both verbatim:

   > {approved}

   `L9-SV-002` is the second and only other new invariant. `L9-SV-015` merges into `L9-SV-001`; `L9-SV-016..018` relocate to the assessment contract; `L9-SV-019` reuses `L9-UNKNOWN-001`; `L9-SV-020` reuses the evidence, assurance, provenance and coordinate invariants. The twelve earlier meanings `L9-SV-003..014` stay as model text.
2. **D2 — composition provenance (R2).** {ruling(f, "D2-composition-provenance")} Realized as `composition_profiles.yaml#provenance_constraints` in `{f["provenance"]["criterion_language"]["name"]}` v{f["provenance"]["criterion_language"]["version"]}, defining {tokens}, and the global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`. RC-033 validates the closure.
3. **D3.** {ruling(f, "D3-derived-ledger-rebinding")}
4. **D4.** {ruling(f, "D4-successor-release")} Computed, not typed in, by `docs/candidates/SV/tools/prepare_successor_release.py` (Quantum-L9/.github#220): the merged state at this branch's base gives {sel["merged_next_version"]} and {sel["merged_next_adr"]}, which earlier-queued PRs claim, so this candidate is provisionally {sel["version"]} and {sel["adr"]}. The tool re-selects from the merged state when the branch is refreshed after those PRs land.
5. **D5.** {ruling(f, "D5-merge-order")}

## Options considered

- **D1 Option A** (development-pack wording) narrowed the ranking consequence to causally attributed rankings, the safeguard to claimed causal effects, and "quantify" to "identify and justify". Independent review classified it as a weakening. Rejected.
- **D2 R1** (remove the four declarations) would have produced a PASS by deleting normative text and left `l9.compose/stage-context@1` unresolved. Kept only as a controlled contingency; not used.

## Consequences

- The compiler evaluates a `required_provenance` token only through the catalog's declared criterion; an undefined token stays unresolved, and an unknown language, criterion or parameter fails closed. No authority is created in the compiler (`Quantum-L9/l9-semantic-compiler-engine@{args.compiler_revision}`).
- `l9.compose/stage-context@1` gains the same mechanical evaluation.
- Consumers bind only through their own release process after admission and trusted replay.

## Evidence

See `docs/semantic-foundation/{sel["version"]}/RELEASE_VALIDATION.md` and the candidate pack evidence on Quantum-L9/.github#220 (`docs/candidates/SV/evidence/admission/`).
""",
        encoding="utf-8",
    )
    return path


def update_adr_index(checkout: Path, sel: dict) -> None:
    path = checkout / "docs" / "adr" / "README.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    last = max(i for i, ln in enumerate(lines) if re.match(r"^- ADR-\d{3}: ", ln))
    lines.insert(last + 1, f"- {sel['adr']}: {ADR_TITLE}\n")
    text = "".join(lines)
    sentence = re.compile(
        r"^ADR-001 through ADR-\d{3}(?:[^\n]*?)? are the global semantic decisions\.",
        re.MULTILINE,
    )
    if len(sentence.findall(text)) != 1:
        raise Refused("ADR index count sentence not found exactly once")
    numbers = adr_numbers(checkout)
    text = sentence.sub(
        f"{adr_ranges(numbers)} are the global semantic decisions.", text
    )
    path.write_text(text, encoding="utf-8")


def write_release(
    checkout: Path, sel: dict, f: dict, args, validator: dict | None
) -> Path:
    root = checkout / RELEASES / sel["version"]
    root.mkdir(parents=False, exist_ok=validator is not None)
    n_sem, n_adr = len(f["semantics"]), len(adr_numbers(checkout))
    surface = "".join(f"- `semantics/{name}`\n" for name in f["semantics"])
    queue = ", ".join(sel["queued_claims"]) or "none"
    status = "Release status: **ADDITIVE SUCCESSOR CANDIDATE**"
    (root / "MANIFEST.md").write_text(
        f"""# Semantic Foundation Manifest {sel["version"]}

{status}

## Install surface

The release contains **{n_sem}** canonical semantic YAML files:
{surface}
The {sel["predecessor"]} inventory is preserved. Three files are added: {", ".join(f"`{p}`" for p in SV_FILES)}. No ledger is removed or renamed.

## Architecture decision records

The release contains **{n_adr}** accepted ADRs plus the ADR index under `docs/adr/`.

{sel["version"]} adds {sel["adr"]} ({ADR_TITLE.lower()}), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/invariants.yaml`: {", ".join(f"`{i}`" for i in f["invariants"])} (D1: `L9-SV-001` is the original SV-001 then the original SV-015, verbatim).
- `semantics/contracts.yaml`: {", ".join(f"`{c}`" for c in f["contracts"])}; derivation digest and count rebound.
- `semantics/vocabulary.yaml`: {len(f["terms"])} terms ({", ".join(f"`{t}`" for t in f["terms"])}).
- `semantics/strategic_value_model.yaml` (`l9.strategic.value@1`), registered in `canonical_sources.yaml`, `generic_compiler_manifest.yaml#requires.semantic_catalogs` and as source class `strategic_value_model`.
- `semantics/projection_profiles.yaml`: `{f["projection"]["id"]}` over {", ".join(f"`{s}`" for s in f["projection"]["sources"])}.
- `semantics/composition_profiles.yaml`: `{f["composition"]["id"]}` (source-class namespace, exact coverage); `provenance_constraints` (`{f["provenance"]["criterion_language"]["name"]}` v{f["provenance"]["criterion_language"]["version"]}, {len(f["provenance"]["definitions"])} definitions) and global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`.
- Payload schemas `semantics/strategic_planner_value_projection.schema.yaml` and `semantics/strategic_planner_value_composition.schema.yaml`, registered in `requires.artifact_schemas`.
- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`: derivation sha256 and item counts only (D3).
- `scripts/validate-semantics.py`: RC-033 (provenance-constraint closure) with 8 negative cases.
- `docs/adr/README.md`: indexes {sel["adr"]}.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/{sel["predecessor"]}/`, preserved unchanged.
""",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        f"""# Semantic Foundation {sel["version"]}

Status: **ADDITIVE SUCCESSOR CANDIDATE**

{sel["version"]} admits the Strategic Value foundation as two global invariants with a claim-scoped assessment contract, one value model, one consumer projection profile and its source-namespaced composition. Every `required_provenance` token becomes mechanically verifiable through criteria the composition catalog declares.

## Bounded delta

Successor to {sel["predecessor"]}. Release number and ADR identity were selected from merged state at {args.base} with earlier-queued claims {queue} skipped (owner decision D4/D5); they are re-selected if the queue changes before admission.

- Two invariants, one contract, {len(f["terms"])} vocabulary terms, the value model, `{f["projection"]["id"]}`, `{f["composition"]["id"]}` and their two payload schemas.
- `provenance_constraints` in the composition catalog and validator RC-033.
- Derivation-coordinate rebinding of capabilities, lifecycle and receipt catalog.
- {sel["adr"]}.

## Evidence

Owner decisions D1-D5: Quantum-L9/.github#220 `docs/candidates/SV/evidence/admission/owner-decision.yaml`. Producer: `Quantum-L9/l9-semantic-compiler-engine@{args.compiler_revision}`. Qualification receipts and the provenance verification are recorded in that pack, bound to the exact admission revision.

## Outstanding Unknowns and findings

- The explicit decision record that `authority_model.admission_rules` requires still has no defined form in a ledger (the v3.24.0 finding); {sel["adr"]} follows the ADR-025 precedent.
- The compiler change is not yet a released compiler version; the producer is pinned by revision.

## Authority

`Quantum-L9/.github` owns these ledgers. Valuation is derived and non-authoritative: it grants no plan admission, strategic commitment, execution, publication, merge, admission or deployment authority. This candidate does not admit itself.
""",
        encoding="utf-8",
    )
    passes = validator["pass_lines"] if validator else "PENDING"
    (root / "RELEASE_VALIDATION.md").write_text(
        f"""# Release Validation {sel["version"]}

Candidate status: **additive successor candidate**.

## Strategic Value and composition provenance closure

- **SC-001** parses {n_sem} canonical sources as YAML mappings, including the three added files.
- **SC-004** binds the contracts derivation to the new invariants digest and count; **RC-001**, **RC-002** and **RC-011** bind capabilities, lifecycle and receipt catalog to the rebound digests (D3).
- **RC-006** finds `strategic_value_model.yaml` in both the source registry and `semantic_catalogs`.
- **RC-033** proves every `required_provenance` token of `l9.compose/stage-context@1` and `{f["composition"]["id"]}` is defined in `provenance_constraints` with an implemented criterion; its 8 negative cases fail closed.
- **SC-008** proves this release record: **{n_sem}** canonical sources, **{n_adr}** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

## Existing closure

`scripts/validate-semantics.py` exits 0 with {passes} PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

{sel["version"]} is a candidate and does not admit itself. Owner approval of decisions D1-D5 is recorded; canonical admission and post-merge trusted replay are separate and not yet performed.
""",
        encoding="utf-8",
    )
    return root


def write_hashes(checkout: Path, version: str) -> None:
    root = checkout / RELEASES / version
    lines = []
    for p in sorted((checkout / "semantics").glob("*.yaml")):
        lines.append((f"./semantics/{p.name}", sha256(p)))
    for p in sorted((checkout / "docs" / "adr").glob("ADR-*.md")):
        lines.append((f"./docs/adr/{p.name}", sha256(p)))
    lines.append(
        ("./docs/adr/README.md", sha256(checkout / "docs" / "adr" / "README.md"))
    )
    for name in ("MANIFEST.md", "README.md", "RELEASE_VALIDATION.md"):
        lines.append((f"./{name}", sha256(root / name)))
    lines.sort(key=lambda item: item[0].encode("utf-8"))
    (root / "HASHES.sha256").write_text(
        "".join(f"{h}  {p}\n" for p, h in lines), encoding="utf-8"
    )


def run_validator(checkout: Path) -> dict:
    done = subprocess.run(
        [sys.executable, "scripts/validate-semantics.py"],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=False,
    )
    out = done.stdout.splitlines()
    return {
        "exit": done.returncode,
        "pass_lines": sum(1 for ln in out if ln.startswith("PASS")),
        "fail_lines": [ln for ln in out if ln.startswith("FAIL")][:20],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--queued", action="append", default=[])
    parser.add_argument("--compiler-revision", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        checkout = args.checkout.resolve()
        if git(checkout, "status", "--porcelain", "--untracked-files=no"):
            raise Refused(
                "checkout has tracked changes; commit the semantic change first"
            )
        if not re.fullmatch(r"[0-9a-f]{40}", args.compiler_revision):
            raise Refused("--compiler-revision must be a full 40-hex commit")
        for rel in SV_FILES:
            if not (checkout / rel).is_file():
                raise Refused(
                    f"{rel} missing; apply the candidate before cutting its release"
                )
        args.base = git(checkout, "rev-parse", "HEAD")
        sel = select(checkout, args.queued)
        if args.dry_run:
            print(json.dumps(sel, indent=2))
            return 0
        if (checkout / RELEASES / sel["version"]).exists():
            raise Refused(f"{sel['version']} already exists")
        before = snapshot(checkout)
        f = facts(checkout)
        write_adr(checkout, sel, f, args)
        update_adr_index(checkout, sel)
        f = facts(checkout)
        write_release(checkout, sel, f, args, None)
        write_hashes(checkout, sel["version"])
        first = run_validator(checkout)
        write_release(checkout, sel, f, args, first)
        write_hashes(checkout, sel["version"])
        final = run_validator(checkout)
        if final["exit"] != 0 or final["pass_lines"] != first["pass_lines"]:
            raise Refused(f"native validation did not settle: {final}")
        after = snapshot(checkout)
        changed = sorted(k for k in before if before[k] != after.get(k))
        if changed:
            raise Refused(f"predecessor release bytes changed: {changed}")
        print(
            json.dumps(
                {**sel, "validator": final, "predecessors_unchanged": True}, indent=2
            )
        )
        return 0
    except Refused as exc:
        print(json.dumps({"result": "REFUSED", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
