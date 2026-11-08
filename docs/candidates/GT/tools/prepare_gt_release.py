#!/usr/bin/env python3
"""Prepare a Game Theory successor release record in a canonical admission checkout.

Two subjects, each its own release (campaign contract Articles 7.5 and 8.5):

* ``--stage core``: L9-GT-001, the GT-only contract, twelve terms, the GT
  projection and composition profiles, the SV-exclusion criterion and both
  native payload schemas.
* ``--stage dependent``: ``l9.contract/strategic-value-interaction-composition@1``
  over the admitted SV and GT foundations.

The release number and ADR identity are selected from the checkout's merged
state, never typed in: next minor after the highest
``docs/semantic-foundation/vX.Y.Z`` and next ADR number after the highest
``docs/adr/ADR-NNN-*.md``.

The tool writes the ADR, its index line and the release documents, all as a
**candidate**. It generates ``HASHES.sha256`` with the v3.21.0 procedure, runs
the native validator (exit 0 required) and proves every predecessor release
directory is byte-identical. Admission is a separate, owner-decided edit. The
tool never commits, pushes or admits.

Usage:
  python3 tools/prepare_gt_release.py --checkout CHECKOUT --stage core \\
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
FULL_SHA = re.compile(r"[0-9a-f]{40}")
RELEASE_DOCS = ("MANIFEST.md", "README.md", "RELEASE_VALIDATION.md")
ADR_INDEX = "README.md"
DECISION = "evidence/admission/gt-owner-decision.yaml"
GT_SCHEMAS = (
    "semantics/strategic_interaction_projection.schema.yaml",
    "semantics/strategic_interaction_composition.schema.yaml",
)
STAGES = {
    "core": {
        "slug": "game-theory-core-conditional-strategic-interaction",
        "title": "Game Theory Core: Conditional Strategic Interaction",
        "added": GT_SCHEMAS,
    },
    "dependent": {
        "slug": "strategic-value-interaction-composition-contract",
        "title": "Strategic Value and Game Theory Interaction Composition Contract",
        "added": (),
    },
}


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


def select(checkout: Path) -> dict:
    released = versions(checkout)
    if not released:
        raise Refused(f"no release directory under {RELEASES}")
    major, minor, _ = released[-1]
    adrs = adr_numbers(checkout)
    return {
        "predecessor": "v{}.{}.{}".format(*released[-1]),
        "version": f"v{major}.{minor + 1}.0",
        "adr": f"ADR-{adrs[-1] + 1:03d}",
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


def facts(checkout: Path, stage: str) -> dict:
    decision = yaml.safe_load((PACK / DECISION).read_text(encoding="utf-8"))
    rulings = {d["id"]: d for d in decision["decisions"]}
    if rulings["G1-gt001-disposition"]["decision"] != "APPROVED":
        raise Refused("L9-GT-001 has no approved owner disposition")
    if stage == "dependent" and (
        rulings["G4-gt-sv-contract"]["decision"] != "APPROVED_FOR_SEPARATE_ADMISSION"
    ):
        raise Refused("the GT+SV contract has no separate owner approval")
    projection = overlay("projection_profile_additions.yaml")["projection_profiles"][0]
    return {
        "semantics": sorted(p.name for p in (checkout / "semantics").glob("*.yaml")),
        "invariant": overlay("invariants_additions.yaml")["invariants"][0],
        "core_contract": overlay("contracts_gt_core.yaml")["contracts"][0],
        "dependent_contract": overlay("contracts_sv_dependent.yaml")["contracts"][0],
        "terms": list(overlay("vocabulary_additions.yaml")["terms"]),
        "projection": projection,
        "composition": overlay("composition_profile_additions.yaml")["profiles"][0],
        "forbidden": projection["forbidden"][0],
        "decision": decision,
        "rulings": rulings,
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


def flat(text: str) -> str:
    return " ".join(str(text).split())


def adr_body(sel: dict, f: dict, args, spec: dict) -> str:
    inv, core = f["invariant"], f["core_contract"]
    if args.stage == "core":
        decision = f"""1. **G1 — `{inv["id"]}` (KEEP).** {flat(f["rulings"]["G1-gt001-disposition"]["irreducibility"])}

   > {flat(inv["statement"])}

