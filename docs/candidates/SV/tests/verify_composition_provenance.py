"""Independent composition-provenance verifier for l9.compose/strategic-planner-value@1.

Compiler 0.9.3 reports the Strategic Value composition as UNKNOWN for exactly one reason:
its ``required_provenance`` declarations (``source_projection_refs``,
``source_projection_digests``, ``composition_profile_ref``, ``composition_profile_digest``)
have no admitted mechanical criterion, so each is recorded ``unresolved``. This verifier
re-derives every fact those four tokens name, plus coverage and receipt binding, from the
run's artifacts and the candidate profile records. It imports nothing from the compiler: the
digest rule (sha256 over sorted-key, compact, UTF-8 JSON of the record or envelope minus its
own digest field) is restated here, so agreement with the compiler is evidence, not reuse.

This is evidence for an owner decision. It does not resolve a criterion in the compiler, does
not edit the profile, and does not change the composition result.

Usage:
  python3 tests/verify_composition_provenance.py --run-dir DIR [--revision SHA] [--out FILE]
  python3 tests/verify_composition_provenance.py --archive TAR [--revision SHA] [--out FILE]

Exit codes: 0 PASS, 1 FAIL, 2 the inputs could not be read (never reported as PASS).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import yaml

PACK = Path(__file__).resolve().parents[1]
COMPOSITION_PROFILE_REF = "l9.compose/strategic-planner-value@1"
PROJECTION_PROFILE_REF = "l9.projection/strategic-planner-value@1"
REQUIRED_SOURCE_CLASSES = (
    "authority_model",
    "contracts",
    "invariants",
    "strategic_value_model",
    "vocabulary",
)
REQUIRED_PROVENANCE_TOKENS = (
    "source_projection_refs",
    "source_projection_digests",
    "composition_profile_ref",
    "composition_profile_digest",
)
# Which independent checks discharge each declared token, and the compiler's always-on
# criterion that already enforces the same fact on every composition.
TOKEN_EQUIVALENCE = {
    "source_projection_refs": {
        "verifier_checks": ["component_refs", "coverage", "receipt_binding"],
        "compiler_always_on": ["component_provenance", "composition_equivalence"],
    },
    "source_projection_digests": {
        "verifier_checks": ["component_digests", "receipt_binding"],
        "compiler_always_on": ["component_provenance", "composition_equivalence"],
    },
    "composition_profile_ref": {
        "verifier_checks": ["composition_profile_ref", "receipt_binding"],
        "compiler_always_on": ["composition_profile_currentness", "envelope_schema"],
    },
    "composition_profile_digest": {
        "verifier_checks": ["composition_profile_digest", "receipt_binding"],
        "compiler_always_on": ["composition_profile_currentness"],
    },
}


class InputError(Exception):
    """Required input missing, unreadable or malformed: the result is unresolved, not PASS."""


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def envelope_digest(artifact: dict[str, Any], field: str) -> str:
    return digest({k: v for k, v in artifact.items() if k != field})


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"unreadable JSON {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{path.name} is not a JSON object")
    return value


def _profile_record(overlay: str, key: str, ref: str) -> dict[str, Any]:
    path = PACK / "overlays" / overlay
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise InputError(f"unreadable profile overlay {overlay}: {exc}") from exc
    matches = [p for p in (doc or {}).get(key) or [] if isinstance(p, dict) and p.get("id") == ref]
    if len(matches) != 1:
        raise InputError(f"{overlay} must define {ref} exactly once (found {len(matches)})")
    return matches[0]


def candidate_profiles() -> tuple[dict[str, Any], dict[str, Any]]:
    composition = _profile_record(
        "composition_profile_additions.yaml", "profiles", COMPOSITION_PROFILE_REF
    )
    projection = _profile_record(
        "projection_profile_additions.yaml", "projection_profiles", PROJECTION_PROFILE_REF
    )
    return composition, projection


def load_run(run_dir: Path) -> dict[str, Any]:
    composed = sorted((run_dir / "composed").glob("*.composed.json"))
    if len(composed) != 1:
        raise InputError(f"expected exactly one composed artifact, found {len(composed)}")
    projections = sorted(run_dir.glob("*/*.projection.json"))
    if not projections:
        raise InputError("no component projection artifacts found")
    receipts = sorted((run_dir / "receipts").glob("*.json"))
    if not receipts:
        raise InputError("no receipts found")
    return {
        "composed": _load_json(composed[0]),
        "projections": [_load_json(p) for p in projections],
        "receipts": [(p.stem, _load_json(p)) for p in receipts],
    }


def _check(ok: bool, **evidence: Any) -> dict[str, Any]:
    return {"status": "pass" if ok else "fail", **evidence}


def verify(run: dict[str, Any], revision: str | None = None) -> dict[str, Any]:
    composition_profile, projection_profile = candidate_profiles()
    composed = run["composed"]
    checks: dict[str, dict[str, Any]] = {}

    profile = composed.get("composition_profile") or {}
    checks["composition_profile_ref"] = _check(
        profile.get("ref") == COMPOSITION_PROFILE_REF,
        observed=profile.get("ref"),
        expected=COMPOSITION_PROFILE_REF,
    )
    expected_profile_digest = digest(composition_profile)
    checks["composition_profile_digest"] = _check(
        profile.get("digest") == expected_profile_digest,
        observed=profile.get("digest"),
        expected=expected_profile_digest,
    )

    # Every projection artifact must itself be intact before its digest can vouch for it.
    artifacts: dict[str, dict[str, Any]] = {}
    artifact_errors: list[str] = []
    projection_profile_digest = digest(projection_profile)
    for art in run["projections"]:
        ref = f"{art.get('projection_profile_ref')}#{art.get('source_ref')}"
        if envelope_digest(art, "projection_digest") != art.get("projection_digest"):
            artifact_errors.append(f"{ref}: projection_digest does not recompute")
        if art.get("projection_profile_ref") != PROJECTION_PROFILE_REF:
            artifact_errors.append(f"{ref}: wrong projection profile")
        if art.get("projection_profile_digest") != projection_profile_digest:
            artifact_errors.append(f"{ref}: projection_profile_digest mismatch")
        if ref in artifacts:
            artifact_errors.append(f"{ref}: duplicate projection artifact")
        artifacts[ref] = art

    components = composed.get("components")
    if not isinstance(components, list):
        components = []
    refs = [c.get("projection_ref") for c in components if isinstance(c, dict)]
    ref_errors = [r for r in refs if r not in artifacts]
    for c in components:
        art = artifacts.get(c.get("projection_ref"))
        if art and (
            c.get("source_ref") != art.get("source_ref")
            or c.get("projection_ref")
            != f"{PROJECTION_PROFILE_REF}#{art.get('source_ref')}"
        ):
            ref_errors.append(f"{c.get('projection_ref')}: source identity disagrees")
    checks["component_refs"] = _check(
        bool(refs) and not ref_errors and not artifact_errors,
        unmatched_or_inconsistent=ref_errors,
        artifact_errors=artifact_errors,
    )

    digest_errors = []
    for c in components:
        art = artifacts.get(c.get("projection_ref"))
        if art is None:
            digest_errors.append(f"{c.get('projection_ref')}: no artifact")
            continue
        if c.get("projection_digest") != envelope_digest(art, "projection_digest"):
            digest_errors.append(f"{c.get('projection_ref')}: projection_digest mismatch")
        if c.get("source_digest") != art.get("source_digest"):
            digest_errors.append(f"{c.get('projection_ref')}: source_digest mismatch")
    checks["component_digests"] = _check(bool(components) and not digest_errors, errors=digest_errors)

    checks["composition_digest"] = _check(
        envelope_digest(composed, "composition_digest") == composed.get("composition_digest"),
        observed=composed.get("composition_digest"),
    )

    classes = [c.get("source_class") for c in components if isinstance(c, dict)]
    payload = composed.get("payload") if isinstance(composed.get("payload"), dict) else {}
    placement_errors = []
    for c in components:
        art = artifacts.get(c.get("projection_ref"))
        if art is None or payload.get(c.get("source_class")) != art.get("payload"):
            placement_errors.append(f"{c.get('source_class')}: payload is not the whole component payload")
    checks["coverage"] = _check(
        sorted(classes) == list(REQUIRED_SOURCE_CLASSES)
        and len(set(refs)) == len(refs) == len(REQUIRED_SOURCE_CLASSES)
        and sorted(payload) == list(REQUIRED_SOURCE_CLASSES)
        and not placement_errors,
        source_classes=sorted(c for c in classes if isinstance(c, str)),
        required=list(REQUIRED_SOURCE_CLASSES),
        placement_errors=placement_errors,
    )

    checks["receipt_binding"] = _receipt_binding(run, composed, artifacts, revision)

    failed = sorted(k for k, v in checks.items() if v["status"] != "pass")
    tokens = {
        token: {
            **mapping,
            "status": "pass"
            if all(checks[c]["status"] == "pass" for c in mapping["verifier_checks"])
            else "fail",
        }
        for token, mapping in TOKEN_EQUIVALENCE.items()
    }
    return {
        "schema": "l9.sv-composition-provenance-equivalence/v1",
        "subject": COMPOSITION_PROFILE_REF,
        "result": "PASS" if not failed else "FAIL",
        "failed_checks": failed,
        "checks": checks,
        "required_provenance_tokens": tokens,
        "compiler_reported_result": checks["receipt_binding"].get("compiler_result"),
        "compiler_unresolved_criteria": checks["receipt_binding"].get("compiler_unresolved"),
    }


def _receipt_binding(run, composed, artifacts, revision) -> dict[str, Any]:
    errors: list[str] = []
    by_op: dict[str, list[dict[str, Any]]] = {}
    for stem, receipt in run["receipts"]:
        if envelope_digest(receipt, "receipt_digest") != receipt.get("receipt_digest"):
            errors.append(f"receipt {stem[:12]}: receipt_digest does not recompute")
        if str(receipt.get("receipt_identity", "")).rsplit("/", 1)[-1] != stem:
            errors.append(f"receipt {stem[:12]}: identity does not match file name")
        by_op.setdefault(str(receipt.get("operation")), []).append(receipt)
    compositions = by_op.get("composition", [])
    if len(compositions) != 1:
        errors.append(f"expected one composition receipt, found {len(compositions)}")
        return _check(False, errors=errors)
    rc = compositions[0]
    coords = rc.get("governing_coordinates") or {}
    revisions = {(r.get("governing_coordinates") or {}).get("revision") for _, r in run["receipts"]}
    if len(revisions) != 1:
        errors.append(f"receipts bind {len(revisions)} authority revisions")
    if revision is not None and coords.get("revision") != revision:
        errors.append(f"authority revision {coords.get('revision')} != expected {revision}")
    if rc.get("profile") != composed.get("composition_profile"):
        errors.append("composition receipt profile differs from composed artifact")
    if (rc.get("output") or {}).get("digest") != composed.get("composition_digest"):
        errors.append("composition receipt output digest differs from composed artifact")
    expected_inputs = sorted(
        (c.get("projection_ref"), c.get("projection_digest")) for c in composed.get("components") or []
    )
    observed_inputs = sorted((i.get("ref"), i.get("digest")) for i in rc.get("inputs") or [])
    if observed_inputs != expected_inputs:
        errors.append("composition receipt inputs differ from composed components")
    projection_outputs = {}
    for r in by_op.get("projection", []):
        out = r.get("output") or {}
        projection_outputs[out.get("ref")] = (out.get("digest"), r.get("result"))
    for ref, art in artifacts.items():
        got = projection_outputs.get(ref)
        if got != (art.get("projection_digest"), "pass"):
            errors.append(f"{ref}: no PASS projection receipt for this exact artifact")
    basis = rc.get("verification_basis") or {}
    return _check(
        not errors,
        errors=errors,
        authority_revision=coords.get("revision"),
        authority_repository=coords.get("repository"),
        projection_receipts_pass=sum(1 for d, res in projection_outputs.values() if res == "pass"),
        compiler_result=rc.get("result"),
        compiler_unresolved=sorted(basis.get("unresolved_criteria") or []),
    )


def _run_from_archive(archive: Path, workdir: Path) -> Path:
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not (member.isfile() or member.isdir()) or member.name.startswith("/") or ".." in Path(member.name).parts:
                raise InputError(f"refusing archive member {member.name}")
        tar.extractall(workdir, filter="data")
    return workdir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-dir", type=Path)
    src.add_argument("--archive", type=Path)
    parser.add_argument("--revision", help="expected authority revision bound by every receipt")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = args.run_dir or _run_from_archive(args.archive, Path(tmp))
            report = verify(load_run(run_dir), args.revision)
    except InputError as exc:
        print(json.dumps({"result": "UNRESOLVED", "reason": str(exc)}))
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
