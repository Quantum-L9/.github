#!/usr/bin/env python3
"""Two-tier datastore provider compatibility (RC-036).

Implements technology_capabilities.yaml#binding_rules.provider_compatibility_tiers
over capability_definitions (technology_capabilities.yaml) and class provider
bindings (binding_catalog.yaml), and runs the positive and negative fixtures in
ops/fixtures/datastore-capability-compatibility/. Read-only: it writes nothing.

A fixture case may name canonical inputs instead of inline ones:
  token_definitions: "@ledger"                         canonical definitions
  provider_binding: "@ledger:<binding id>"             canonical provider binding
  admission: admitted | candidate                      applied to every ledger-sourced item

Usage:
  python3 scripts/datastore_capability_compatibility.py [--root DIR]
Exit codes: 0 every fixture produced its expected result, 1 a mismatch, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

FIXTURES = "ops/fixtures/datastore-capability-compatibility"
TECHNOLOGIES = "semantics/technology_capabilities.yaml"
BINDINGS = "semantics/binding_catalog.yaml"
RESULTS = (
    "incompatible",
    "incompatible_until_resolved",
    "semantically_compatible",
    "runtime_qualified",
)
FAKE_SUBJECTS = frozenset({"in_memory", "fake", "mock"})


def binding_digest(binding: dict[str, Any]) -> str:
    canonical = json.dumps(
        binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _version_tuple(value: object) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in str(value).split("."))
    except ValueError:
        return None


def _in_range(version: object, bounds: dict[str, Any]) -> bool | None:
    """True inside, False outside, None when the version is unknown or unparsable."""
    if version in (None, "unknown"):
        return None
    got = _version_tuple(version)
    low = _version_tuple(bounds.get("min_inclusive"))
    high = _version_tuple(bounds.get("max_exclusive"))
    if got is None or low is None or high is None:
        return None
    return low <= got < high


def _receipt_qualifies(
    receipt: dict[str, Any],
    binding: dict[str, Any],
    token: str,
    probe_id: object,
    deployment: object,
    server_version: object,
    check_server_version: bool = True,
) -> bool:
    if str(receipt.get("subject_kind", "")).lower() in FAKE_SUBJECTS:
        return False  # D2-EVAL-09
    if check_server_version:
        # D2-EVAL-09: the receipt's provider_server_version is a bound coordinate.
        # It must be present, parseable, inside the binding's range and equal to
        # the deployed server version; otherwise the receipt does not qualify.
        version = receipt.get("provider_server_version")
        bounds = binding.get("server_version_range")
        if _version_tuple(version) is None or _version_tuple(server_version) is None:
            return False
        if _version_tuple(version) != _version_tuple(server_version):
            return False
        if isinstance(bounds, dict) and not _in_range(version, bounds):
            return False
    return (
        receipt.get("provider_binding_id") == binding.get("id")
        and receipt.get("provider_binding_digest_sha256") == binding_digest(binding)
        and receipt.get("token") == token
        and receipt.get("probe_id") == probe_id
        and receipt.get("deployment_profile") == deployment
    )


def evaluate_token(
    token: str,
    definitions: dict[str, Any],
    aliases: dict[str, str],
    binding: dict[str, Any],
    deployment: object,
    server_version: object,
    receipts: list[dict[str, Any]],
    check_server_version: bool = True,
) -> tuple[str, str]:
    canonical = aliases.get(token, token)
    definition = definitions.get(canonical)
    if not isinstance(definition, dict) or definition.get("admission") != "admitted":
        return "incompatible_until_resolved", "D2-EVAL-01"
    facts = binding.get("facts") if isinstance(binding.get("facts"), dict) else {}
    fact = facts.get(canonical)
    if (
        not isinstance(fact, dict)
        or fact.get("admission") != "admitted"
        or fact.get("status") not in ("provided", "not_provided")
    ):
        return "incompatible_until_resolved", "D2-EVAL-02"
    if fact.get("status") == "not_provided":
        return "incompatible", "D2-EVAL-03"
    if not fact.get("citations"):
        return "incompatible_until_resolved", "D2-EVAL-06"
    bounds = binding.get("server_version_range")
    if isinstance(bounds, dict) and not _in_range(server_version, bounds):
        return "incompatible_until_resolved", "D2-EVAL-10"
    required = fact.get("requires_deployment") or []
    if required and deployment in (None, "unknown"):
        return "incompatible_until_resolved", "D2-EVAL-04"
    if required and deployment not in required:
        return "incompatible", "D2-EVAL-05"
    probe_id = definition.get("probe_id")
    qualifying = [
        r
        for r in receipts
        if _receipt_qualifies(
            r,
            binding,
            canonical,
            probe_id,
            deployment,
            server_version,
            check_server_version,
        )
    ]
    if qualifying:
        newest = max(qualifying, key=lambda r: str(r.get("executed_at", "")))
        if newest.get("verdict") == "pass":
            return "runtime_qualified", "D2-EVAL-08"
    return "semantically_compatible", "D2-EVAL-07"


def evaluate(
    case: dict[str, Any],
    aliases: dict[str, str] | None = None,
    check_server_version: bool = True,
) -> dict[str, Any]:
    required = list(case.get("required_capabilities") or [])
    if not required:
        return {"overall": "incompatible_until_resolved", "tokens": {}}
    definitions = case.get("token_definitions") or {}
    binding = case.get("provider_binding") or {}
    aliases = aliases or {}
    receipts = [copy.deepcopy(r) for r in case.get("receipts") or []]
    digest = binding_digest(binding)
    for receipt in receipts:
        if receipt.get("provider_binding_digest_sha256") == "@binding":
            receipt["provider_binding_digest_sha256"] = digest
    tokens = {
        t: evaluate_token(
            t,
            definitions,
            aliases,
            binding,
            case.get("deployment_profile"),
            case.get("server_version"),
            receipts,
            check_server_version,
        )
        for t in required
    }
    results = [r for r, _ in tokens.values()]
    if "incompatible" in results:
        overall = "incompatible"
    elif "incompatible_until_resolved" in results:
        overall = "incompatible_until_resolved"
    elif all(r == "runtime_qualified" for r in results):
        overall = "runtime_qualified"
    else:
        overall = "semantically_compatible"
    return {
        "overall": overall,
        "tokens": {t: {"result": r, "rule": rule} for t, (r, rule) in tokens.items()},
    }


def ledger_inputs(root: Path) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    """Canonical definitions (token -> {probe_id}), aliases, provider bindings by id."""
    technologies = yaml.safe_load((root / TECHNOLOGIES).read_text(encoding="utf-8"))
    bindings = yaml.safe_load((root / BINDINGS).read_text(encoding="utf-8"))
    block = technologies.get("capability_definitions") or {}
    definitions = {
        token: {"probe_id": (entry.get("runtime_probe") or {}).get("probe_id")}
        for token, entry in (block.get("tokens") or {}).items()
        if isinstance(entry, dict)
    }
    providers = {
        b["id"]: b
        for b in bindings.get("bindings") or []
        if isinstance(b, dict) and b.get("class") == "provider"
    }
    return definitions, dict(block.get("aliases") or {}), providers


def resolve_case(
    case: dict[str, Any],
    definitions: dict[str, Any],
    providers: dict[str, Any],
) -> dict[str, Any]:
    resolved = copy.deepcopy(case)
    admission = case.get("admission", "admitted")
    if case.get("token_definitions") == "@ledger":
        resolved["token_definitions"] = {
            t: dict(d, admission=admission) for t, d in definitions.items()
        }
    ref = case.get("provider_binding")
    if isinstance(ref, str) and ref.startswith("@ledger:"):
        binding = copy.deepcopy(providers[ref.split(":", 1)[1]])
        for fact in (binding.get("facts") or {}).values():
            fact["admission"] = admission
        resolved["provider_binding"] = binding
    return resolved


def run_suite(
    root: Path, check_server_version: bool = True
) -> tuple[list[str], list[str], set[str]]:
    """Run every fixture. check_server_version=False is the RC-036-NEG code mutant."""
    definitions, aliases, providers = ledger_inputs(root)
    passes: list[str] = []
    failures: list[str] = []
    seen: set[str] = set()
    for polarity in ("positive", "negative"):
        for path in sorted((root / FIXTURES / polarity).glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            case = resolve_case(doc["case"], definitions, providers)
            got = evaluate(case, aliases, check_server_version)
            expect = doc["expect"]
            ok = got["overall"] == expect["overall"] and all(
                got["tokens"].get(t, {}).get("result") == r
                for t, r in (expect.get("tokens") or {}).items()
            )
            if polarity == "negative" and expect["overall"] == "runtime_qualified":
                ok = False  # a negative fixture never expects full qualification
            for rule in doc.get("falsifies") or []:
                seen.add(rule)
            line = f"{polarity} {path.name}: got {got['overall']}, expected {expect['overall']}"
            (passes if ok else failures).append(line)
    return passes, failures, seen


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    args = parser.parse_args(argv)
    try:
        passes, failures, _ = run_suite(args.root.resolve())
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"UNRESOLVED {exc}")
        return 2
    for line in passes:
        print(f"PASS {line}")
    for line in failures:
        print(f"FAIL {line}")
    print(f"{len(passes)} passed, {len(failures)} failed")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