2. **G2 — GT-only subject.** `{core["id"]}` over exactly {", ".join(f"`{i}`" for i in core["source_invariants"])}; {len(f["terms"])} vocabulary terms; `{f["projection"]["id"]}` over {", ".join(f"`{s}`" for s in f["projection"]["sources"])}; `{f["composition"]["id"]}`; and the forbidden criterion `{f["forbidden"]}`. It excludes every SV-owned term, invariant and contract from the GT projection. The GT core stays valid without Strategic Value; it cites no SV invariant.
3. **G3 — payload schemas.** {flat(f["rulings"]["G3-schema-disposition"]["ruling"])}
4. **Not in this release.** `{f["dependent_contract"]["id"]}` is admitted separately, after this release (G4)."""
        context = (
            "Strategic planning needs admitted semantics for conditional strategic "
            "interaction: how other actors respond to a focal action, under their "
            "information, incentives and versioned assumptions. Without them a planner "
            "silently treats the world as passive. The candidate (Quantum-L9/.github#213, "
            "remediated in #216) was aligned with Strategic Value, which v3.32.0 "
            "(ADR-029) admitted on its own first."
        )
    else:
        dep = f["dependent_contract"]
        decision = f"""1. **G4 — `{dep["id"]}`.** {flat(f["rulings"]["G4-gt-sv-contract"]["ruling"])}
2. The contract cites {", ".join(f"`{i}`" for i in dep["source_invariants"])}. It redefines neither foundation: a GT-conditioned Strategic Value assessment is one canonical SV assessment evaluated over GT-conditioned futures, never a standalone value plus a GT uplift."""
        context = (
            "With Strategic Value (v3.32.0, ADR-029) and the Game Theory core "
            "admitted, a planner needs the contract that joins them without "
            "double counting or redefining either foundation."
        )
    return f"""# {sel["adr"]} — {spec["title"]}

**Status:** Candidate for semantic-foundation {sel["version"]}.

## Context

{context}

## Decision

{decision}

## Consequences

- Consumers bind only through their own release process after admission and trusted replay.
- No projection, composition or receipt is evidence of a numerical valuation or of an executed game solver.
- Neither foundation grants plan admission, strategic commitment, execution, publication or deployment authority.

## Evidence relied on

Owner decisions: `docs/candidates/GT/{DECISION}`. Producer: `Quantum-L9/l9-semantic-compiler-engine@{args.compiler_revision}`. See `docs/semantic-foundation/{sel["version"]}/RELEASE_VALIDATION.md`.
"""


def write_adr(checkout: Path, sel: dict, f: dict, args, spec: dict) -> None:
    path = checkout / "docs" / "adr" / f"{sel['adr']}-{spec['slug']}.md"
    if path.exists():
        raise Refused(f"{path.name} exists")
    path.write_text(adr_body(sel, f, args, spec), encoding="utf-8")


def update_adr_index(checkout: Path, sel: dict, spec: dict) -> None:
    path = checkout / "docs" / "adr" / ADR_INDEX
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    last = max(i for i, ln in enumerate(lines) if re.match(r"^- ADR-\d{3}: ", ln))
    lines.insert(last + 1, f"- {sel['adr']}: {spec['title']}\n")
    text = "".join(lines)
    sentence = re.compile(
        r"^ADR-001 through ADR-\d{3}[^\n]*? are the global semantic decisions\.",
        re.MULTILINE,
    )
    if len(sentence.findall(text)) != 1:
        raise Refused("ADR index count sentence not found exactly once")
    text = sentence.sub(
        f"{adr_ranges(adr_numbers(checkout))} are the global semantic decisions.", text
    )
    path.write_text(text, encoding="utf-8")


def changes(f: dict, stage: str) -> str:
    inv, core = f["invariant"], f["core_contract"]
    if stage == "dependent":
        return (
            f"- `semantics/contracts.yaml`: `{f['dependent_contract']['id']}`.\n"
            "- Derived ledgers whose recorded `contracts.yaml` digest moved: "
            "derivation sha256 and item counts only.\n"
        )
    return (
        f"- `semantics/invariants.yaml`: `{inv['id']}`.\n"
        f"- `semantics/contracts.yaml`: `{core['id']}`; derivation digest and count rebound.\n"
        f"- `semantics/vocabulary.yaml`: {len(f['terms'])} terms "
        f"({', '.join(f'`{t}`' for t in f['terms'])}).\n"
        f"- `semantics/projection_profiles.yaml`: `{f['projection']['id']}` and the "
        f"forbidden criterion `{f['forbidden']}`.\n"
        f"- `semantics/composition_profiles.yaml`: `{f['composition']['id']}`.\n"
        f"- {', '.join(f'`{p}`' for p in GT_SCHEMAS)}, registered in "
        "`generic_compiler_manifest.yaml#requires.artifact_schemas`.\n"
        "- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, "
        "`semantics/receipt_catalog.yaml`: derivation sha256 and item counts only.\n"
    )


def write_release(checkout: Path, sel: dict, f: dict, args, spec, validator) -> None:
    root = checkout / RELEASES / sel["version"]
    root.mkdir(parents=False, exist_ok=validator is not None)
    n_sem, n_adr = len(f["semantics"]), len(adr_numbers(checkout))
    surface = "".join(f"- `semantics/{name}`\n" for name in f["semantics"])
    added = spec["added"]
    added_text = (
        f"{len(added)} files are added: {', '.join(f'`{p}`' for p in added)}"
        if added
        else "No file is added"
    )
    (root / "MANIFEST.md").write_text(
        f"""# Semantic Foundation Manifest {sel["version"]}

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **{n_sem}** canonical semantic YAML files:
{surface}
The {sel["predecessor"]} inventory is preserved. {added_text}. No ledger is removed or renamed.

## Architecture decision records

The release contains **{n_adr}** accepted ADRs plus the ADR index under `docs/adr/`.

{sel["version"]} adds {sel["adr"]} ({spec["title"]}), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

{changes(f, args.stage)}- `docs/adr/README.md`: indexes {sel["adr"]}.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/{sel["predecessor"]}/`, preserved unchanged.
""",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        f"""# Semantic Foundation {sel["version"]}

Status: **ADDITIVE SUCCESSOR CANDIDATE**

{sel["version"]} carries {sel["adr"]}: {spec["title"]}.

## Bounded delta

Successor to {sel["predecessor"]}. The release number and ADR identity were selected from the merged state at {args.base}.

{changes(f, args.stage)}
## Evidence

Owner decisions: `docs/candidates/GT/{DECISION}`. Producer: `Quantum-L9/l9-semantic-compiler-engine@{args.compiler_revision}`.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants plan admission, strategic commitment, execution, publication, merge, admission or deployment authority. This candidate does not admit itself.
""",
        encoding="utf-8",
    )
    passes = validator["pass_lines"] if validator else "PENDING"
    (root / "RELEASE_VALIDATION.md").write_text(
        f"""# Release Validation {sel["version"]}

Candidate status: **additive successor candidate**.

## Closure

- **SC-001** parses {n_sem} canonical sources as YAML mappings.
- **SC-004** and **RC-001**, **RC-002**, **RC-011** bind the contracts derivation and the derived ledgers to the rebound digests.
- **SC-008** proves this release record: **{n_sem}** canonical sources, **{n_adr}** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with {passes} PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

{sel["version"]} is a candidate and does not admit itself.
""",
        encoding="utf-8",
    )


def write_hashes(checkout: Path, version: str) -> None:
    root = checkout / RELEASES / version
    lines = [
        (f"./semantics/{p.name}", sha256(p))
        for p in sorted((checkout / "semantics").glob("*.yaml"))
    ]
    lines += [
        (f"./docs/adr/{p.name}", sha256(p))
        for p in sorted((checkout / "docs" / "adr").glob("ADR-*.md"))
    ]
    lines.append(
        (f"./docs/adr/{ADR_INDEX}", sha256(checkout / "docs" / "adr" / ADR_INDEX))
    )
    lines += [(f"./{name}", sha256(root / name)) for name in RELEASE_DOCS]
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


def preconditions(checkout: Path, args, spec: dict) -> None:
    if git(checkout, "status", "--porcelain", "--untracked-files=no"):
        raise Refused("checkout has tracked changes; commit the semantic change first")
    if not FULL_SHA.fullmatch(args.compiler_revision):
        raise Refused("--compiler-revision must be a full 40-hex commit")
    for rel in spec["added"] + GT_SCHEMAS:
        if not (checkout / rel).is_file():
            raise Refused(f"{rel} missing; apply the candidate before its release")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--stage", choices=tuple(STAGES), required=True)
    parser.add_argument("--compiler-revision", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    spec = STAGES[args.stage]
    try:
        checkout = args.checkout.resolve()
        preconditions(checkout, args, spec)
        args.base = git(checkout, "rev-parse", "HEAD")
        sel = select(checkout)
        if args.dry_run:
            print(json.dumps(sel, indent=2))
            return 0
        if (checkout / RELEASES / sel["version"]).exists():
            raise Refused(f"{sel['version']} already exists")
        before = snapshot(checkout)
        f = facts(checkout, args.stage)
        write_adr(checkout, sel, f, args, spec)
        update_adr_index(checkout, sel, spec)
        write_release(checkout, sel, f, args, spec, None)
        write_hashes(checkout, sel["version"])
        first = run_validator(checkout)
        write_release(checkout, sel, f, args, spec, first)
        write_hashes(checkout, sel["version"])
        final = run_validator(checkout)
        if final["exit"] != 0 or final["pass_lines"] != first["pass_lines"]:
            raise Refused(f"native validation did not settle: {final}")
        changed = sorted(k for k, v in before.items() if v != snapshot(checkout).get(k))
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
