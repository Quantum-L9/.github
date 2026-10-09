#!/usr/bin/env python3
"""Semantic Foundation closure validator. Read-only, deterministic, offline.

Checks the structural closure of the canonical semantic ledgers under
``semantics/`` and the current release record under
``docs/semantic-foundation/<version>/``. It never modifies a file, never
decides whether semantic law is correct, and never admits a capability or a
technology. Every unresolved reference fails closed with file, field, and
offending value.

Usage: scripts/validate-semantics.py [--root DIR] [--release vX.Y.Z]
Exit status: 0 when every check passes, 1 on any failure, 2 when the
validator itself cannot run (missing dependency, unreadable tree).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # fail closed: a missing parser is not a pass
    print(
        "FAIL SC-000 validator: PyYAML is not installed; install python3-yaml (pip install pyyaml)"
    )
    sys.exit(2)


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes: list[str] = []

    def fail(
        self, check: str, path: str, field: str, value: object, message: str
    ) -> None:
        self.failures.append(f"FAIL {check} {path} {field}={value!r}: {message}")

    def ok(self, check: str, message: str) -> None:
        self.passes.append(f"PASS {check} {message}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path, report: Report, check: str) -> dict | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        report.fail(check, str(path), "yaml", "-", f"parse failed: {exc}")
        return None
    if not isinstance(data, dict):
        report.fail(
            check,
            str(path),
            "document",
            type(data).__name__,
            "top-level document is not a mapping",
        )
        return None
    return data


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def check_sc001(root: Path, report: Report) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    files = sorted((root / "semantics").glob("*.yaml"))
    if not files:
        report.fail(
            "SC-001", "semantics/", "files", 0, "no canonical semantic sources found"
        )
        return docs
    before = len(report.failures)
    for path in files:
        data = load_yaml(path, report, "SC-001")
        if data is not None:
            docs[rel(root, path)] = data
    if len(report.failures) == before:
        report.ok(
            "SC-001", f"{len(files)} canonical semantic sources parse as YAML mappings"
        )
    return docs


def check_sc002(root: Path, docs: dict[str, dict], report: Report) -> None:
    registry_path = "semantics/canonical_sources.yaml"
    registry = docs.get(registry_path)
    if registry is None:
        report.fail(
            "SC-002",
            registry_path,
            "file",
            "-",
            "canonical source registry missing or unparsable",
        )
        return
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        report.fail(
            "SC-002",
            registry_path,
            "sources",
            type(sources).__name__,
            "registry has no source list",
        )
        return
    before = len(report.failures)
    seen_ids: dict[str, int] = {}
    seen_paths: dict[str, int] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}]",
                source,
                "source entry is not a mapping",
            )
            continue
        source_id = source.get("id")
        source_path = source.get("path")
        if not source_id:
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}].id",
                source_id,
                "missing canonical source id",
            )
        elif source_id in seen_ids:
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}].id",
                source_id,
                f"duplicate canonical source id (first at sources[{seen_ids[source_id]}])",
            )
        else:
            seen_ids[source_id] = index
        if not source_path:
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}].path",
                source_path,
                "missing registered path",
            )
            continue
        if source_path in seen_paths:
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}].path",
                source_path,
                f"duplicate registered path (first at sources[{seen_paths[source_path]}])",
            )
        else:
            seen_paths[source_path] = index
        if not (root / source_path).is_file():
            report.fail(
                "SC-002",
                registry_path,
                f"sources[{index}].path",
                source_path,
                "registered path does not exist",
            )
            continue
        target = docs.get(source_path)
        if target is None or target.get("canonical") is not True:
            report.fail(
                "RC-007",
                registry_path,
                f"sources[{index}].path",
                source_path,
                "registered path is not a parsed ledger declaring canonical: true",
            )
    if len(report.failures) == before:
        report.ok(
            "SC-002",
            f"{len(sources)} registered canonical sources resolve to existing files with unique ids and paths",
        )
        report.ok(
            "RC-007",
            "every registered path resolves to a canonical ledger (RC-008 uniqueness is SC-002)",
        )


def check_sc003(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    seen: dict[str, str] = {}
    for path, data in sorted(docs.items()):
        artifact_id = data.get("artifact_id")
        if not artifact_id:
            report.fail(
                "SC-003",
                path,
                "artifact_id",
                artifact_id,
                "canonical ledger declares no artifact_id",
            )
            continue
        if artifact_id in seen:
            report.fail(
                "SC-003",
                path,
                "artifact_id",
                artifact_id,
                f"duplicate artifact_id (also in {seen[artifact_id]})",
            )
        else:
            seen[artifact_id] = path
    if len(report.failures) == before:
        report.ok("SC-003", f"{len(seen)} artifact_id values are present and unique")


def check_sc004(root: Path, docs: dict[str, dict], report: Report) -> None:
    contracts_path = "semantics/contracts.yaml"
    contracts = docs.get(contracts_path)
    if contracts is None:
        report.fail(
            "SC-004",
            contracts_path,
            "file",
            "-",
            "contract catalog missing or unparsable",
        )
        return
    derivation = contracts.get("derivation")
    if not isinstance(derivation, dict):
        report.fail(
            "SC-004",
            contracts_path,
            "derivation",
            derivation,
            "derivation block missing",
        )
        return
    before = len(report.failures)
    source_artifact = derivation.get("source_artifact")
    source_path = f"semantics/{source_artifact}" if source_artifact else None
    source_doc = docs.get(source_path) if source_path else None
    if source_doc is None:
        report.fail(
            "SC-004",
            contracts_path,
            "derivation.source_artifact",
            source_artifact,
            "derivation source is not a parsed canonical semantic source",
        )
        return
    recorded_id = derivation.get("source_artifact_id")
    actual_id = source_doc.get("artifact_id")
    if recorded_id != actual_id:
        report.fail(
            "SC-004",
            contracts_path,
            "derivation.source_artifact_id",
            recorded_id,
            f"source artifact declares artifact_id {actual_id!r}",
        )
    recorded_digest = derivation.get("source_digest_sha256")
    actual_digest = sha256_file(root / source_path)
    if recorded_digest != actual_digest:
        report.fail(
            "SC-004",
            contracts_path,
            "derivation.source_digest_sha256",
            recorded_digest,
            f"sha256 of {source_path} is {actual_digest}",
        )
    invariants = source_doc.get("invariants")
    actual_count = len(invariants) if isinstance(invariants, list) else None
    recorded_count = derivation.get("source_invariant_count")
    if actual_count is None:
        report.fail(
            "SC-004",
            source_path,
            "invariants",
            type(invariants).__name__,
            "invariant corpus is not a list",
        )
    elif recorded_count != actual_count:
        report.fail(
            "SC-004",
            contracts_path,
            "derivation.source_invariant_count",
            recorded_count,
            f"{source_path} contains {actual_count} invariant records",
        )
    if len(report.failures) == before:
        report.ok(
            "SC-004",
            f"contracts.yaml derivation matches {source_path} "
            f"(artifact_id={actual_id}, sha256={actual_digest[:12]}…, invariants={actual_count})",
        )


def check_sc005(docs: dict[str, dict], report: Report) -> None:
    capabilities_path = "semantics/capabilities.yaml"
    patterns_path = "semantics/architecture_patterns.yaml"
    capabilities = docs.get(capabilities_path)
    patterns = docs.get(patterns_path)
    if capabilities is None or patterns is None:
        report.fail(
            "SC-005",
            capabilities_path if capabilities is None else patterns_path,
            "file",
            "-",
            "required ledger missing or unparsable",
        )
        return
    before = len(report.failures)
    entries = capabilities.get("capabilities")
    if not isinstance(entries, list):
        report.fail(
            "SC-005",
            capabilities_path,
            "capabilities",
            type(entries).__name__,
            "catalog is not a list",
        )
        return
    required_fields = (capabilities.get("capability_entry_contract") or {}).get(
        "required_fields"
    ) or []
    catalog_ids: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            report.fail(
                "SC-005",
                capabilities_path,
                f"capabilities[{index}]",
                entry,
                "catalog entry is not a mapping",
            )
            continue
        for field in required_fields:
            if field not in entry:
                report.fail(
                    "SC-005",
                    capabilities_path,
                    f"capabilities[{index}].{field}",
                    None,
                    "required capability field missing",
                )
        entry_id = entry.get("id")
        if entry_id in catalog_ids:
            report.fail(
                "SC-005",
                capabilities_path,
                f"capabilities[{index}].id",
                entry_id,
                "duplicate capability id",
            )
        elif entry_id:
            catalog_ids.add(entry_id)
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        requires = entry.get("requires") or {}
        for ref in (
            (requires.get("capabilities") or []) if isinstance(requires, dict) else []
        ):
            if ref not in catalog_ids:
                report.fail(
                    "SC-005",
                    capabilities_path,
                    f"capabilities[{index}].requires.capabilities",
                    ref,
                    "required capability does not resolve through the canonical capability catalog",
                )
    recorded_count = (capabilities.get("catalog_status") or {}).get(
        "admitted_capability_count"
    )
    if recorded_count != len(entries):
        report.fail(
            "SC-005",
            capabilities_path,
            "catalog_status.admitted_capability_count",
            recorded_count,
            f"catalog holds {len(entries)} admitted capability entries",
        )
    # Only fields the foundation types as canonical capability references are
    # resolved through capabilities.yaml (``capability_refs``, the ProductTopology
    # field name). Pattern-level ``architecture_obligations`` are architectural
    # traits, not capability identities, and are never resolved here (RC-012
    # checks their shape).
    pattern_list = patterns.get("patterns")
    if not isinstance(pattern_list, list):
        report.fail(
            "SC-005",
            patterns_path,
            "patterns",
            type(pattern_list).__name__,
            "pattern list missing",
        )
    else:
        for index, pattern in enumerate(pattern_list):
            if not isinstance(pattern, dict):
                continue
            for ref in pattern.get("capability_refs") or []:
                if ref not in catalog_ids:
                    report.fail(
                        "SC-005",
                        patterns_path,
                        f"patterns[{index}].capability_refs",
                        ref,
                        "canonical capability reference does not resolve through capabilities.yaml",
                    )
    if len(report.failures) == before:
        report.ok(
            "SC-005",
            f"capability model closed: {len(catalog_ids)} admitted capabilities, "
            "typed capability references resolve, traits are not resolved as capabilities",
        )


def check_sc006(docs: dict[str, dict], report: Report) -> None:
    bindings_path = "semantics/binding_catalog.yaml"
    technologies_path = "semantics/technology_capabilities.yaml"
    bindings = docs.get(bindings_path)
    technologies = docs.get(technologies_path)
    if bindings is None or technologies is None:
        report.fail(
            "SC-006",
            bindings_path if bindings is None else technologies_path,
            "file",
            "-",
            "required ledger missing or unparsable",
        )
        return
    before = len(report.failures)
    registered = {
        t.get("id")
        for t in technologies.get("technologies") or []
        if isinstance(t, dict)
    }
    binding_list = bindings.get("bindings")
    if not isinstance(binding_list, list):
        report.fail(
            "SC-006",
            bindings_path,
            "bindings",
            type(binding_list).__name__,
            "binding list missing",
        )
        return
    resolved = 0
    for index, binding in enumerate(binding_list):
        if not isinstance(binding, dict):
            continue
        for family in ("target", "provider"):
            block = binding.get(family)
            if isinstance(block, dict) and "technology" in block:
                technology = block.get("technology")
                if technology in registered:
                    resolved += 1
                else:
                    report.fail(
                        "SC-006",
                        bindings_path,
                        f"bindings[{index}].{family}.technology",
                        technology,
                        "technology is not registered in technology_capabilities.yaml",
                    )
    if len(report.failures) == before:
        report.ok(
            "SC-006",
            f"{resolved} binding technology targets resolve to registered technologies",
        )


def check_sc007(docs: dict[str, dict], report: Report) -> None:
    bindings_path = "semantics/binding_catalog.yaml"
    bindings = docs.get(bindings_path)
    if bindings is None:
        report.fail(
            "SC-007",
            bindings_path,
            "file",
            "-",
            "binding catalog missing or unparsable",
        )
        return
    before = len(report.failures)
    seen: set[str] = set()
    for index, binding in enumerate(bindings.get("bindings") or []):
        if not isinstance(binding, dict):
            report.fail(
                "SC-007",
                bindings_path,
                f"bindings[{index}]",
                binding,
                "binding entry is not a mapping",
            )
            continue
        binding_id = binding.get("id")
        if not binding_id or not isinstance(binding_id, str):
            report.fail(
                "SC-007",
                bindings_path,
                f"bindings[{index}].id",
                binding_id,
                "binding identifier missing",
            )
        elif binding_id in seen:
            report.fail(
                "SC-007",
                bindings_path,
                f"bindings[{index}].id",
                binding_id,
                "duplicate binding identifier",
            )
        else:
            seen.add(binding_id)
    if len(report.failures) == before:
        report.ok(
            "SC-007",
            f"{len(seen)} binding identifiers present and unique; no registered ledger declares a "
            "canonical binding-ID grammar, so grammar conformance is not enforced",
        )


def check_sc008(root: Path, release: str | None, report: Report) -> None:
    base = root / "docs" / "semantic-foundation"
    if release is None:
        # Numeric version order: v3.10.0 must outrank v3.5.0.
        versions = (
            sorted(
                (p.name for p in base.iterdir() if p.is_dir()),
                key=lambda name: ([int(n) for n in re.findall(r"\d+", name)], name),
            )
            if base.is_dir()
            else []
        )
        if not versions:
            report.fail(
                "SC-008",
                str(base.relative_to(root)),
                "release",
                None,
                "no release record directory found",
            )
            return
        release = versions[-1]
    release_dir = base / release
    manifest = release_dir / "MANIFEST.md"
    hashes = release_dir / "HASHES.sha256"
    if not manifest.is_file() or not hashes.is_file():
        report.fail(
            "SC-008",
            rel(root, release_dir),
            "files",
            "MANIFEST.md,HASHES.sha256",
            "release record incomplete",
        )
        return
    before = len(report.failures)
    semantics_files = sorted(
        f"semantics/{p.name}" for p in (root / "semantics").glob("*.yaml")
    )
    manifest_text = manifest.read_text(encoding="utf-8")
    listed = set(re.findall(r"`(semantics/[^`]+\.yaml)`", manifest_text))
    for path in semantics_files:
        if path not in listed:
            report.fail(
                "SC-008",
                rel(root, manifest),
                "install surface",
                path,
                "canonical source is not listed in the manifest",
            )
    for path in sorted(listed):
        if path not in semantics_files:
            report.fail(
                "SC-008",
                rel(root, manifest),
                "install surface",
                path,
                "manifest lists a file that does not exist",
            )
    count_match = re.search(
        r"contains \*\*(\d+)\*\* canonical semantic YAML files", manifest_text
    )
    if count_match is None:
        report.fail(
            "SC-008",
            rel(root, manifest),
            "install surface count",
            None,
            "manifest does not state the canonical file count",
        )
    elif int(count_match.group(1)) != len(semantics_files):
        report.fail(
            "SC-008",
            rel(root, manifest),
            "install surface count",
            int(count_match.group(1)),
            f"semantics/ holds {len(semantics_files)} canonical YAML files",
        )
    recorded: dict[str, str] = {}
    for line_no, line in enumerate(
        hashes.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            report.fail(
                "SC-008",
                rel(root, hashes),
                f"line {line_no}",
                line,
                "malformed sha256 inventory line",
            )
            continue
        recorded[parts[1]] = parts[0]
    adr_files = sorted((root / "docs" / "adr").glob("ADR-*.md"))
    adr_match = re.search(r"contains \*\*(\d+)\*\* accepted ADRs", manifest_text)
    if adr_match is None:
        report.fail(
            "SC-008",
            rel(root, manifest),
            "ADR count",
            None,
            "manifest does not state the accepted ADR count",
        )
    elif int(adr_match.group(1)) != len(adr_files):
        report.fail(
            "SC-008",
            rel(root, manifest),
            "ADR count",
            int(adr_match.group(1)),
            f"docs/adr/ holds {len(adr_files)} ADR-*.md records",
        )
    # Inventory is what the manifest declares: every canonical source, every
    # accepted ADR plus the ADR index, and the release record's own documents.
    expected = {f"./{p}" for p in semantics_files}
    expected |= {f"./docs/adr/{p.name}" for p in adr_files}
    expected.add("./docs/adr/README.md")
    expected |= {f"./{p.name}" for p in release_dir.glob("*.md")}
    for entry in sorted(expected - set(recorded)):
        report.fail(
            "SC-008",
            rel(root, hashes),
            "inventory",
            entry,
            "release hash inventory omits this file",
        )
    for entry, digest in sorted(recorded.items()):
        target = (
            release_dir / entry[2:]
            if not entry.startswith(("./semantics/", "./docs/"))
            else root / entry[2:]
        )
        if not target.is_file():
            report.fail(
                "SC-008",
                rel(root, hashes),
                "inventory",
                entry,
                "hashed file does not exist",
            )
            continue
        actual = sha256_file(target)
        if actual != digest:
            report.fail(
                "SC-008",
                rel(root, hashes),
                entry,
                digest,
                f"delivered bytes hash to {actual}",
            )
    if len(report.failures) == before:
        report.ok(
            "SC-008",
            f"release {release}: manifest lists all {len(semantics_files)} canonical sources and "
            f"{len(recorded)} hashed files match delivered bytes",
        )


# The validator's own path, used as the receipt location for negative-case
# batches that prove a closure check fails closed.
VALIDATOR_PATH = "scripts/validate-semantics.py"
# Field label for a ledger's canonical owner, reported by RC-016 and RC-018.
AUTHORITY_OWNER_FIELD = "authority.owner"

DERIVATION_ITEM_KEYS = {
    "invariants.yaml": "invariants",
    "contracts.yaml": "contracts",
    "capabilities.yaml": "capabilities",
}


def check_derivation_sources(
    check: str, ledger_path: str, root: Path, docs: dict[str, dict], report: Report
) -> None:
    ledger = docs.get(ledger_path)
    if ledger is None:
        report.fail(check, ledger_path, "file", "-", "ledger missing or unparsable")
        return
    sources = (ledger.get("derivation") or {}).get("source_artifacts")
    if not isinstance(sources, list) or not sources:
        report.fail(
            check,
            ledger_path,
            "derivation.source_artifacts",
            sources,
            "derivation source list missing",
        )
        return
    before = len(report.failures)
    for index, source in enumerate(sources):
        field = f"derivation.source_artifacts[{index}]"
        if not isinstance(source, dict):
            report.fail(check, ledger_path, field, source, "entry is not a mapping")
            continue
        artifact = source.get("artifact")
        source_path = f"semantics/{artifact}" if artifact else None
        source_doc = docs.get(source_path) if source_path else None
        if source_doc is None:
            report.fail(
                check,
                ledger_path,
                f"{field}.artifact",
                artifact,
                "derivation source is not a parsed canonical semantic source",
            )
            continue
        if source.get("artifact_id") != source_doc.get("artifact_id"):
            report.fail(
                check,
                ledger_path,
                f"{field}.artifact_id",
                source.get("artifact_id"),
                f"source artifact declares artifact_id {source_doc.get('artifact_id')!r}",
            )
        actual_digest = sha256_file(root / source_path)
        if source.get("sha256") != actual_digest:
            report.fail(
                check,
                ledger_path,
                f"{field}.sha256",
                source.get("sha256"),
                f"sha256 of {source_path} is {actual_digest}",
            )
        if "item_count" in source:
            item_key = DERIVATION_ITEM_KEYS.get(artifact)
            items = source_doc.get(item_key) if item_key else None
            if not isinstance(items, list):
                report.fail(
                    check,
                    ledger_path,
                    f"{field}.item_count",
                    source.get("item_count"),
                    f"no countable record list is known for {artifact}",
                )
            elif source.get("item_count") != len(items):
                report.fail(
                    check,
                    ledger_path,
                    f"{field}.item_count",
                    source.get("item_count"),
                    f"{source_path} contains {len(items)} {item_key} records",
                )
    if len(report.failures) == before:
        report.ok(
            check,
            f"{ledger_path} derivation matches the bytes of its {len(sources)} declared sources",
        )


def check_rc004(docs: dict[str, dict], report: Report) -> None:
    profiles_path = "semantics/projection_profiles.yaml"
    catalog = docs.get(profiles_path)
    if catalog is None:
        report.fail(
            "RC-004",
            profiles_path,
            "file",
            "-",
            "projection catalog missing or unparsable",
        )
        return
    source_classes = catalog.get("source_classes")
    profiles = catalog.get("projection_profiles")
    if not isinstance(source_classes, dict) or not isinstance(profiles, list):
        report.fail(
            "RC-004",
            profiles_path,
            "source_classes/projection_profiles",
            None,
            "catalog shape missing",
        )
        return
    before = len(report.failures)
    resolved = 0
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        sources = profile.get("sources")
        names = (
            list(sources.keys())
            if isinstance(sources, dict)
            else list(sources)
            if isinstance(sources, list)
            else None
        )
        if names is None:
            report.fail(
                "RC-004",
                profiles_path,
                f"projection_profiles[{index}].sources",
                sources,
                "profile declares no source mapping or list",
            )
            continue
        for name in names:
            if name in source_classes:
                resolved += 1
            else:
                report.fail(
                    "RC-004",
                    profiles_path,
                    f"projection_profiles[{index}].sources",
                    name,
                    "projection source does not resolve to source_classes",
                )
    if len(report.failures) == before:
        report.ok(
            "RC-004",
            f"{resolved} projection source references across {len(profiles)} profiles resolve to source_classes",
        )


IDENTITY_PROFILE_ID = "l9.projection/product-identity-topology@1"
IDENTITY_TOPOLOGY_SELECTORS = (
    "$.identity",
    "$.governance",
    "$.product.id",
    "$.product.kind",
)
STAGE_CONSUMER_PREFIX = "semantic_build_stage."
OLD_PATTERN_FIELD = "required_capabilities"
OBLIGATION_FIELD = "architecture_obligations"
COMPILATION_PROFILES_PATH = "semantics/compilation_profiles.yaml"
VOCABULARY_PATH = "semantics/vocabulary.yaml"
# Stage fields the canonical compilation profile owns and the vocabulary only
# represents. Presentation and indirection fields (label, validation.*) are
# vocabulary-owned and intentionally not compared.
STAGE_PARITY_FIELDS = ("consumes", "operations", "produces")

# RC-014 identity registry closure. The two registries name identity
# coordinates only (identity_model.yaml authority sources
# actor_registry_and_identity_resolution_contract and
# surface_registry_and_runtime_evidence). Equal strings across the two
# dimensions are legal; ownership fields of another dimension and any
# runtime-resolution structure are not.
ACTOR_REGISTRY_PATH = "semantics/actor_registry.yaml"
SURFACE_REGISTRY_PATH = "semantics/surface_registry.yaml"
IDENTITY_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CROSS_DIMENSION_FIELDS = (
    "governance_profile_ref",
    "provider_ref",
    "adapter_ref",
    "credential_ref",
    "signing_key_ref",
    "grants",
    "permissions",
    "roles",
    "token",
    "tokens",
)
ACTOR_FORBIDDEN_ENTRY_FIELDS = ("surface_ref",) + CROSS_DIMENSION_FIELDS
SURFACE_FORBIDDEN_ENTRY_FIELDS = ("actor_ref",) + CROSS_DIMENSION_FIELDS
RESOLVER_LEAKAGE_KEYS = (
    "environment_variables",
    "environment_variable",
    "env_vars",
    "env",
    "environment_markers",
    "runtime_markers",
    "marker_precedence",
    "marker_interpretation",
    "host_detection",
    "detection_rules",
    "resolution_rules",
    "resolver",
    "memory_write",
    "memory_write_behavior",
    "credential_provisioning",
    "governance_profile_inference",
)


def _profile_label(index: int, profile: dict) -> str:
    return f"projection_profiles[{index}] ({profile.get('id') or 'no id'})"


def _profile_catalog(
    check: str, docs: dict[str, dict], report: Report
) -> tuple[dict, list] | None:
    profiles_path = "semantics/projection_profiles.yaml"
    catalog = docs.get(profiles_path)
    if catalog is None:
        report.fail(
            check,
            profiles_path,
            "file",
            "-",
            "projection catalog missing or unparsable",
        )
        return None
    profiles = catalog.get("projection_profiles")
    if not isinstance(profiles, list):
        report.fail(
            check,
            profiles_path,
            "projection_profiles",
            profiles,
            "profile list missing",
        )
        return None
    return catalog, profiles


def check_rc003(docs: dict[str, dict], report: Report) -> None:
    loaded = _profile_catalog("RC-003", docs, report)
    if loaded is None:
        return
    catalog, profiles = loaded
    profiles_path = "semantics/projection_profiles.yaml"
    classes = catalog.get("profile_classes")
    if not isinstance(classes, dict) or not classes:
        report.fail(
            "RC-003",
            profiles_path,
            "profile_classes",
            classes,
            "class registry missing",
        )
        return
    before = len(report.failures)
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        if profile.get("class") not in classes:
            report.fail(
                "RC-003",
                profiles_path,
                f"{_profile_label(index, profile)}.class",
                profile.get("class"),
                "profile class does not resolve to profile_classes",
            )
    if len(report.failures) == before:
        report.ok(
            "RC-003",
            f"{len(profiles)} projection profile classes resolve to the {len(classes)} declared profile_classes",
        )


def check_rc005(docs: dict[str, dict], report: Report) -> None:
    loaded = _profile_catalog("RC-005", docs, report)
    if loaded is None:
        return
    catalog, profiles = loaded
    profiles_path = "semantics/projection_profiles.yaml"
    source_classes = catalog.get("source_classes") or {}
    vocabulary = docs.get("semantics/vocabulary.yaml") or {}
    stage_ids = {
        str(stage.get("id"))
        for stage in vocabulary.get("semantic_build_stages") or []
        if isinstance(stage, dict)
    }
    before = len(report.failures)
    identity_seen = False
    stage_count = 0
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        label = _profile_label(index, profile)
        if profile.get("class") == "stage":
            stage_count += 1
            consumer = str(profile.get("consumer") or "")
            if not consumer.startswith(STAGE_CONSUMER_PREFIX):
                report.fail(
                    "RC-005",
                    profiles_path,
                    f"{label}.consumer",
                    profile.get("consumer"),
                    f"stage profile consumer must start with {STAGE_CONSUMER_PREFIX!r}",
                )
            elif consumer.removeprefix(STAGE_CONSUMER_PREFIX) not in stage_ids:
                report.fail(
                    "RC-005",
                    profiles_path,
                    f"{label}.consumer",
                    consumer,
                    "referenced stage is not declared in vocabulary.semantic_build_stages",
                )
        if profile.get("id") != IDENTITY_PROFILE_ID:
            continue
        identity_seen = True
        sources = profile.get("sources")
        if not isinstance(sources, dict):
            report.fail(
                "RC-005",
                profiles_path,
                f"{label}.sources",
                sources,
                "identity projection sources must be a source-local selector mapping",
            )
            continue
        if "selects" in profile:
            report.fail(
                "RC-005",
                profiles_path,
                f"{label}.selects",
                profile.get("selects"),
                "identity projection must not carry a profile-level selects field",
            )
        for name in ("product_topology", "identity_model"):
            block = sources.get(name)
            if name not in source_classes:
                report.fail(
                    "RC-005",
                    profiles_path,
                    f"{label}.sources.{name}",
                    name,
                    "source does not resolve to source_classes",
                )
            selectors = block.get("selectors") if isinstance(block, dict) else None
            if not isinstance(selectors, list) or not selectors:
                report.fail(
                    "RC-005",
                    profiles_path,
                    f"{label}.sources.{name}.selectors",
                    selectors,
                    "source must own a non-empty selectors list",
                )
                continue
            if name == "product_topology" and set(map(str, selectors)) != set(
                IDENTITY_TOPOLOGY_SELECTORS
            ):
                report.fail(
                    "RC-005",
                    profiles_path,
                    f"{label}.sources.product_topology.selectors",
                    selectors,
                    f"ProductTopology selection must be exactly {list(IDENTITY_TOPOLOGY_SELECTORS)}",
                )
    if not identity_seen:
        report.fail(
            "RC-005",
            profiles_path,
            "projection_profiles",
            IDENTITY_PROFILE_ID,
            "identity projection profile is missing",
        )
    if len(report.failures) == before:
        report.ok(
            "RC-005",
            f"identity projection uses source-local selectors; {stage_count} stage profiles bind "
            "to declared semantic_build_stages",
        )


def check_rc012(docs: dict[str, dict], report: Report) -> None:
    patterns_path = "semantics/architecture_patterns.yaml"
    profiles_path = "semantics/projection_profiles.yaml"
    patterns = docs.get(patterns_path)
    loaded = _profile_catalog("RC-012", docs, report)
    if patterns is None or loaded is None:
        if patterns is None:
            report.fail(
                "RC-012",
                patterns_path,
                "file",
                "-",
                "pattern catalog missing or unparsable",
            )
        return
    _catalog, profiles = loaded
    before = len(report.failures)
    obligation_count = 0
    for index, pattern in enumerate(patterns.get("patterns") or []):
        if not isinstance(pattern, dict):
            continue
        if OLD_PATTERN_FIELD in pattern:
            report.fail(
                "RC-012",
                patterns_path,
                f"patterns[{index}].{OLD_PATTERN_FIELD}",
                pattern.get("id"),
                f"architecture obligations must be declared as {OBLIGATION_FIELD}",
            )
        if OBLIGATION_FIELD in pattern:
            values = pattern.get(OBLIGATION_FIELD)
            if not isinstance(values, list) or not all(
                isinstance(v, str) and v.strip() for v in values
            ):
                report.fail(
                    "RC-012",
                    patterns_path,
                    f"patterns[{index}].{OBLIGATION_FIELD}",
                    values,
                    "architecture obligations must be a list of non-empty strings",
                )
            else:
                obligation_count += len(values)
    for name, block in (patterns.get("projection_profiles") or {}).items():
        includes = block.get("include") if isinstance(block, dict) else None
        if isinstance(includes, list) and OLD_PATTERN_FIELD in includes:
            report.fail(
                "RC-012",
                patterns_path,
                f"projection_profiles.{name}.include",
                OLD_PATTERN_FIELD,
                f"pattern projection include must name {OBLIGATION_FIELD}",
            )
    old_selector = f"$.patterns[*].{OLD_PATTERN_FIELD}"
    new_selector = f"$.patterns[*].{OBLIGATION_FIELD}"
    selecting_profiles = 0
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        sources = profile.get("sources")
        blocks = sources.values() if isinstance(sources, dict) else []
        selectors = [
            str(s)
            for block in blocks
            if isinstance(block, dict)
            for s in block.get("selectors") or []
        ]
        if old_selector in selectors:
            report.fail(
                "RC-012",
                profiles_path,
                f"{_profile_label(index, profile)}.sources.architecture_patterns.selectors",
                old_selector,
                f"selector must target {new_selector}",
            )
        if new_selector in selectors:
            selecting_profiles += 1
    if selecting_profiles == 0:
        report.fail(
            "RC-012",
            profiles_path,
            "projection_profiles",
            new_selector,
            "no projection selects architecture-pattern obligations",
        )
    if len(report.failures) == before:
        report.ok(
            "RC-012",
            f"{obligation_count} architecture obligations typed as {OBLIGATION_FIELD}; "
            f"{selecting_profiles} profiles select them; no {OLD_PATTERN_FIELD} field or selector remains",
        )


def _stage_sequence(
    check: str, path: str, field: str, stages: object, report: Report
) -> list[tuple[int, str]] | None:
    """Return [(ordinal, id)] in list order, or None after failing closed.

    Each entry must be a mapping with a non-empty string ``id`` and an integer
    ``ordinal``; ids and ordinals must be unique; ordinals must equal the list
    position (1..N) because both ledgers declare stages as ordered.
    """
    if not isinstance(stages, list) or not stages:
        report.fail(check, path, field, stages, "stage list missing or empty")
        return None
    sequence: list[tuple[int, str]] = []
    before = len(report.failures)
    for index, stage in enumerate(stages):
        label = f"{field}[{index}]"
        if not isinstance(stage, dict):
            report.fail(check, path, label, stage, "stage entry is not a mapping")
            continue
        stage_id = stage.get("id")
        ordinal = stage.get("ordinal")
        if not isinstance(stage_id, str) or not stage_id:
            report.fail(check, path, f"{label}.id", stage_id, "stage id missing")
            continue
        if not isinstance(ordinal, int) or isinstance(ordinal, bool):
            report.fail(
                check, path, f"{label}.ordinal", ordinal, "stage ordinal missing"
            )
            continue
        if ordinal != index + 1:
            report.fail(
                check,
                path,
                f"{label}.ordinal",
                ordinal,
                f"stage {stage_id!r} is listed at position {index + 1}; ordinals must follow list order",
            )
        sequence.append((ordinal, stage_id))
    ids = [stage_id for _, stage_id in sequence]
    for stage_id in sorted(set(ids)):
        if ids.count(stage_id) > 1:
            report.fail(check, path, field, stage_id, "duplicate stage id")
    ordinals = [ordinal for ordinal, _ in sequence]
    for ordinal in sorted(set(ordinals)):
        if ordinals.count(ordinal) > 1:
            report.fail(check, path, field, ordinal, "duplicate stage ordinal")
    return sequence if len(report.failures) == before else None


def check_rc013(docs: dict[str, dict], report: Report) -> None:
    """Stage-domain equality: vocabulary.semantic_build_stages must list exactly
    the stages of the canonical compilation profile, in the same order, with
    the same ordinals. The vocabulary projects the profile; it never defines a
    stage of its own."""
    ledger = docs.get(COMPILATION_PROFILES_PATH)
    if ledger is None:
        report.fail(
            "RC-013",
            COMPILATION_PROFILES_PATH,
            "file",
            "-",
            "compilation profile ledger missing or unparsable",
        )
        return
    if ledger.get("canonical") is not True:
        report.fail(
            "RC-013",
            COMPILATION_PROFILES_PATH,
            "canonical",
            ledger.get("canonical"),
            "compilation profile ledger must declare canonical: true",
        )
        return
    profiles = ledger.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != 1:
        report.fail(
            "RC-013",
            COMPILATION_PROFILES_PATH,
            "profiles",
            len(profiles) if isinstance(profiles, list) else profiles,
            "exactly one canonical compilation profile is expected; no ledger "
            "declares a selection rule for several",
        )
        return
    profile = profiles[0]
    if not isinstance(profile, dict):
        report.fail(
            "RC-013", COMPILATION_PROFILES_PATH, "profiles[0]", profile, "not a mapping"
        )
        return
    profile_id = profile.get("id") or "no id"
    canonical = _stage_sequence(
        "RC-013",
        COMPILATION_PROFILES_PATH,
        f"profiles[0] ({profile_id}).stages",
        profile.get("stages"),
        report,
    )
    vocabulary = docs.get(VOCABULARY_PATH)
    if vocabulary is None:
        report.fail(
            "RC-013", VOCABULARY_PATH, "file", "-", "vocabulary missing or unparsable"
        )
        return
    declared = _stage_sequence(
        "RC-013",
        VOCABULARY_PATH,
        "semantic_build_stages",
        vocabulary.get("semantic_build_stages"),
        report,
    )
    if canonical is None or declared is None:
        return
    before = len(report.failures)
    canonical_ids = {stage_id: ordinal for ordinal, stage_id in canonical}
    declared_ids = {stage_id: ordinal for ordinal, stage_id in declared}
    for stage_id, ordinal in canonical_ids.items():
        if stage_id not in declared_ids:
            report.fail(
                "RC-013",
                VOCABULARY_PATH,
                "semantic_build_stages",
                stage_id,
                f"stage declared at ordinal {ordinal} by {profile_id} is absent from the vocabulary",
            )
    for stage_id, ordinal in declared_ids.items():
        if stage_id not in canonical_ids:
            report.fail(
                "RC-013",
                VOCABULARY_PATH,
                f"semantic_build_stages[{ordinal - 1}].id",
                stage_id,
                f"stage is not declared by the canonical compilation profile {profile_id}",
            )
    for index, (ordinal, stage_id) in enumerate(declared):
        expected = canonical_ids.get(stage_id)
        if expected is not None and expected != ordinal:
            report.fail(
                "RC-013",
                VOCABULARY_PATH,
                f"semantic_build_stages[{index}].ordinal",
                ordinal,
                f"stage {stage_id!r} has ordinal {expected} in {profile_id}",
            )
    if len(report.failures) == before and [s for _, s in declared] != [
        s for _, s in canonical
    ]:
        report.fail(
            "RC-013",
            VOCABULARY_PATH,
            "semantic_build_stages",
            [s for _, s in declared],
            f"stage order differs from {profile_id}: {[s for _, s in canonical]}",
        )
    if len(report.failures) == before:
        _compare_stage_fields(
            profile_id,
            profile.get("stages"),
            vocabulary.get("semantic_build_stages"),
            report,
        )
    if len(report.failures) == before:
        report.ok(
            "RC-013",
            f"vocabulary.semantic_build_stages equals the {len(canonical)}-stage canonical "
            f"profile {profile_id}: ids, order, ordinals, "
            + ", ".join(STAGE_PARITY_FIELDS[:-1])
            + f", and {STAGE_PARITY_FIELDS[-1]} agree",
        )


def _compare_stage_fields(
    profile_id: str, canonical: list, declared: list, report: Report
) -> None:
    """Field-level parity: every vocabulary stage carries the canonical
    profile's exact consumes, operations, and produces lists (same values,
    same order). Called only after ids, order, and ordinals already agree."""
    canonical_by_id = {stage["id"]: stage for stage in canonical}
    for index, stage in enumerate(declared):
        stage_id = stage["id"]
        canonical_stage = canonical_by_id[stage_id]
        for field in STAGE_PARITY_FIELDS:
            expected = canonical_stage.get(field)
            if not isinstance(expected, list) or not expected:
                report.fail(
                    "RC-013",
                    COMPILATION_PROFILES_PATH,
                    f"stages ({stage_id}).{field}",
                    expected,
                    f"canonical profile {profile_id} must declare a non-empty list",
                )
                continue
            actual = stage.get(field)
            if actual != expected:
                report.fail(
                    "RC-013",
                    VOCABULARY_PATH,
                    f"semantic_build_stages[{index}] ({stage_id}).{field}",
                    actual,
                    f"canonical profile {profile_id} declares {expected!r}",
                )


def _walk_keys(node: object, trail: str, found: list[tuple[str, str]]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{trail}.{key}" if trail else str(key)
            if str(key) in RESOLVER_LEAKAGE_KEYS:
                found.append((path, str(key)))
            _walk_keys(value, path, found)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _walk_keys(item, f"{trail}[{index}]", found)


def _check_identity_registry(
    check: str,
    path: str,
    docs: dict[str, dict],
    report: Report,
    entries_key: str,
    status_vocab_key: str,
    kind_vocab_key: str | None,
    forbidden_entry_fields: tuple[str, ...],
) -> tuple[set[str], set[str]] | None:
    """IR-001/IR-003 shape, IR-002/IR-004 aliases, IR-005 dimension
    separation, IR-008 resolver leakage for one registry. Returns
    (canonical ids, alias keys) or None after failing closed."""
    ledger = docs.get(path)
    if ledger is None:
        report.fail(check, path, "file", "-", "registry missing or unparsable")
        return None
    before = len(report.failures)
    artifact_id = ledger.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        report.fail(check, path, "artifact_id", artifact_id, "artifact_id missing")
    else:
        holders = [p for p, d in docs.items() if d.get("artifact_id") == artifact_id]
        if len(holders) != 1:
            report.fail(
                check,
                path,
                "artifact_id",
                artifact_id,
                f"artifact_id is declared by {len(holders)} ledgers: {sorted(holders)}",
            )
    if ledger.get("canonical") is not True:
        report.fail(
            check, path, "canonical", ledger.get("canonical"), "must be canonical: true"
        )
    statuses = ledger.get(status_vocab_key)
    if not isinstance(statuses, dict) or not statuses:
        report.fail(
            check, path, status_vocab_key, statuses, "bounded status vocabulary missing"
        )
        statuses = {}
    kinds: dict = {}
    if kind_vocab_key is not None:
        kinds = ledger.get(kind_vocab_key)
        if not isinstance(kinds, dict) or not kinds:
            report.fail(
                check, path, kind_vocab_key, kinds, "bounded kind vocabulary missing"
            )
            kinds = {}
    entries = ledger.get(entries_key)
    if not isinstance(entries, list) or not entries:
        report.fail(check, path, entries_key, entries, "registry entries missing")
        return None
    ids: list[str] = []
    for index, entry in enumerate(entries):
        label = f"{entries_key}[{index}]"
        if not isinstance(entry, dict):
            report.fail(check, path, label, entry, "entry is not a mapping")
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not IDENTITY_ID_PATTERN.match(entry_id):
            report.fail(
                check,
                path,
                f"{label}.id",
                entry_id,
                "identity id must be non-empty normalized kebab-case",
            )
        else:
            ids.append(entry_id)
        if entry.get("status") not in statuses:
            report.fail(
                check,
                path,
                f"{label}.status",
                entry.get("status"),
                f"status must be one of {sorted(statuses)}",
            )
        if kind_vocab_key is not None and entry.get("kind") not in kinds:
            report.fail(
                check,
                path,
                f"{label}.kind",
                entry.get("kind"),
                f"kind must be one of {sorted(kinds)}",
            )
        for field in forbidden_entry_fields:
            if field in entry:
                report.fail(
                    check,
                    path,
                    f"{label}.{field}",
                    entry.get(field),
                    "cross-dimension ownership field is not allowed in an identity registry",
                )
    for entry_id in sorted(set(ids)):
        if ids.count(entry_id) > 1:
            report.fail(check, path, entries_key, entry_id, "duplicate identity id")
    canonical_ids = set(ids)
    aliases = ledger.get("aliases")
    alias_keys: list[str] = []
    if aliases is None:
        aliases = []
    if not isinstance(aliases, list):
        report.fail(check, path, "aliases", aliases, "aliases must be a list")
        aliases = []
    for index, alias in enumerate(aliases):
        label = f"aliases[{index}]"
        if not isinstance(alias, dict):
            report.fail(check, path, label, alias, "alias entry is not a mapping")
            continue
        key = alias.get("alias")
        target = alias.get("canonical")
        if not isinstance(key, str) or not IDENTITY_ID_PATTERN.match(key):
            report.fail(
                check,
                path,
                f"{label}.alias",
                key,
                "alias must be non-empty normalized kebab-case",
            )
            continue
        alias_keys.append(key)
        if key in canonical_ids:
            report.fail(
                check,
                path,
                f"{label}.alias",
                key,
                "alias shadows a canonical identity id in the same dimension",
            )
        if target not in canonical_ids:
            report.fail(
                check,
                path,
                f"{label}.canonical",
                target,
                "alias target does not resolve to a canonical identity id in this registry",
            )
    for key in sorted(set(alias_keys)):
        if alias_keys.count(key) > 1:
            report.fail(check, path, "aliases", key, "duplicate alias key")
    for index, alias in enumerate(aliases):
        if isinstance(alias, dict) and alias.get("canonical") in alias_keys:
            report.fail(
                check,
                path,
                f"aliases[{index}].canonical",
                alias.get("canonical"),
                "alias targets another alias",
            )
    leaks: list[tuple[str, str]] = []
    _walk_keys(ledger, "", leaks)
    for trail, key in leaks:
        report.fail(
            check,
            path,
            trail,
            key,
            "runtime-resolution structure is downstream operating-plane responsibility",
        )
    if len(report.failures) != before:
        return None
    return canonical_ids, set(alias_keys)


def check_rc014(docs: dict[str, dict], report: Report) -> None:
    """Identity registry closure (IR-001..IR-008)."""
    before = len(report.failures)
    actor = _check_identity_registry(
        "RC-014",
        ACTOR_REGISTRY_PATH,
        docs,
        report,
        "actors",
        "actor_statuses",
        "actor_kinds",
        ACTOR_FORBIDDEN_ENTRY_FIELDS,
    )
    surface = _check_identity_registry(
        "RC-014",
        SURFACE_REGISTRY_PATH,
        docs,
        report,
        "surfaces",
        "surface_statuses",
        None,
        SURFACE_FORBIDDEN_ENTRY_FIELDS,
    )
    # IR-007 registration closure: once in canonical_sources, once in the
    # compiler manifest's semantic_catalogs. SC-008 covers release inventory.
    registry = docs.get("semantics/canonical_sources.yaml") or {}
    registered = [
        s.get("path") for s in registry.get("sources") or [] if isinstance(s, dict)
    ]
    manifest = docs.get("semantics/generic_compiler_manifest.yaml") or {}
    requires = manifest.get("requires") or {}
    catalogs = requires.get("semantic_catalogs") if isinstance(requires, dict) else []
    for path in (ACTOR_REGISTRY_PATH, SURFACE_REGISTRY_PATH):
        name = path.removeprefix("semantics/")
        if registered.count(path) != 1:
            report.fail(
                "RC-014",
                "semantics/canonical_sources.yaml",
                "sources",
                path,
                f"registry must be registered exactly once (found {registered.count(path)})",
            )
        classified = sum(
            1
            for entries in (requires.values() if isinstance(requires, dict) else [])
            if isinstance(entries, list)
            for entry in entries
            if entry == name
        )
        if (
            not isinstance(catalogs, list)
            or catalogs.count(name) != 1
            or classified != 1
        ):
            report.fail(
                "RC-014",
                "semantics/generic_compiler_manifest.yaml",
                "requires.semantic_catalogs",
                name,
                "registry must be classified exactly once, under semantic_catalogs",
            )
    if len(report.failures) != before or actor is None or surface is None:
        return
    actor_ids, actor_aliases = actor
    surface_ids, surface_aliases = surface
    # IR-006: cross-dimension string equality is legal and is only reported.
    overlap = sorted((actor_ids | actor_aliases) & (surface_ids | surface_aliases))
    report.ok(
        "RC-014",
        f"identity registries closed: {len(actor_ids)} actors with {len(actor_aliases)} "
        f"typed aliases, {len(surface_ids)} surfaces with {len(surface_aliases)} typed "
        f"aliases; no cross-dimension ownership field, no runtime-resolution structure; "
        f"{len(overlap)} strings legally shared across dimensions {overlap}",
    )


REPO_OPS_IR_ID = "l9.repository-operations-ir/v1"
REPO_OPS_CLASS = "repository_operations_ir"
REPO_OPS_PYPROJECT_BINDING = "l9.binding/repository-operations-pyproject@1"
REPO_OPS_MAKEFILE_BINDING = "l9.binding/repository-operations-makefile@1"
REPO_OPS_PROFILE = "l9.projection/repository-operations-compiler@1"
REPO_OPS_FORBIDDEN = {
    "repository_specific_semantic_invention",
    "dependency_constraint_invention",
    "build_backend_invention",
    "target_artifact_as_semantic_authority",
    "node_or_package_json_semantics_in_first_version",
}


def _unique_entry(entries: object, key: str, value: str) -> tuple[dict | None, int]:
    if not isinstance(entries, list):
        return None, 0
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get(key) == value
    ]
    return (matches[0] if len(matches) == 1 else None, len(matches))


def _evaluate_rc015(docs: dict[str, dict], report: Report) -> None:
    ir_path = "semantics/ir_catalog.yaml"
    bindings_path = "semantics/binding_catalog.yaml"
    technologies_path = "semantics/technology_capabilities.yaml"
    profiles_path = "semantics/projection_profiles.yaml"
    capabilities_path = "semantics/capabilities.yaml"
    technology_profiles_path = "semantics/technology_profiles.yaml"

    ir_catalog = docs.get(ir_path) or {}
    ir, ir_count = _unique_entry(ir_catalog.get("irs"), "id", REPO_OPS_IR_ID)
    if ir_count != 1:
        report.fail(
            "RC-015",
            ir_path,
            "irs",
            REPO_OPS_IR_ID,
            f"IR must exist exactly once (found {ir_count})",
        )
    elif ir.get("semantic_class") != REPO_OPS_CLASS:
        report.fail(
            "RC-015",
            ir_path,
            f"irs[{REPO_OPS_IR_ID}].semantic_class",
            ir.get("semantic_class"),
            f"must be {REPO_OPS_CLASS!r}",
        )

    transitions = [
        item
        for item in ir_catalog.get("allowed_transitions") or []
        if isinstance(item, dict)
        and item.get("from") == REPO_OPS_IR_ID
        and item.get("to") == "l9.target-ir/v1"
    ]
    if len(transitions) != 1:
        report.fail(
            "RC-015",
            ir_path,
            "allowed_transitions",
            REPO_OPS_IR_ID,
            f"IR -> target transition must exist exactly once (found {len(transitions)})",
        )
    else:
        ops = set(transitions[0].get("operations") or [])
        for required in ("binding_selection", "lowering"):
            if required not in ops:
                report.fail(
                    "RC-015",
                    ir_path,
                    "allowed_transitions.operations",
                    required,
                    "required repository-operations lowering operation missing",
                )

    technologies = (docs.get(technologies_path) or {}).get("technologies") or []
    for technology in ("python", "toml", "makefile"):
        _entry, count = _unique_entry(technologies, "id", technology)
        if count != 1:
            report.fail(
                "RC-015",
                technologies_path,
                "technologies",
                technology,
                f"technology must exist exactly once (found {count})",
            )

    binding_list = (docs.get(bindings_path) or {}).get("bindings") or []
    pyproject, py_count = _unique_entry(binding_list, "id", REPO_OPS_PYPROJECT_BINDING)
    makefile, make_count = _unique_entry(binding_list, "id", REPO_OPS_MAKEFILE_BINDING)
    for binding, count, binding_id, technology, artifact in (
        (pyproject, py_count, REPO_OPS_PYPROJECT_BINDING, "toml", "pyproject.toml"),
        (makefile, make_count, REPO_OPS_MAKEFILE_BINDING, "makefile", "Makefile"),
    ):
        if count != 1 or binding is None:
            report.fail(
                "RC-015",
                bindings_path,
                "bindings",
                binding_id,
                f"binding must exist exactly once (found {count})",
            )
            continue
        if binding.get("source_ir") != REPO_OPS_CLASS:
            report.fail(
                "RC-015",
                bindings_path,
                f"{binding_id}.source_ir",
                binding.get("source_ir"),
                f"must consume {REPO_OPS_CLASS}",
            )
        if binding.get("target_ir") != "target_ir":
            report.fail(
                "RC-015",
                bindings_path,
                f"{binding_id}.target_ir",
                binding.get("target_ir"),
                "must produce target_ir",
            )
        target = binding.get("target") or {}
        if target.get("technology") != technology:
            report.fail(
                "RC-015",
                bindings_path,
                f"{binding_id}.target.technology",
                target.get("technology"),
                f"must target {technology}",
            )
        if target.get("artifact") != artifact:
            report.fail(
                "RC-015",
                bindings_path,
                f"{binding_id}.target.artifact",
                target.get("artifact"),
                f"must target {artifact}",
            )

    if makefile is not None:
        maps = makefile.get("maps")
        expected_maps = {"build": "build", "test": "test", "validate": "validate"}
        if maps != expected_maps:
            report.fail(
                "RC-015",
                bindings_path,
                f"{REPO_OPS_MAKEFILE_BINDING}.maps",
                maps,
                f"Makefile v1 map must be exactly {expected_maps}",
            )

    profile_list = (docs.get(profiles_path) or {}).get("projection_profiles") or []
    profile, profile_count = _unique_entry(profile_list, "id", REPO_OPS_PROFILE)
    if profile_count != 1 or profile is None:
        report.fail(
            "RC-015",
            profiles_path,
            "projection_profiles",
            REPO_OPS_PROFILE,
            f"profile must exist exactly once (found {profile_count})",
        )
    else:
        if profile.get("class") != "consumer":
            report.fail(
                "RC-015",
                profiles_path,
                f"{REPO_OPS_PROFILE}.class",
                profile.get("class"),
                "must be consumer",
            )
        sources = profile.get("sources") or {}
        required_selectors = {
            "ir_catalog": {
                '$.irs[?(@.id=="l9.repository-operations-ir/v1")]',
                '$.irs[?(@.id=="l9.target-ir/v1")]',
                '$.allowed_transitions[?(@.from=="l9.repository-operations-ir/v1")]',
            },
            "binding_catalog": {
                '$.bindings[?(@.id=="l9.binding/repository-operations-pyproject@1")]',
                '$.bindings[?(@.id=="l9.binding/repository-operations-makefile@1")]',
            },
            "technology_capabilities": {
                '$.technologies[?(@.id=="python")]',
                '$.technologies[?(@.id=="toml")]',
                '$.technologies[?(@.id=="makefile")]',
            },
        }
        all_selectors: list[str] = []
        for source_name, required in required_selectors.items():
            block = sources.get(source_name)
            selectors = block.get("selectors") if isinstance(block, dict) else None
            selector_set = set(map(str, selectors or []))
            all_selectors.extend(map(str, selectors or []))
            for selector in required:
                if selector not in selector_set:
                    report.fail(
                        "RC-015",
                        profiles_path,
                        f"{REPO_OPS_PROFILE}.sources.{source_name}.selectors",
                        selector,
                        "required selector missing",
                    )
        if any(
            'id=="node"' in selector or "package.json" in selector
            for selector in all_selectors
        ):
            report.fail(
                "RC-015",
                profiles_path,
                f"{REPO_OPS_PROFILE}.sources",
                all_selectors,
                "Node/package.json semantics are outside repository-operations profile v1",
            )
        forbidden = set(profile.get("forbidden") or [])
        missing_forbidden = sorted(REPO_OPS_FORBIDDEN - forbidden)
        if missing_forbidden:
            report.fail(
                "RC-015",
                profiles_path,
                f"{REPO_OPS_PROFILE}.forbidden",
                missing_forbidden,
                "required forbidden semantics missing",
            )

    capabilities = (docs.get(capabilities_path) or {}).get("capabilities")
    if capabilities != []:
        report.fail(
            "RC-015",
            capabilities_path,
            "capabilities",
            capabilities,
            "this slice must not globalize repository-operation capabilities",
        )

    technology_profiles = (docs.get(technology_profiles_path) or {}).get("profiles")
    if technology_profiles != []:
        report.fail(
            "RC-015",
            technology_profiles_path,
            "profiles",
            technology_profiles,
            "this slice must not add a technology profile for repository build metadata",
        )


def _check_rc015_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases = []

    case = copy.deepcopy(docs)
    binding, _ = _unique_entry(
        case["semantics/binding_catalog.yaml"]["bindings"],
        "id",
        REPO_OPS_PYPROJECT_BINDING,
    )
    binding["target"]["technology"] = "unregistered-toml"
    cases.append(("unregistered pyproject technology", case))

    case = copy.deepcopy(docs)
    binding, _ = _unique_entry(
        case["semantics/binding_catalog.yaml"]["bindings"],
        "id",
        REPO_OPS_MAKEFILE_BINDING,
    )
    binding["source_ir"] = "missing_repository_operations_ir"
    cases.append(("Makefile binding missing IR", case))

    case = copy.deepcopy(docs)
    binding, _ = _unique_entry(
        case["semantics/binding_catalog.yaml"]["bindings"],
        "id",
        REPO_OPS_MAKEFILE_BINDING,
    )
    binding["maps"]["publish"] = "publish"
    cases.append(("Makefile v1 adds publish", case))

    case = copy.deepcopy(docs)
    profile, _ = _unique_entry(
        case["semantics/projection_profiles.yaml"]["projection_profiles"],
        "id",
        REPO_OPS_PROFILE,
    )
    profile["sources"]["ir_catalog"]["selectors"] = [
        selector
        for selector in profile["sources"]["ir_catalog"]["selectors"]
        if REPO_OPS_IR_ID not in str(selector)
    ]
    cases.append(("profile omits repository operations IR", case))

    case = copy.deepcopy(docs)
    profile, _ = _unique_entry(
        case["semantics/projection_profiles.yaml"]["projection_profiles"],
        "id",
        REPO_OPS_PROFILE,
    )
    profile["sources"]["technology_capabilities"]["selectors"].append(
        '$.technologies[?(@.id=="node")]'
    )
    cases.append(("profile adds Node/package.json concern", case))

    case = copy.deepcopy(docs)
    case["semantics/capabilities.yaml"]["capabilities"].append(
        {"id": "l9.capability/repository-build"}
    )
    cases.append(("slice globalizes repository operation capability", case))

    case = copy.deepcopy(docs)
    case["semantics/technology_profiles.yaml"]["profiles"].append(
        {"id": "repo-build", "language": "python", "transport": "none"}
    )
    cases.append(("slice adds transport-bearing repository technology profile", case))

    for label, candidate in cases:
        candidate_report = Report()
        _evaluate_rc015(candidate, candidate_report)
        if not candidate_report.failures:
            report.fail(
                "RC-015",
                VALIDATOR_PATH,
                "negative_case",
                label,
                "negative case did not fail closed",
            )
    if not any(
        f.startswith("FAIL RC-015 scripts/validate-semantics.py negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-015-NEG",
            f"{len(cases)} repository-operations negative cases fail closed",
        )


def check_rc015(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc015(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-015",
            "repository operations IR, Python pyproject binding, Makefile v1 binding, target technologies, and consumer projection are structurally closed",
        )
        _check_rc015_negative_cases(docs, report)


STRATEGY_MODEL_PATH = "semantics/strategic_cognition_model.yaml"
STRATEGY_MODEL_ID = "l9.strategic-cognition-model/global@1"
STRATEGY_SOURCE_ID = "l9.source/strategic-cognition-model@1"
STRATEGY_SCOPE = "l9_global_strategic_cognition_semantics"
STRATEGY_INVARIANT_ID = "L9-STRATEGY-001"
STRATEGY_INVARIANT_STATEMENT = (
    "Plan Keeper owns the Strategic Plan. Strategic Plan Metacognitive Reasoner owns analysis of the reasoning "
    "processes that produce the Strategic Plan. The latter may teach the former but may never modify, supersede, "
    "or become strategic authority."
)
STRATEGY_OWNER = "Quantum-L9/.github"
PLAN_KEEPER = "plan_keeper"
METACOGNITIVE_REASONER = "strategic_plan_metacognitive_reasoner"
STRATEGY_TERMS = (
    "strategy",
    "strategic_cognition",
    "strategic_plan",
    "strategic_intent",
    PLAN_KEEPER,
    METACOGNITIVE_REASONER,
    "current_meta_view",
)
STRATEGY_AUTHORITY_SOURCE = "strategic_authority"
STRATEGY_RESOLUTION_REF = "authority_model.yaml#strategic_cognition_authority"
STRATEGY_COMPILER_BOUNDARY_REF = "vocabulary.yaml#stage_rules.reasoning_plane_rule"
METACOGNITION_DENIED = {
    "strategic_plan_mutation",
    "strategic_plan_supersession",
    "strategic_authority",
}
# The Plan Keeper's admitted permissions, exactly. An allowlist, not a
# blocklist: any other grant is authority self-expansion and fails closed.
# v3.19.0 (ADR-018) admits emission of the planning episode and the revision
# candidate; RC-026 requires both and keeps them zero-authority.
PLAN_KEEPER_MAY = {
    "revise_strategic_plan_within_granted_strategic_authority",
    "consume_planning_cognition_lessons",
    "emit_strategic_planning_episode",
    "emit_strategic_plan_revision_candidate",
}
PLAN_KEEPER_MAY_NOT = {
    "acquire_truth_source_ownership_by_consuming_projections",
    "derive_authority_from_reasoning_capability",
    "become_execution_or_implementation_authority_by_implication",
    "revise_strategic_plan_beyond_granted_strategic_authority",
}
METACOGNITION_MAY_NOT = {
    "modify_strategic_plan",
    "supersede_plan_keeper",
    "become_strategic_authority",
    "grant_itself_strategic_authority",
    "convert_metacognitive_conclusions_into_strategic_decisions",
}
# The Reasoner's admitted permissions, exactly. An allowlist, not a blocklist:
# any other grant (edit, approve, grant, ...) fails closed.
# v3.19.0 (ADR-018) admits emission of the advisory metacognitive analysis.
METACOGNITION_MAY = {
    "analyze_plan_keeper_reasoning_episodes",
    "compare_planning_reasoning_expectations_outcomes_and_revisions",
    "identify_recurring_planning_reasoning_strengths_and_failure_patterns",
    "emit_planning_cognition_lessons_for_plan_keeper",
    "emit_strategic_plan_metacognitive_analysis",
}
# Model sections admitted by v3.8.0, plus the reasoning_artifacts anchors
# admitted by v3.19.0 (ADR-018). Anything else (plan graph, runtime, prompts,
# actor bindings, capabilities, artifact classes) is out of scope.
STRATEGY_MODEL_KEYS = {
    "schema",
    "artifact_id",
    "canonical",
    "authority",
    "canonical_source",
    "governed_by",
    "purpose",
    "plane",
    "global_rules",
    "concepts",
    "reasoning_artifacts",
    "roles",
    "authority_separation",
}


STRATEGY_AUTHORITY_PATH = "semantics/authority_model.yaml"


def _rc016_ledger(docs: dict[str, dict], report: Report) -> dict:
    model_path = STRATEGY_MODEL_PATH
    holders = [
        path
        for path, doc in docs.items()
        if doc.get("artifact_id") == STRATEGY_MODEL_ID
    ]
    if holders != [model_path]:
        report.fail(
            "RC-016",
            model_path,
            "artifact_id",
            holders,
            f"{STRATEGY_MODEL_ID} must be declared exactly once, by {model_path}",
        )
    model = docs.get(model_path) or {}
    authority = model.get("authority") or {}
    if model.get("canonical") is not True:
        report.fail(
            "RC-016",
            model_path,
            "canonical",
            model.get("canonical"),
            "Strategic Cognition ledger must be canonical",
        )
    if authority.get("owner") != STRATEGY_OWNER:
        report.fail(
            "RC-016",
            model_path,
            AUTHORITY_OWNER_FIELD,
            authority.get("owner"),
            f"Strategic Cognition semantics are owned by {STRATEGY_OWNER}",
        )
    if authority.get("scope") != STRATEGY_SCOPE:
        report.fail(
            "RC-016",
            model_path,
            "authority.scope",
            authority.get("scope"),
            f"must be {STRATEGY_SCOPE!r}",
        )
    if authority.get("authority_class") != "canonical":
        report.fail(
            "RC-016",
            model_path,
            "authority.authority_class",
            authority.get("authority_class"),
            "must be canonical",
        )
    extra_keys = sorted(set(model) - STRATEGY_MODEL_KEYS)
    if extra_keys:
        report.fail(
            "RC-016",
            model_path,
            "keys",
            extra_keys,
            "model declares sections outside the admitted Strategic Cognition semantics",
        )
    return model


def _rc016_registration(docs: dict[str, dict], report: Report) -> None:
    model_path = STRATEGY_MODEL_PATH
    registry_path = "semantics/canonical_sources.yaml"
    manifest_path = "semantics/generic_compiler_manifest.yaml"
    sources = (docs.get(registry_path) or {}).get("sources") or []
    registered = [
        s for s in sources if isinstance(s, dict) and s.get("path") == model_path
    ]
    if len(registered) != 1:
        report.fail(
            "RC-016",
            registry_path,
            "sources",
            model_path,
            f"ledger must be registered exactly once (found {len(registered)})",
        )
    elif (
        registered[0].get("id") != STRATEGY_SOURCE_ID
        or registered[0].get("canonical") is not True
    ):
        report.fail(
            "RC-016",
            registry_path,
            "sources.id",
            registered[0].get("id"),
            f"registration must be canonical {STRATEGY_SOURCE_ID}",
        )

    manifest = docs.get(manifest_path) or {}
    requires = manifest.get("requires") or {}
    catalog_name = model_path.removeprefix("semantics/")
    classes = [
        cls
        for cls, names in requires.items()
        if isinstance(names, list) and catalog_name in names
    ]
    if classes != ["semantic_catalogs"]:
        report.fail(
            "RC-016",
            manifest_path,
            "requires",
            classes,
            "ledger must be classified exactly once, as a semantic catalog",
        )
    if "strategic_cognition" not in (manifest.get("does_not_own") or []):
        report.fail(
            "RC-016",
            manifest_path,
            "does_not_own",
            manifest.get("does_not_own"),
            "Semantic Compiler must not own Strategic Cognition",
        )
    if any("strateg" in str(cap) for cap in manifest.get("capabilities") or []):
        report.fail(
            "RC-016",
            manifest_path,
            "capabilities",
            manifest.get("capabilities"),
            "Semantic Compiler must not gain a strategic capability",
        )


def _rc016_invariant(docs: dict[str, dict], report: Report) -> None:
    invariants_path = "semantics/invariants.yaml"
    invariants = (docs.get(invariants_path) or {}).get("invariants") or []
    invariant, count = _unique_entry(invariants, "id", STRATEGY_INVARIANT_ID)
    family = [
        i.get("id")
        for i in invariants
        if isinstance(i, dict) and str(i.get("id", "")).startswith("L9-STRATEGY-")
    ]
    mentions = [
        i.get("id")
        for i in invariants
        if isinstance(i, dict) and "Plan Keeper" in str(i.get("statement", ""))
    ]
    if count != 1 or invariant is None:
        report.fail(
            "RC-016",
            invariants_path,
            "invariants",
            STRATEGY_INVARIANT_ID,
            f"Strategic Cognition invariant must exist exactly once (found {count})",
        )
    else:
        if (
            " ".join(str(invariant.get("statement", "")).split())
            != STRATEGY_INVARIANT_STATEMENT
        ):
            report.fail(
                "RC-016",
                invariants_path,
                f"{STRATEGY_INVARIANT_ID}.statement",
                invariant.get("statement"),
                "statement must preserve the admitted authority separation exactly",
            )
        if (
            invariant.get("scope") != "global"
            or invariant.get("owner") != STRATEGY_OWNER
        ):
            report.fail(
                "RC-016",
                invariants_path,
                f"{STRATEGY_INVARIANT_ID}.scope",
                invariant.get("scope"),
                "must be a global invariant owned by the global authority",
            )
    if family != [STRATEGY_INVARIANT_ID] or mentions != [STRATEGY_INVARIANT_ID]:
        report.fail(
            "RC-016",
            invariants_path,
            "invariants",
            sorted(set(family + mentions)),
            "Strategic Cognition law must be exactly one constitutional invariant",
        )


def _rc016_plan_keeper(model: dict, report: Report) -> dict:
    model_path = STRATEGY_MODEL_PATH
    concepts = model.get("concepts") or {}
    keeper = (model.get("roles") or {}).get(PLAN_KEEPER) or {}
    if (concepts.get("strategic_plan") or {}).get("owner_role") != PLAN_KEEPER:
        report.fail(
            "RC-016",
            model_path,
            "concepts.strategic_plan.owner_role",
            (concepts.get("strategic_plan") or {}).get("owner_role"),
            "Plan Keeper must own the Strategic Plan",
        )
    if keeper.get("owns") != ["strategic_plan"]:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{PLAN_KEEPER}.owns",
            keeper.get("owns"),
            "Plan Keeper owns the Strategic Plan and nothing else; consuming projections transfers no truth-source ownership",
        )
    if "underlying_truth_sources" not in (keeper.get("does_not_own") or []):
        report.fail(
            "RC-016",
            model_path,
            f"roles.{PLAN_KEEPER}.does_not_own",
            keeper.get("does_not_own"),
            "Plan Keeper must not own underlying truth sources",
        )
    if keeper.get("authority_source") != STRATEGY_AUTHORITY_SOURCE:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{PLAN_KEEPER}.authority_source",
            keeper.get("authority_source"),
            "Plan Keeper authority must come only from explicitly granted strategic authority",
        )
    granted = [str(item) for item in keeper.get("may") or []]
    if sorted(granted) != sorted(PLAN_KEEPER_MAY):
        report.fail(
            "RC-016",
            model_path,
            f"roles.{PLAN_KEEPER}.may",
            keeper.get("may"),
            "Plan Keeper may hold exactly its admitted permissions; any other grant is authority self-expansion and fails closed",
        )
    missing_keeper_denials = sorted(
        PLAN_KEEPER_MAY_NOT - set(keeper.get("may_not") or [])
    )
    if missing_keeper_denials:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{PLAN_KEEPER}.may_not",
            missing_keeper_denials,
            "required Plan Keeper prohibitions missing",
        )
    return keeper


def _rc016_reasoner(model: dict, report: Report) -> None:
    model_path = STRATEGY_MODEL_PATH
    reasoner = (model.get("roles") or {}).get(METACOGNITIVE_REASONER) or {}
    if reasoner.get("owns") != ["strategic_plan_reasoning_analysis"]:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.owns",
            reasoner.get("owns"),
            "Reasoner owns only analysis of Strategic Plan reasoning",
        )
    if (
        reasoner.get("subject")
        != "reasoning_processes_that_produce_and_revise_the_strategic_plan"
        or reasoner.get("universal_metacognitive_authority") is not False
    ):
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.subject",
            reasoner.get("subject"),
            "Reasoner subject is Strategic Plan reasoning only, never universal metacognition",
        )
    missing_denials = sorted(METACOGNITION_MAY_NOT - set(reasoner.get("may_not") or []))
    if missing_denials:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.may_not",
            missing_denials,
            "required metacognition prohibitions missing",
        )
    granted = [str(item) for item in reasoner.get("may") or []]
    if sorted(granted) != sorted(METACOGNITION_MAY):
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.may",
            reasoner.get("may"),
            "Reasoner may hold exactly its admitted analysis permissions; any other grant, including Strategic Plan mutation or strategic authority, fails closed",
        )
    if reasoner.get("strategic_authority") is not False:
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.strategic_authority",
            reasoner.get("strategic_authority"),
            "Reasoner must never be strategic authority",
        )
    if (
        reasoner.get("output_authority") != "advisory"
        or reasoner.get("output_consumer") != PLAN_KEEPER
    ):
        report.fail(
            "RC-016",
            model_path,
            f"roles.{METACOGNITIVE_REASONER}.output_authority",
            reasoner.get("output_authority"),
            "Reasoner output is advisory to the Plan Keeper",
        )


def _rc016_roles_not_actors(model: dict, docs: dict[str, dict], report: Report) -> None:
    roles = model.get("roles") or {}
    for role_id in (PLAN_KEEPER, METACOGNITIVE_REASONER):
        role = roles.get(role_id) or {}
        if (
            role.get("role_kind") != "semantic_role"
            or role.get("actor_identity_binding") != "none"
        ):
            report.fail(
                "RC-016",
                STRATEGY_MODEL_PATH,
                f"roles.{role_id}.actor_identity_binding",
                role.get("actor_identity_binding"),
                "strategic roles are semantic roles, not ActorIdentities",
            )
    actors = (docs.get(ACTOR_REGISTRY_PATH) or {}).get("actors") or []
    actor_ids = {str(a.get("id")) for a in actors if isinstance(a, dict)}
    bound = sorted(
        actor_ids
        & {
            PLAN_KEEPER,
            METACOGNITIVE_REASONER,
            "plan-keeper",
            "strategic-plan-metacognitive-reasoner",
        }
    )
    if bound:
        report.fail(
            "RC-016",
            ACTOR_REGISTRY_PATH,
            "actors",
            bound,
            "strategic roles must not be registered as actors",
        )


def _rc016_model_separation(model: dict, report: Report) -> None:
    separation = model.get("authority_separation") or {}
    relation = separation.get("teaching_relation") or {}
    expected = (
        (separation.get("invariant_ref"), STRATEGY_INVARIANT_ID),
        (separation.get("resolution_ref"), STRATEGY_RESOLUTION_REF),
        (separation.get("strategic_plan_owner"), PLAN_KEEPER),
        (
            separation.get("strategic_plan_reasoning_analysis_owner"),
            METACOGNITIVE_REASONER,
        ),
        (relation.get("from"), METACOGNITIVE_REASONER),
        (relation.get("to"), PLAN_KEEPER),
        (relation.get("authority_effect"), "none"),
    )
    if any(actual != wanted for actual, wanted in expected):
        report.fail(
            "RC-016",
            STRATEGY_MODEL_PATH,
            "authority_separation",
            separation,
            "Plan Keeper / metacognition separation must be declared with an authority-free teaching relation",
        )


def _rc016_authority_resolution(
    docs: dict[str, dict], keeper: dict, report: Report
) -> None:
    authority_path = STRATEGY_AUTHORITY_PATH
    resolution = (docs.get(authority_path) or {}).get(
        "strategic_cognition_authority"
    ) or {}
    if (
        resolution.get("strategic_plan_owner") != PLAN_KEEPER
        or resolution.get("global_semantics_owner") != STRATEGY_OWNER
    ):
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.strategic_plan_owner",
            resolution.get("strategic_plan_owner"),
            "authority model must resolve the Strategic Plan to the Plan Keeper",
        )
    linked = (
        resolution.get("detailed_model")
        == STRATEGY_MODEL_PATH.removeprefix("semantics/")
        and resolution.get("invariant_ref") == STRATEGY_INVARIANT_ID
        and resolution.get("strategic_plan_authority_source")
        == keeper.get("authority_source")
    )
    if not linked:
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.detailed_model",
            resolution.get("detailed_model"),
            "authority resolution must reference the model and invariant and agree with the Plan Keeper authority source",
        )
    if (
        resolution.get("strategic_plan_reasoning_analysis_owner")
        != METACOGNITIVE_REASONER
    ):
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.strategic_plan_reasoning_analysis_owner",
            resolution.get("strategic_plan_reasoning_analysis_owner"),
            "authority model must resolve Strategic Plan reasoning analysis to the Reasoner",
        )
    missing_denied = sorted(
        METACOGNITION_DENIED - set(resolution.get("metacognition_denied") or [])
    )
    if missing_denied:
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.metacognition_denied",
            missing_denied,
            "metacognition must be denied Strategic Plan mutation, supersession, and strategic authority",
        )
    if resolution.get("roles_are_actor_identities") is not False:
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.roles_are_actor_identities",
            resolution.get("roles_are_actor_identities"),
            "strategic roles must not be ActorIdentities",
        )
    if "semantic_compiler_does_not_own_strategic_cognition" not in (
        resolution.get("rules") or []
    ):
        report.fail(
            "RC-016",
            authority_path,
            "strategic_cognition_authority.rules",
            resolution.get("rules"),
            "Semantic Compiler exclusion rule missing",
        )


def _rc016_meta_view_authority(model: dict, report: Report) -> None:
    model_path = STRATEGY_MODEL_PATH
    view = (model.get("concepts") or {}).get("current_meta_view") or {}
    properties = view.get("properties") or {}
    if (
        view.get("authority_class") != "derived"
        or view.get("authoritative") is not False
        or view.get("canonical_source") is not False
    ):
        report.fail(
            "RC-016",
            model_path,
            "concepts.current_meta_view.authority_class",
            view.get("authority_class"),
            "Current Meta View is derived and never canonical authority",
        )
    if (
        properties.get("may_reinterpret_source_truth") is not False
        or properties.get("may_create_authority") is not False
    ):
        report.fail(
            "RC-016",
            model_path,
            "concepts.current_meta_view.properties",
            properties,
            "Current Meta View must not reinterpret source truth or create authority",
        )
    for flag in (
        "derived",
        "disposable",
        "provenance_preserving",
        "invalidated_when_source_truth_changes",
    ):
        if properties.get(flag) is not True:
            report.fail(
                "RC-016",
                model_path,
                f"concepts.current_meta_view.properties.{flag}",
                properties.get(flag),
                "required Current Meta View property missing",
            )


def _rc016_meta_view_reuse(model: dict, docs: dict[str, dict], report: Report) -> None:
    model_path = STRATEGY_MODEL_PATH
    artifacts_path = "semantics/artifact_model.yaml"
    view = (model.get("concepts") or {}).get("current_meta_view") or {}
    artifact_classes = (docs.get(artifacts_path) or {}).get("artifacts") or {}
    for field, class_name in (
        ("artifact_class_ref", "composed_projection"),
        ("component_artifact_class_ref", "projection_artifact"),
    ):
        reused = (
            view.get(field) == class_name
            and (artifact_classes.get(class_name) or {}).get("authority_class")
            == "derived"
        )
        if not reused:
            report.fail(
                "RC-016",
                model_path,
                f"concepts.current_meta_view.{field}",
                view.get(field),
                f"Current Meta View must reuse the existing derived {class_name} class",
            )
    schema_ids = {doc.get("artifact_id") for doc in docs.values()}
    if (
        view.get("schema_ref") != "l9.schema/composed-projection@1"
        or view.get("schema_ref") not in schema_ids
    ):
        report.fail(
            "RC-016",
            model_path,
            "concepts.current_meta_view.schema_ref",
            view.get("schema_ref"),
            "Current Meta View must reuse the composed-projection schema",
        )
    if "current_meta_view" in artifact_classes:
        report.fail(
            "RC-016",
            artifacts_path,
            "artifacts",
            "current_meta_view",
            "Current Meta View must not be a new artifact class",
        )


def _rc016_plane_and_terms(model: dict, docs: dict[str, dict], report: Report) -> None:
    plane = model.get("plane") or {}
    expected_plane = (
        plane.get("conceptual_plane") == "reasoning_plane"
        and plane.get("semantic_compiler_owner") is False
        and plane.get("runtime_owned_here") is False
        and plane.get("compiler_boundary_ref") == STRATEGY_COMPILER_BOUNDARY_REF
    )
    if not expected_plane:
        report.fail(
            "RC-016",
            STRATEGY_MODEL_PATH,
            "plane",
            plane,
            "Strategic Cognition belongs to the Reasoning Plane, is not compiler-owned, and owns no runtime",
        )
    vocabulary = docs.get(VOCABULARY_PATH) or {}
    reasoning_rule = (vocabulary.get("stage_rules") or {}).get(
        "reasoning_plane_rule"
    ) or {}
    if reasoning_rule.get(
        "current_dependency_allowed"
    ) is not False or "MUST remain independent" not in str(
        reasoning_rule.get("rule", "")
    ):
        report.fail(
            "RC-016",
            VOCABULARY_PATH,
            "stage_rules.reasoning_plane_rule",
            reasoning_rule,
            "Semantic Compiler must remain independent of the Reasoning Plane",
        )
    terms = vocabulary.get("terms") or {}
    model_name = STRATEGY_MODEL_PATH.removeprefix("semantics/")
    for term in STRATEGY_TERMS:
        if (terms.get(term) or {}).get("detailed_model") != model_name:
            report.fail(
                "RC-016",
                VOCABULARY_PATH,
                f"terms.{term}",
                terms.get(term),
                "Strategic Cognition term must exist and defer to the Strategic Cognition model",
            )


def _evaluate_rc016(docs: dict[str, dict], report: Report) -> None:
    model = _rc016_ledger(docs, report)
    _rc016_registration(docs, report)
    _rc016_invariant(docs, report)
    keeper = _rc016_plan_keeper(model, report)
    _rc016_reasoner(model, report)
    _rc016_roles_not_actors(model, docs, report)
    _rc016_model_separation(model, report)
    _rc016_authority_resolution(docs, keeper, report)
    _rc016_meta_view_authority(model, report)
    _rc016_meta_view_reuse(model, docs, report)
    _rc016_plane_and_terms(model, docs, report)


def _check_rc016_negative_cases(docs: dict[str, dict], report: Report) -> None:
    model = STRATEGY_MODEL_PATH
    authority = "semantics/authority_model.yaml"
    reasoner = f"roles.{METACOGNITIVE_REASONER}"
    cases = []

    case = copy.deepcopy(docs)
    case[model]["roles"][METACOGNITIVE_REASONER]["may"].append("edit_strategic_plan")
    cases.append(
        ("Reasoner gains Strategic Plan mutation", case, model, f"{reasoner}.may")
    )

    case = copy.deepcopy(docs)
    case[model]["roles"][METACOGNITIVE_REASONER]["strategic_authority"] = True
    cases.append(
        (
            "Reasoner becomes strategic authority",
            case,
            model,
            f"{reasoner}.strategic_authority",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["concepts"]["current_meta_view"]["authority_class"] = "canonical"
    cases.append(
        (
            "Current Meta View promoted to canonical authority",
            case,
            model,
            "concepts.current_meta_view.authority_class",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["concepts"]["current_meta_view"]["properties"][
        "may_reinterpret_source_truth"
    ] = True
    cases.append(
        (
            "Current Meta View may reinterpret source truth",
            case,
            model,
            "concepts.current_meta_view.properties",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["roles"][PLAN_KEEPER]["owns"].append("underlying_truth_sources")
    cases.append(
        (
            "Plan Keeper owns truth sources by consuming projections",
            case,
            model,
            f"roles.{PLAN_KEEPER}.owns",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["roles"][PLAN_KEEPER]["may"].append(
        "revise_strategic_plan_without_authority"
    )
    cases.append(
        (
            "Plan Keeper gains an unadmitted permission",
            case,
            model,
            f"roles.{PLAN_KEEPER}.may",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["roles"][PLAN_KEEPER]["may_not"].remove(
        "revise_strategic_plan_beyond_granted_strategic_authority"
    )
    cases.append(
        (
            "Plan Keeper beyond-scope prohibition removed",
            case,
            model,
            f"roles.{PLAN_KEEPER}.may_not",
        )
    )

    case = copy.deepcopy(docs)
    case[model]["authority"]["owner"] = "l9-semantic-compiler"
    cases.append(
        (
            "Strategic Cognition owned by Semantic Compiler",
            case,
            model,
            AUTHORITY_OWNER_FIELD,
        )
    )

    case = copy.deepcopy(docs)
    del case[authority]["strategic_cognition_authority"]["metacognition_denied"]
    cases.append(
        (
            "Plan Keeper / metacognition separation removed",
            case,
            authority,
            "strategic_cognition_authority.metacognition_denied",
        )
    )

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc016(candidate, candidate_report)
        prefix = f"FAIL RC-016 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-016",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith("FAIL RC-016 scripts/validate-semantics.py negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-016-NEG",
            f"{len(cases)} Strategic Cognition negative cases fail closed for their intended reason",
        )


def check_rc016(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc016(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-016",
            "Strategic Cognition ledger, invariant, Plan Keeper / Strategic Plan Metacognitive Reasoner authority separation, Current Meta View projection reuse, and Reasoning Plane boundary are structurally closed",
        )
        _check_rc016_negative_cases(docs, report)


# RC-017 validation-completeness closure. The validation contract must make
# incomplete applicable validation coverage incapable of resolving to
# ``satisfied``, and the Cursor-Governance operating-plane projection must
# carry the operative contract semantics (not only headings and outcomes)
# together with the global invariants those semantics cite. No new contract,
# invariant, profile, or result taxonomy is admitted here; existing law
# (L9-ASSURANCE-001, L9-UNKNOWN-001, L9-VALIDATION-001, L9-CORRECTNESS-001,
# L9-EVIDENCE-001) is operationalized through the existing contract.
CONTRACTS_PATH = "semantics/contracts.yaml"
PROFILES_PATH = "semantics/projection_profiles.yaml"
INVARIANTS_PATH = "semantics/invariants.yaml"
VALIDATION_CONTRACT_ID = "l9.contract/validation-and-correctness@1"
VALIDATION_CONTRACT_OWNER = "Quantum-L9/.github"
# The uniform contract shape of contracts.yaml. A field outside it on the
# validation contract is a result taxonomy or sub-contract smuggled in.
CONTRACT_SHAPE = {
    "id",
    "purpose",
    "scope",
    "owner",
    "source_invariants",
    "applies_to",
    "requires",
    "guarantees",
    "forbidden",
    "outcomes",
}
VALIDATION_SOURCE_INVARIANTS = {
    "L9-VALIDATION-001",
    "L9-CORRECTNESS-001",
    "L9-EVIDENCE-001",
    "L9-UNKNOWN-001",
    "L9-ASSURANCE-001",
}
VALIDATION_REQUIRED_GUARANTEES = {
    # completeness (this change)
    "validation_success_requires_every_applicable_required_criterion_to_be_evaluated_and_satisfied",
    "unavailable_unreadable_unexecuted_or_unresolved_required_criteria_preclude_success",
    "validation_coverage_is_explicit_and_evidence_bound",
    # existing unresolved-stays-unresolved law the completeness obligations rest on
    "unresolved_validation_semantics_remain_unresolved",
}
VALIDATION_REQUIRED_FORBIDDEN = {
    # completeness (this change)
    "silent_skip_of_applicable_required_validation",
    "default_success_on_missing_unreadable_unexecuted_or_unresolved_required_validation",
    "partial_validation_coverage_reported_as_complete",
    # existing coercion prohibition the completeness obligations rest on
    "unknown_to_success_coercion",
}
# The outcome algebra, exactly. Keys are the existing three; ``satisfied`` is
# bound to complete evaluation of every applicable required criterion, and
# incomplete coverage lands in ``unresolved``. Any other mapping fails closed.
VALIDATION_OUTCOMES = {
    "satisfied": "every_applicable_required_criterion_was_evaluated_and_evidence_supports_the_candidate_against_each",
    "rejected": "evidence_refutes_the_candidate_against_declared_criteria",
    "unresolved": "validation_cannot_resolve_the_candidate_against_every_applicable_required_criterion",
}
VALIDATION_SUCCESS_OUTCOME = "satisfied"
CG_PROFILE_ID = "l9.projection/cursor-governance-operating-plane@1"
CG_CONSUMER = "Cursor-Governance"
CG_CONTRACT_SELECTORS = {
    "$.contracts[*].id",
    "$.contracts[*].purpose",
    "$.contracts[*].scope",
    "$.contracts[*].source_invariants",
    "$.contracts[*].requires",
    "$.contracts[*].guarantees",
    "$.contracts[*].forbidden",
    "$.contracts[*].outcomes",
}
GLOBAL_INVARIANTS_SELECTOR = '$.invariants[?(@.scope=="global")]'


def _rc017_contract(docs: dict[str, dict], report: Report) -> dict | None:
    catalog = docs.get(CONTRACTS_PATH) or {}
    contracts = catalog.get("contracts")
    contract, count = _unique_entry(contracts, "id", VALIDATION_CONTRACT_ID)
    if count != 1 or contract is None:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            "contracts",
            VALIDATION_CONTRACT_ID,
            f"validation contract must exist exactly once (found {count})",
        )
        return None
    label = f"contracts[{VALIDATION_CONTRACT_ID}]"
    if contract.get("owner") != VALIDATION_CONTRACT_OWNER:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.owner",
            contract.get("owner"),
            f"validation law is owned by {VALIDATION_CONTRACT_OWNER}",
        )
    if contract.get("scope") != "global":
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.scope",
            contract.get("scope"),
            "validation contract must be global",
        )
    extra_keys = sorted(set(contract) - CONTRACT_SHAPE)
    if extra_keys:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.keys",
            extra_keys,
            "validation contract declares fields outside the uniform contract shape; "
            "no result taxonomy or sub-contract is admitted here",
        )
    # No result taxonomy is defined by the contract catalog.
    outcome_semantics = catalog.get("outcome_semantics") or {}
    if (
        outcome_semantics.get("scope") != "contract_local"
        or outcome_semantics.get("global_error_taxonomy_defined_here") is not False
    ):
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            "outcome_semantics",
            outcome_semantics,
            "contract outcomes stay contract-local; the catalog must not define a result taxonomy",
        )
    return contract


def _rc017_source_invariants(
    contract: dict, docs: dict[str, dict], report: Report
) -> None:
    label = f"contracts[{VALIDATION_CONTRACT_ID}]"
    declared = [str(item) for item in contract.get("source_invariants") or []]
    missing = sorted(VALIDATION_SOURCE_INVARIANTS - set(declared))
    if missing:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.source_invariants",
            missing,
            "validation contract must rest on the existing validation and assurance invariants",
        )
    duplicates = sorted({item for item in declared if declared.count(item) > 1})
    if duplicates:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.source_invariants",
            duplicates,
            "source invariant declared more than once",
        )
    invariants = (docs.get(INVARIANTS_PATH) or {}).get("invariants") or []
    for invariant_id in sorted(VALIDATION_SOURCE_INVARIANTS):
        invariant, count = _unique_entry(invariants, "id", invariant_id)
        if count != 1 or invariant is None:
            report.fail(
                "RC-017",
                INVARIANTS_PATH,
                "invariants",
                invariant_id,
                f"source invariant must exist exactly once (found {count})",
            )
        elif (
            invariant.get("scope") != "global"
            or invariant.get("owner") != VALIDATION_CONTRACT_OWNER
        ):
            report.fail(
                "RC-017",
                INVARIANTS_PATH,
                f"invariants[{invariant_id}].scope",
                invariant.get("scope"),
                "source invariant must be a global invariant owned by the global authority",
            )


def _rc017_obligations(contract: dict, report: Report) -> None:
    label = f"contracts[{VALIDATION_CONTRACT_ID}]"
    for field, required in (
        ("guarantees", VALIDATION_REQUIRED_GUARANTEES),
        ("forbidden", VALIDATION_REQUIRED_FORBIDDEN),
    ):
        values = contract.get(field)
        if not isinstance(values, list) or not all(
            isinstance(v, str) and v.strip() for v in values
        ):
            report.fail(
                "RC-017",
                CONTRACTS_PATH,
                f"{label}.{field}",
                values,
                "must be a list of non-empty strings",
            )
            continue
        missing = sorted(required - set(values))
        if missing:
            report.fail(
                "RC-017",
                CONTRACTS_PATH,
                f"{label}.{field}",
                missing,
                f"required validation-completeness {field} missing",
            )
    requires = contract.get("requires")
    if not isinstance(requires, list) or not requires:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.requires",
            requires,
            "validation contract must declare its requires",
        )


def _rc017_outcomes(contract: dict, report: Report) -> None:
    label = f"contracts[{VALIDATION_CONTRACT_ID}]"
    outcomes = contract.get("outcomes")
    if not isinstance(outcomes, dict):
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.outcomes",
            outcomes,
            "outcome algebra missing",
        )
        return
    if set(outcomes) != set(VALIDATION_OUTCOMES):
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.outcomes",
            sorted(map(str, outcomes)),
            f"outcome keys must be exactly {sorted(VALIDATION_OUTCOMES)}; no new result taxonomy",
        )
        return
    values = [str(v) for v in outcomes.values()]
    if len(set(values)) != len(values):
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.outcomes",
            outcomes,
            "satisfied, rejected, and unresolved must remain distinct outcomes",
        )
        return
    success = outcomes.get(VALIDATION_SUCCESS_OUTCOME)
    for key in ("rejected", "unresolved"):
        if outcomes.get(key) == success:
            report.fail(
                "RC-017",
                CONTRACTS_PATH,
                f"{label}.outcomes",
                outcomes,
                f"{key} must not resolve to the success outcome",
            )
    if outcomes != VALIDATION_OUTCOMES:
        report.fail(
            "RC-017",
            CONTRACTS_PATH,
            f"{label}.outcomes",
            outcomes,
            "outcome algebra must bind satisfied to complete evaluation of every applicable "
            f"required criterion and route incomplete coverage to unresolved: {VALIDATION_OUTCOMES}",
        )


def _rc017_projection(docs: dict[str, dict], report: Report) -> None:
    catalog = docs.get(PROFILES_PATH) or {}
    profiles = catalog.get("projection_profiles")
    profile, count = _unique_entry(profiles, "id", CG_PROFILE_ID)
    if count != 1 or profile is None:
        report.fail(
            "RC-017",
            PROFILES_PATH,
            "projection_profiles",
            CG_PROFILE_ID,
            f"Cursor-Governance operating-plane profile must exist exactly once (found {count})",
        )
        return
    _rc017_profile_identity(profile, report)
    label = f"projection_profiles[{CG_PROFILE_ID}]"
    sources = profile.get("sources")
    if not isinstance(sources, dict):
        report.fail(
            "RC-017",
            PROFILES_PATH,
            f"{label}.sources",
            sources,
            "profile sources must be a source-local selector mapping",
        )
        return
    source_classes = catalog.get("source_classes") or {}
    for name in ("contracts", "invariants"):
        if name not in source_classes:
            report.fail(
                "RC-017",
                PROFILES_PATH,
                f"{label}.sources.{name}",
                name,
                "source does not resolve to source_classes",
            )
    _rc017_projection_selectors(label, sources, report)


def _rc017_profile_identity(profile: dict, report: Report) -> None:
    label = f"projection_profiles[{CG_PROFILE_ID}]"
    if profile.get("class") != "consumer" or profile.get("consumer") != CG_CONSUMER:
        report.fail(
            "RC-017",
            PROFILES_PATH,
            f"{label}.consumer",
            profile.get("consumer"),
            f"must be a consumer profile for {CG_CONSUMER}",
        )


def _rc017_projection_selectors(label: str, sources: dict, report: Report) -> None:
    contracts_block = sources.get("contracts")
    contract_selectors = (
        contracts_block.get("selectors") if isinstance(contracts_block, dict) else None
    )
    if not isinstance(contract_selectors, list):
        report.fail(
            "RC-017",
            PROFILES_PATH,
            f"{label}.sources.contracts.selectors",
            contract_selectors,
            "contract projection must own a selectors list",
        )
    else:
        missing = sorted(CG_CONTRACT_SELECTORS - set(map(str, contract_selectors)))
        if missing:
            report.fail(
                "RC-017",
                PROFILES_PATH,
                f"{label}.sources.contracts.selectors",
                missing,
                "operating-plane contract projection must carry the operative contract "
                "semantics, not only headings and outcomes",
            )
    invariants_block = sources.get("invariants")
    invariant_selectors = (
        invariants_block.get("selectors")
        if isinstance(invariants_block, dict)
        else None
    )
    if not isinstance(
        invariant_selectors, list
    ) or GLOBAL_INVARIANTS_SELECTOR not in set(map(str, invariant_selectors)):
        report.fail(
            "RC-017",
            PROFILES_PATH,
            f"{label}.sources.invariants.selectors",
            invariant_selectors,
            f"operating-plane projection must carry the global invariants its contracts cite "
            f"via {GLOBAL_INVARIANTS_SELECTOR}",
        )


def _evaluate_rc017(docs: dict[str, dict], report: Report) -> None:
    contract = _rc017_contract(docs, report)
    if contract is not None:
        _rc017_source_invariants(contract, docs, report)
        _rc017_obligations(contract, report)
        _rc017_outcomes(contract, report)
    _rc017_projection(docs, report)


def _check_rc017_negative_cases(docs: dict[str, dict], report: Report) -> None:
    contract_field = f"contracts[{VALIDATION_CONTRACT_ID}]"
    profile_field = f"projection_profiles[{CG_PROFILE_ID}]"
    cases = []

    def mutated_contract() -> tuple[dict, dict]:
        case = copy.deepcopy(docs)
        contract, _ = _unique_entry(
            case[CONTRACTS_PATH]["contracts"], "id", VALIDATION_CONTRACT_ID
        )
        return case, contract

    def mutated_profile() -> tuple[dict, dict]:
        case = copy.deepcopy(docs)
        profile, _ = _unique_entry(
            case[PROFILES_PATH]["projection_profiles"], "id", CG_PROFILE_ID
        )
        return case, profile

    for guarantee in (
        "validation_success_requires_every_applicable_required_criterion_to_be_evaluated_and_satisfied",
        "unavailable_unreadable_unexecuted_or_unresolved_required_criteria_preclude_success",
        "validation_coverage_is_explicit_and_evidence_bound",
        "unresolved_validation_semantics_remain_unresolved",
    ):
        case, contract = mutated_contract()
        contract["guarantees"].remove(guarantee)
        cases.append(
            (
                f"guarantee removed: {guarantee}",
                case,
                CONTRACTS_PATH,
                f"{contract_field}.guarantees",
            )
        )

    for prohibition in (
        "silent_skip_of_applicable_required_validation",
        "default_success_on_missing_unreadable_unexecuted_or_unresolved_required_validation",
        "partial_validation_coverage_reported_as_complete",
        "unknown_to_success_coercion",
    ):
        case, contract = mutated_contract()
        contract["forbidden"].remove(prohibition)
        cases.append(
            (
                f"prohibition removed: {prohibition}",
                case,
                CONTRACTS_PATH,
                f"{contract_field}.forbidden",
            )
        )

    case, contract = mutated_contract()
    contract["source_invariants"].remove("L9-ASSURANCE-001")
    cases.append(
        (
            "assurance basis removed from source_invariants",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.source_invariants",
        )
    )

    case, contract = mutated_contract()
    contract["outcomes"]["unresolved"] = contract["outcomes"]["satisfied"]
    cases.append(
        (
            "unresolved validation resolves as satisfied",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.outcomes",
        )
    )

    case, contract = mutated_contract()
    contract["outcomes"]["satisfied"] = (
        "evidence_supports_the_candidate_against_declared_criteria"
    )
    cases.append(
        (
            "satisfied no longer requires every applicable required criterion",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.outcomes",
        )
    )

    case, contract = mutated_contract()
    contract["outcomes"]["partially_satisfied"] = (
        "some_required_criteria_were_evaluated"
    )
    cases.append(
        (
            "new result taxonomy key added to outcomes",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.outcomes",
        )
    )

    case, contract = mutated_contract()
    contract["result_taxonomy"] = {"pass": "any_evaluated_criterion_passed"}
    cases.append(
        (
            "parallel result taxonomy field added to the contract",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.keys",
        )
    )

    case = copy.deepcopy(docs)
    case[CONTRACTS_PATH]["outcome_semantics"]["global_error_taxonomy_defined_here"] = (
        True
    )
    cases.append(
        (
            "contract catalog defines a result taxonomy",
            case,
            CONTRACTS_PATH,
            "outcome_semantics",
        )
    )

    case, contract = mutated_contract()
    contract["owner"] = CG_CONSUMER
    cases.append(
        (
            "validation law owned by the consumer",
            case,
            CONTRACTS_PATH,
            f"{contract_field}.owner",
        )
    )

    for selector in (
        "$.contracts[*].source_invariants",
        "$.contracts[*].requires",
        "$.contracts[*].guarantees",
        "$.contracts[*].forbidden",
    ):
        case, profile = mutated_profile()
        profile["sources"]["contracts"]["selectors"].remove(selector)
        cases.append(
            (
                f"projection selector removed: {selector}",
                case,
                PROFILES_PATH,
                f"{profile_field}.sources.contracts.selectors",
            )
        )

    case, profile = mutated_profile()
    del profile["sources"]["invariants"]
    cases.append(
        (
            "governing invariants projection removed",
            case,
            PROFILES_PATH,
            f"{profile_field}.sources.invariants.selectors",
        )
    )

    case, profile = mutated_profile()
    profile["sources"]["invariants"]["selectors"] = ["$.invariants[*].id"]
    cases.append(
        (
            "invariants projected as headings without their statements",
            case,
            PROFILES_PATH,
            f"{profile_field}.sources.invariants.selectors",
        )
    )

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc017(candidate, candidate_report)
        prefix = f"FAIL RC-017 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-017",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith(f"FAIL RC-017 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-017-NEG",
            f"{len(cases)} validation-completeness negative cases fail closed for their intended reason",
        )


def check_rc017(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc017(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-017",
            "validation-and-correctness contract binds satisfied to complete evaluation of every applicable "
            "required criterion, routes unavailable, unreadable, unexecuted, or unresolved required criteria to "
            "unresolved, forbids silent skip, default success, and partial coverage reported as complete, and the "
            "Cursor-Governance operating-plane projection carries operative contract semantics with the global invariants",
        )
        _check_rc017_negative_cases(docs, report)


# RC-018 Strategic Plan semantic closure. The Strategic Plan model owns exactly
# four primitives, five relation meanings, and Affected Strategic Closure. It
# reuses the Strategic Plan concept, Plan Keeper ownership, objective, Strategic
# Intent, and lifecycle supersession by reference instead of redefining them,
# and it carries no representation. Every criterion is evaluated on every run:
# an absent section is a failure, never a skip
# (l9.contract/validation-and-correctness@1).
PLAN_MODEL_PATH = "semantics/strategic_plan_model.yaml"
PLAN_MODEL_ID = "l9.strategic-plan-model/global@1"
PLAN_SOURCE_ID = "l9.source/strategic-plan-model@1"
PLAN_SCOPE = "l9_global_strategic_plan_semantics"
PLAN_MODEL_NAME = PLAN_MODEL_PATH.removeprefix("semantics/")
PLAN_CONCEPT_FIELD = "concepts.strategic_plan"
LIFECYCLE_PATH = "semantics/lifecycle.yaml"
# Model sections admitted by v3.10.0, exactly. A missing section is a coverage
# failure; an extra one is out of scope.
PLAN_MODEL_KEYS = {
    "schema",
    "artifact_id",
    "canonical",
    "authority",
    "canonical_source",
    "governed_by",
    "purpose",
    "subject",
    "global_rules",
    "primitives",
    "reused_concepts",
    "relations",
    "relation_rules",
    "reasoning_concepts",
}
PLAN_SUBJECT = {
    "concept_ref": "strategic_cognition_model.yaml#concepts.strategic_plan",
    "resolution_ref": STRATEGY_RESOLUTION_REF,
}
PLAN_PRIMITIVES = {
    "strategic_goal",
    "strategic_target",
    "strategic_hypothesis",
    "strategic_commitment",
}
PLAN_PRIMITIVE_KEYS = {"definition", "question"}
PLAN_MEANING_RELATIONS = {"advances", "enables", "depends_on", "conflicts_with"}
PLAN_SUPERSEDES = {"semantics_ref": "lifecycle.yaml#lifecycle_relations.supersedes"}
PLAN_RELATIONS = PLAN_MEANING_RELATIONS | {"supersedes"}
PLAN_RELATION_RULES = {
    "relations_do_not_transfer_ownership_or_authority",
    "material_causal_enables_claims_remain_attributable_to_a_strategic_hypothesis",
}
PLAN_GLOBAL_RULES = {
    "strategic_plan_represents_strategy_without_absorbing_external_truth_ownership",
    "strategic_hypothesis_is_plan_owned_belief_not_authoritative_truth",
    "reality_change_may_require_reconsideration_but_never_directly_modifies_or_invalidates_strategic_plan",
    "reasoning_workspace_content_is_not_strategic_plan_content_without_authorized_decision",
    "planning_horizon_does_not_create_primitive_types",
    "compound_causal_claims_are_expressible_by_one_strategic_hypothesis",
    "outcome_of_one_primitive_does_not_establish_correctness_of_another",
}
PLAN_REUSED_CONCEPTS = {
    "strategy": "strategic_cognition_model.yaml#concepts.strategy",
    "objective": "vocabulary.yaml#terms.objective",
    "strategic_intent": "strategic_cognition_model.yaml#concepts.strategic_intent",
}
PLAN_CLOSURE = "affected_strategic_closure"
# v3.19.0 (ADR-018) binds the closure to its derived representation schema
# while keeping the closure algorithm undefined here; RC-026 pins the values.
PLAN_CLOSURE_KEYS = {
    "definition",
    "purpose",
    "may_not",
    "representation_schema_ref",
    "authority_class",
    "authoritative",
    "representation_does_not_define_closure_algorithm",
}
PLAN_CLOSURE_MAY_NOT = {
    "decide_strategy",
    "modify_strategic_plan",
    "invalidate_strategic_plan",
    "mark_dependent_strategy_stale_automatically",
}
PLAN_TERMS = (*sorted(PLAN_PRIMITIVES), PLAN_CLOSURE)
# Representation the model leaves to a later campaign. None of these keys may
# appear at any depth of the ledger.
PLAN_REPRESENTATION_KEYS = {
    "fields",
    "properties",
    "required",
    "schema_ref",
    "identifier",
    "id_format",
    "confidence",
    "probability",
    "horizon",
    "duration",
    "date",
    "endpoints",
    "endpoint_types",
    "source_types",
    "target_types",
}


def _mapping(value: object) -> dict:
    """``value`` when it is a mapping, else an empty one.

    A malformed nested block must surface as a located failure on the fields
    its consumer requires, never as an AttributeError that aborts validation.
    """
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    """``value`` when it is a list, else an empty one (see ``_mapping``)."""
    return value if isinstance(value, list) else []


def _resolve_ref(docs: dict[str, dict], ref: str) -> object:
    """Resolve ``<ledger>.yaml#a.b.c`` against parsed ledgers; None if absent."""
    name, _, anchor = ref.partition("#")
    node: object = docs.get(f"semantics/{name}")
    for part in anchor.split(".") if anchor else []:
        node = node.get(part) if isinstance(node, dict) else None
    return node


def _rc018_ledger(docs: dict[str, dict], report: Report) -> dict:
    holders = [
        path for path, doc in docs.items() if doc.get("artifact_id") == PLAN_MODEL_ID
    ]
    if holders != [PLAN_MODEL_PATH]:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "artifact_id",
            holders,
            f"{PLAN_MODEL_ID} must be declared exactly once, by {PLAN_MODEL_PATH}",
        )
    model = docs.get(PLAN_MODEL_PATH) or {}
    authority = _mapping(model.get("authority"))
    if model.get("canonical") is not True:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "canonical",
            model.get("canonical"),
            "Strategic Plan ledger must be canonical",
        )
    if authority.get("owner") != STRATEGY_OWNER:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            AUTHORITY_OWNER_FIELD,
            authority.get("owner"),
            f"Strategic Plan semantics are owned by {STRATEGY_OWNER}",
        )
    if authority.get("scope") != PLAN_SCOPE:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "authority.scope",
            authority.get("scope"),
            f"must be {PLAN_SCOPE!r}",
        )
    if authority.get("authority_class") != "canonical":
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "authority.authority_class",
            authority.get("authority_class"),
            "must be canonical",
        )
    if set(model) != PLAN_MODEL_KEYS:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "keys",
            {
                "missing": sorted(PLAN_MODEL_KEYS - set(model)),
                "extra": sorted(set(model) - PLAN_MODEL_KEYS),
            },
            "model must declare exactly the admitted Strategic Plan sections",
        )
    return model


def _rc018_registration(docs: dict[str, dict], report: Report) -> None:
    registry_path = "semantics/canonical_sources.yaml"
    manifest_path = "semantics/generic_compiler_manifest.yaml"
    sources = _list(_mapping(docs.get(registry_path)).get("sources"))
    registered = [
        s for s in sources if isinstance(s, dict) and s.get("path") == PLAN_MODEL_PATH
    ]
    expected = {
        "id": PLAN_SOURCE_ID,
        "canonical": True,
        "projection_allowed": True,
        "derivation_allowed": False,
    }
    if len(registered) != 1 or any(
        registered[0].get(key) != value for key, value in expected.items()
    ):
        report.fail(
            "RC-018",
            registry_path,
            "sources",
            registered,
            f"ledger must be registered exactly once as {expected}",
        )
    requires = _mapping(_mapping(docs.get(manifest_path)).get("requires"))
    classes = [
        cls
        for cls, names in requires.items()
        if isinstance(names, list) and PLAN_MODEL_NAME in names
    ]
    if classes != ["semantic_catalogs"]:
        report.fail(
            "RC-018",
            manifest_path,
            "requires",
            classes,
            "ledger must be classified exactly once, as a semantic catalog",
        )


def _string_list(value: object) -> list[str] | None:
    """Return ``value`` when it is a list of strings, else None (malformed)."""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return None


def _rc018_governance(model: dict, docs: dict[str, dict], report: Report) -> None:
    governed = _mapping(model.get("governed_by"))
    invariant_ids = {
        i.get("id")
        for i in _list(_mapping(docs.get(INVARIANTS_PATH)).get("invariants"))
        if isinstance(i, dict)
    }
    cited = _string_list(governed.get("invariants"))
    if (
        cited is None
        or STRATEGY_INVARIANT_ID not in cited
        or not set(cited) <= invariant_ids
    ):
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "governed_by.invariants",
            governed.get("invariants"),
            f"must cite {STRATEGY_INVARIANT_ID} and only existing invariants",
        )
    contract_ids = {
        c.get("id")
        for c in _list(_mapping(docs.get(CONTRACTS_PATH)).get("contracts"))
        if isinstance(c, dict)
    }
    contracts = _string_list(governed.get("contracts"))
    if not contracts or not set(contracts) <= contract_ids:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "governed_by.contracts",
            governed.get("contracts"),
            "must cite existing contracts only",
        )


def _rc018_subject(model: dict, docs: dict[str, dict], report: Report) -> None:
    if model.get("subject") != PLAN_SUBJECT:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "subject",
            model.get("subject"),
            f"Strategic Plan content must anchor to the existing concept and authority resolution {PLAN_SUBJECT}",
        )
    plan = _resolve_ref(docs, PLAN_SUBJECT["concept_ref"])
    plan = plan if isinstance(plan, dict) else {}
    if (
        plan.get("owner_role") != PLAN_KEEPER
        or plan.get("content_defined_here") is not False
        or plan.get("structure_defined_here") is not False
    ):
        report.fail(
            "RC-018",
            STRATEGY_MODEL_PATH,
            PLAN_CONCEPT_FIELD,
            plan,
            "Strategic Plan stays owned by the Plan Keeper and its content and structure stay undefined there",
        )
    resolution = _resolve_ref(docs, PLAN_SUBJECT["resolution_ref"])
    resolution = resolution if isinstance(resolution, dict) else {}
    if resolution.get("strategic_plan_owner") != PLAN_KEEPER:
        report.fail(
            "RC-018",
            STRATEGY_AUTHORITY_PATH,
            "strategic_cognition_authority.strategic_plan_owner",
            resolution.get("strategic_plan_owner"),
            "Strategic Plan ownership must resolve to the Plan Keeper",
        )


def _rc018_rule_set(
    rules: object, admitted: set[str], field: str, report: Report
) -> None:
    rules = rules if isinstance(rules, dict) else {}
    if set(rules) != admitted or any(value is not True for value in rules.values()):
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            field,
            rules,
            f"must declare exactly the admitted rules, each true: {sorted(admitted)}",
        )


def _rc018_primitives(model: dict, report: Report) -> None:
    primitives = model.get("primitives")
    primitives = primitives if isinstance(primitives, dict) else {}
    if set(primitives) != PLAN_PRIMITIVES:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "primitives",
            sorted(primitives),
            f"exactly four Plan-owned primitives are admitted: {sorted(PLAN_PRIMITIVES)}",
        )
    for name in sorted(PLAN_PRIMITIVES & set(primitives)):
        entry = primitives[name]
        if (
            not isinstance(entry, dict)
            or set(entry) != PLAN_PRIMITIVE_KEYS
            or not all(isinstance(v, str) and v.strip() for v in entry.values())
        ):
            report.fail(
                "RC-018",
                PLAN_MODEL_PATH,
                f"primitives.{name}",
                entry,
                "primitive declares exactly a definition and a characteristic question",
            )


def _rc018_reused_concepts(model: dict, docs: dict[str, dict], report: Report) -> None:
    reused = model.get("reused_concepts")
    reused = reused if isinstance(reused, dict) else {}
    if set(reused) != set(PLAN_REUSED_CONCEPTS):
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "reused_concepts",
            sorted(reused),
            f"exactly {sorted(PLAN_REUSED_CONCEPTS)} are reused, and none is owned here",
        )
    for name, ref in sorted(PLAN_REUSED_CONCEPTS.items()):
        if reused.get(name) != {"concept_ref": ref, "owned_here": False}:
            report.fail(
                "RC-018",
                PLAN_MODEL_PATH,
                f"reused_concepts.{name}",
                reused.get(name),
                f"must reference {ref} with owned_here false",
            )
    objective = _resolve_ref(docs, PLAN_REUSED_CONCEPTS["objective"])
    objective = objective if isinstance(objective, dict) else {}
    if (
        objective.get("semantic_class") != "optimization"
        or objective.get("detailed_model") == PLAN_MODEL_NAME
    ):
        report.fail(
            "RC-018",
            VOCABULARY_PATH,
            "terms.objective",
            objective,
            "objective remains the existing optimization criterion and is not redefined by the Strategic Plan",
        )
    intent = _resolve_ref(docs, PLAN_REUSED_CONCEPTS["strategic_intent"])
    if not isinstance(intent, dict) or intent.get("owned_here") is not False:
        report.fail(
            "RC-018",
            STRATEGY_MODEL_PATH,
            "concepts.strategic_intent",
            intent,
            "Strategic Intent remains upstream of the Strategic Plan",
        )


def _rc018_relations(model: dict, docs: dict[str, dict], report: Report) -> None:
    relations = model.get("relations")
    relations = relations if isinstance(relations, dict) else {}
    if set(relations) != PLAN_RELATIONS:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "relations",
            sorted(relations),
            f"exactly five strategic relations are admitted: {sorted(PLAN_RELATIONS)}",
        )
    for name in sorted(PLAN_MEANING_RELATIONS & set(relations)):
        entry = relations[name]
        meaning = entry.get("meaning") if isinstance(entry, dict) else None
        if set(entry or {}) != {"meaning"} or not (
            isinstance(meaning, str) and meaning.strip()
        ):
            report.fail(
                "RC-018",
                PLAN_MODEL_PATH,
                f"relations.{name}",
                entry,
                "relation declares its admitted meaning only; endpoint typing is not admitted",
            )
    if "supersedes" in relations and relations["supersedes"] != PLAN_SUPERSEDES:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "relations.supersedes",
            relations["supersedes"],
            f"supersedes reuses lifecycle supersession: {PLAN_SUPERSEDES}",
        )
    lifecycle_supersedes = _resolve_ref(docs, PLAN_SUPERSEDES["semantics_ref"])
    if not isinstance(lifecycle_supersedes, dict) or not lifecycle_supersedes.get(
        "semantics"
    ):
        report.fail(
            "RC-018",
            LIFECYCLE_PATH,
            "lifecycle_relations.supersedes",
            lifecycle_supersedes,
            "reused supersession semantics must exist",
        )
    _rc018_rule_set(
        model.get("relation_rules"), PLAN_RELATION_RULES, "relation_rules", report
    )


def _rc018_closure(model: dict, report: Report) -> None:
    concepts = model.get("reasoning_concepts")
    concepts = concepts if isinstance(concepts, dict) else {}
    if set(concepts) != {PLAN_CLOSURE}:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "reasoning_concepts",
            sorted(concepts),
            f"{PLAN_CLOSURE} is the single admitted strategic reasoning concept",
        )
    closure = concepts.get(PLAN_CLOSURE)
    closure = closure if isinstance(closure, dict) else {}
    field = f"reasoning_concepts.{PLAN_CLOSURE}"
    if set(closure) != PLAN_CLOSURE_KEYS or not all(
        isinstance(closure.get(key), str) and closure[key].strip()
        for key in ("definition", "purpose")
    ):
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            field,
            closure,
            "closure declares exactly a definition, a purpose, and its prohibitions",
        )
    may_not = _string_list(closure.get("may_not"))
    if (
        may_not is None
        or len(may_not) != len(set(may_not))
        or set(may_not) != PLAN_CLOSURE_MAY_NOT
    ):
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            f"{field}.may_not",
            closure.get("may_not"),
            f"closure identifies reconsideration and may not {sorted(PLAN_CLOSURE_MAY_NOT)}",
        )


def _key_paths(node: object, trail: str = ""):
    """Yield ``(dotted_path, key)`` for every mapping key at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{trail}.{key}" if trail else str(key)
            yield path, str(key)
            yield from _key_paths(value, path)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _key_paths(item, f"{trail}[{index}]")


def _rc018_representation(model: dict, report: Report) -> None:
    found = [path for path, key in _key_paths(model) if key in PLAN_REPRESENTATION_KEYS]
    if found:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "representation_keys",
            found,
            "Strategic Plan representation is not admitted by the semantic model",
        )


def _rc018_terms(docs: dict[str, dict], report: Report) -> None:
    terms = _mapping(_mapping(docs.get(VOCABULARY_PATH)).get("terms"))
    for term in PLAN_TERMS:
        if _mapping(terms.get(term)).get("detailed_model") != PLAN_MODEL_NAME:
            report.fail(
                "RC-018",
                VOCABULARY_PATH,
                f"terms.{term}",
                terms.get(term),
                "Strategic Plan term must exist and defer to the Strategic Plan model",
            )


def _evaluate_rc018(docs: dict[str, dict], report: Report) -> None:
    model = _rc018_ledger(docs, report)
    _rc018_registration(docs, report)
    _rc018_governance(model, docs, report)
    _rc018_subject(model, docs, report)
    _rc018_rule_set(
        model.get("global_rules"), PLAN_GLOBAL_RULES, "global_rules", report
    )
    _rc018_primitives(model, report)
    _rc018_reused_concepts(model, docs, report)
    _rc018_relations(model, docs, report)
    _rc018_closure(model, report)
    _rc018_representation(model, report)
    _rc018_terms(docs, report)


def _check_rc018_negative_cases(docs: dict[str, dict], report: Report) -> None:
    model = PLAN_MODEL_PATH
    closure = f"reasoning_concepts.{PLAN_CLOSURE}"
    cases = []

    def mutated() -> tuple[dict, dict]:
        case = copy.deepcopy(docs)
        return case, case[model]

    case, ledger = mutated()
    ledger["primitives"]["strategic_milestone"] = {"definition": "x", "question": "y"}
    cases.append(("fifth Plan-owned primitive", case, model, "primitives"))

    case, ledger = mutated()
    ledger["primitives"]["strategic_objective"] = {"definition": "x", "question": "y"}
    cases.append(
        ("strategic_objective duplicates objective", case, model, "primitives")
    )

    case, ledger = mutated()
    ledger["reused_concepts"]["capability"] = {
        "concept_ref": "capabilities.yaml#capabilities",
        "owned_here": True,
    }
    cases.append(("Strategic Plan absorbs Capability", case, model, "reused_concepts"))

    case, ledger = mutated()
    ledger["reused_concepts"]["objective"]["owned_here"] = True
    cases.append(
        ("objective redefined as Plan-owned", case, model, "reused_concepts.objective")
    )

    case, ledger = mutated()
    ledger["relations"]["blocks"] = {"meaning": "x"}
    cases.append(("sixth strategic relation", case, model, "relations"))

    case, ledger = mutated()
    ledger["relations"]["supersedes"] = {"meaning": "x"}
    cases.append(("supersedes redefined locally", case, model, "relations.supersedes"))

    case, ledger = mutated()
    ledger["relations"]["enables"]["endpoint_types"] = {"source": ["strategic_target"]}
    cases.append(("relation endpoint type matrix", case, model, "relations.enables"))

    case, ledger = mutated()
    del ledger["relation_rules"][
        "material_causal_enables_claims_remain_attributable_to_a_strategic_hypothesis"
    ]
    cases.append(
        ("causal enables detached from hypothesis", case, model, "relation_rules")
    )

    case, ledger = mutated()
    ledger["relation_rules"]["relations_do_not_transfer_ownership_or_authority"] = False
    cases.append(("relations transfer ownership", case, model, "relation_rules"))

    case, ledger = mutated()
    ledger["global_rules"][
        "reality_change_may_require_reconsideration_but_never_directly_modifies_or_invalidates_strategic_plan"
    ] = False
    cases.append(
        ("reality directly modifies the Strategic Plan", case, model, "global_rules")
    )

    case, ledger = mutated()
    ledger["reasoning_concepts"][PLAN_CLOSURE]["may_not"].remove(
        "modify_strategic_plan"
    )
    cases.append(
        ("closure may modify the Strategic Plan", case, model, f"{closure}.may_not")
    )

    case, ledger = mutated()
    ledger["primitives"]["strategic_hypothesis"]["confidence"] = 0.8
    cases.append(
        ("confidence representation admitted", case, model, "representation_keys")
    )

    case, ledger = mutated()
    ledger["authority"]["owner"] = "graphiti"
    cases.append(
        (
            "Strategic Plan semantics owned by a store",
            case,
            model,
            AUTHORITY_OWNER_FIELD,
        )
    )

    case, ledger = mutated()
    ledger["subject"]["concept_ref"] = "strategic_plan_model.yaml#primitives"
    cases.append(
        (
            "Strategic Plan re-anchored away from Strategic Cognition",
            case,
            model,
            "subject",
        )
    )

    case, ledger = mutated()
    ledger["reasoning_concepts"][PLAN_CLOSURE]["may_not"].append({"x": 1})
    cases.append(
        (
            "malformed closure prohibition fails closed without crashing",
            case,
            model,
            f"{closure}.may_not",
        )
    )

    case, ledger = mutated()
    ledger["authority"] = ["x"]
    cases.append(
        (
            "non-mapping authority fails closed without crashing",
            case,
            model,
            AUTHORITY_OWNER_FIELD,
        )
    )

    case, ledger = mutated()
    ledger["governed_by"] = "x"
    cases.append(
        (
            "non-mapping governed_by fails closed without crashing",
            case,
            model,
            "governed_by.invariants",
        )
    )

    case, ledger = mutated()
    del ledger["relations"]
    cases.append(("relations section absent is not skipped", case, model, "relations"))

    case = copy.deepcopy(docs)
    case[STRATEGY_MODEL_PATH]["concepts"]["strategic_plan"]["owner_role"] = (
        METACOGNITIVE_REASONER
    )
    cases.append(
        (
            "Reasoner becomes Strategic Plan owner",
            case,
            STRATEGY_MODEL_PATH,
            PLAN_CONCEPT_FIELD,
        )
    )

    case = copy.deepcopy(docs)
    case[STRATEGY_MODEL_PATH]["concepts"]["strategic_plan"]["content_defined_here"] = (
        True
    )
    cases.append(
        (
            "Strategic Cognition absorbs Plan content",
            case,
            STRATEGY_MODEL_PATH,
            PLAN_CONCEPT_FIELD,
        )
    )

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc018(candidate, candidate_report)
        prefix = f"FAIL RC-018 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-018",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith(f"FAIL RC-018 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-018-NEG",
            f"{len(cases)} Strategic Plan negative cases fail closed for their intended reason",
        )


def check_rc018(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc018(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-018",
            "Strategic Plan ledger declares exactly four Plan-owned primitives, five strategic relations with "
            "supersession reused from lifecycle, and Affected Strategic Closure; it anchors to the existing "
            "Strategic Plan concept and Plan Keeper authority, reuses objective and Strategic Intent without "
            "owning them, and carries no representation",
        )
        _check_rc018_negative_cases(docs, report)


# RC-019 Cursor-Governance identity projection closure. One consumer profile,
# l9.projection/cursor-governance-identity@1, must project the canonical
# ActorIdentity and SurfaceIdentity entries and their typed aliases from the
# two canonical registries so the downstream deterministic projector can
# resolve local actor_ref / surface_ref coordinates. The check governs this
# exact profile coordinate only: it does not define an "identity" profile
# family by name and does not cap how many Cursor-Governance profiles exist
# (GAR-F-161001). It adds no actor, surface, alias, or identity dimension.
CG_IDENTITY_PROFILE_ID = "l9.projection/cursor-governance-identity@1"
CG_IDENTITY_OUTPUT_SCHEMA = "l9.projection.cursor-governance-identity/v1"
# Both registries keep their typed historical aliases under the same key.
ALIASES_SELECTOR = "$.aliases"
ACTOR_REGISTRY_ARTIFACT_ID = "l9.actor-registry/global@1"
SURFACE_REGISTRY_ARTIFACT_ID = "l9.surface-registry/global@1"
# source name -> (canonical ledger path, artifact_id, required selectors)
CG_IDENTITY_SOURCES = {
    "actor_registry": (
        ACTOR_REGISTRY_PATH,
        ACTOR_REGISTRY_ARTIFACT_ID,
        ("$.actors", ALIASES_SELECTOR),
    ),
    "surface_registry": (
        SURFACE_REGISTRY_PATH,
        SURFACE_REGISTRY_ARTIFACT_ID,
        ("$.surfaces", ALIASES_SELECTOR),
    ),
}
# The projection carries identity only. These boundaries stay downstream or
# are owned by other ledgers, and the profile must say so.
CG_IDENTITY_FORBIDDEN = {
    "identity_ownership_transfer",
    "credential_token_or_signing_key_semantics",
    "role_permission_or_grant_semantics",
    "actor_to_surface_assignment",
    "adapter_provider_or_governance_profile_selection",
    "runtime_marker_or_runtime_evidence_interpretation",
    "execution_authority",
}
SIMPLE_SELECTOR = re.compile(r"^\$\.([A-Za-z_]\w*)(\.[A-Za-z_]\w*|\[\*\])*$")
CG_IDENTITY_LABEL = f"projection_profiles[{CG_IDENTITY_PROFILE_ID}]"


def _rc019_selector_root(selector: str) -> str | None:
    """Top-level key a plain field / wildcard selector reads, or None when the
    selector is not in the plain subset this check can resolve statically."""
    match = SIMPLE_SELECTOR.match(selector)
    return match.group(1) if match else None


def _rc019_fail(field: str, value: object, message: str, report: Report) -> None:
    report.fail("RC-019", PROFILES_PATH, field, value, message)


def _rc019_profile_shape(profile: dict, report: Report) -> None:
    label = CG_IDENTITY_LABEL
    if profile.get("class") != "consumer":
        _rc019_fail(
            f"{label}.class",
            profile.get("class"),
            "identity projection must be a consumer profile",
            report,
        )
    if profile.get("consumer") != CG_CONSUMER:
        _rc019_fail(
            f"{label}.consumer",
            profile.get("consumer"),
            f"identity projection consumer must be exactly {CG_CONSUMER!r}",
            report,
        )
    output_schema = (profile.get("output") or {}).get("schema")
    if output_schema != CG_IDENTITY_OUTPUT_SCHEMA:
        _rc019_fail(
            f"{label}.output.schema",
            output_schema,
            f"output schema must be exactly {CG_IDENTITY_OUTPUT_SCHEMA!r}; it is the downstream consumer contract",
            report,
        )
    missing_forbidden = sorted(
        CG_IDENTITY_FORBIDDEN - set(profile.get("forbidden") or [])
    )
    if missing_forbidden:
        _rc019_fail(
            f"{label}.forbidden",
            missing_forbidden,
            "identity projection must declare the ownership boundaries it does not carry",
            report,
        )


def _rc019_source_resolves(
    name: str, catalog: dict, docs: dict[str, dict], report: Report
) -> dict | None:
    """The canonical ledger a profile source names, or None after failing closed
    when source_classes points anywhere but the canonical registry."""
    ledger_path, artifact_id, _required = CG_IDENTITY_SOURCES[name]
    declared = ((catalog.get("source_classes") or {}).get(name) or {}).get(
        "canonical_artifact"
    )
    ledger = docs.get(ledger_path) or {}
    if (
        declared != ledger_path.removeprefix("semantics/")
        or ledger.get("artifact_id") != artifact_id
        or ledger.get("canonical") is not True
    ):
        _rc019_fail(
            f"source_classes.{name}.canonical_artifact",
            declared,
            f"source {name} must resolve to the canonical ledger {ledger_path} ({artifact_id})",
            report,
        )
        return None
    return ledger


def _rc019_source_selectors(
    name: str, block: object, ledger: dict, report: Report
) -> None:
    ledger_path, _artifact_id, required = CG_IDENTITY_SOURCES[name]
    field = f"{CG_IDENTITY_LABEL}.sources.{name}.selectors"
    selectors = block.get("selectors") if isinstance(block, dict) else None
    if not isinstance(selectors, list) or not selectors:
        _rc019_fail(
            field, selectors, "source must own a non-empty selectors list", report
        )
        return
    selector_set = set(map(str, selectors))
    missing = sorted(set(required) - selector_set)
    if missing:
        _rc019_fail(
            field,
            missing,
            f"identity projection must carry the canonical {name} entries and typed aliases",
            report,
        )
    for selector in sorted(selector_set):
        root = _rc019_selector_root(selector)
        if root is None or root not in ledger:
            _rc019_fail(
                field,
                selector,
                f"selector does not resolve to a top-level section of {ledger_path}",
                report,
            )


def _rc019_sources(
    profile: dict, catalog: dict, docs: dict[str, dict], report: Report
) -> None:
    sources = profile.get("sources")
    if not isinstance(sources, dict):
        _rc019_fail(
            f"{CG_IDENTITY_LABEL}.sources",
            sources,
            "profile sources must be a source-local selector mapping",
            report,
        )
        return
    if set(sources) != set(CG_IDENTITY_SOURCES):
        _rc019_fail(
            f"{CG_IDENTITY_LABEL}.sources",
            sorted(map(str, sources)),
            f"identity projection sources must be exactly {sorted(CG_IDENTITY_SOURCES)}; "
            "no other ledger may be substituted for or added beside the canonical registries",
            report,
        )
    for name in CG_IDENTITY_SOURCES:
        if name not in sources:
            continue
        ledger = _rc019_source_resolves(name, catalog, docs, report)
        if ledger is not None:
            _rc019_source_selectors(name, sources.get(name), ledger, report)


def _evaluate_rc019(docs: dict[str, dict], report: Report) -> None:
    catalog = docs.get(PROFILES_PATH) or {}
    profiles = catalog.get("projection_profiles")
    profile, count = _unique_entry(profiles, "id", CG_IDENTITY_PROFILE_ID)
    if count != 1 or profile is None:
        _rc019_fail(
            "projection_profiles",
            CG_IDENTITY_PROFILE_ID,
            f"Cursor-Governance identity projection profile must exist exactly once (found {count})",
            report,
        )
        return
    _rc019_profile_shape(profile, report)
    _rc019_sources(profile, catalog, docs, report)


def _check_rc019_negative_cases(docs: dict[str, dict], report: Report) -> None:
    field = f"projection_profiles[{CG_IDENTITY_PROFILE_ID}]"
    cases = []

    def mutated() -> tuple[dict, list, dict]:
        case = copy.deepcopy(docs)
        profiles = case[PROFILES_PATH]["projection_profiles"]
        profile, _ = _unique_entry(profiles, "id", CG_IDENTITY_PROFILE_ID)
        return case, profiles, profile

    case, profiles, profile = mutated()
    profiles.remove(profile)
    cases.append(("target profile missing", case, "projection_profiles"))
    case, profiles, profile = mutated()
    profiles.append(copy.deepcopy(profile))
    cases.append(("target profile duplicated", case, "projection_profiles"))
    case, _, profile = mutated()
    profile["consumer"] = VALIDATION_CONTRACT_OWNER
    cases.append(("wrong consumer", case, f"{field}.consumer"))
    case, _, profile = mutated()
    profile["class"] = "governance"
    cases.append(("wrong profile class", case, f"{field}.class"))
    case, _, profile = mutated()
    del profile["sources"]["actor_registry"]
    cases.append(("actor_registry source missing", case, f"{field}.sources"))
    case, _, profile = mutated()
    del profile["sources"]["surface_registry"]
    cases.append(("surface_registry source missing", case, f"{field}.sources"))
    case, _, profile = mutated()
    profile["sources"]["identity_model"] = profile["sources"].pop("actor_registry")
    cases.append(
        ("identity_model substituted for actor_registry", case, f"{field}.sources")
    )
    case, _, profile = mutated()
    profile["sources"]["actor_registry"]["selectors"].remove(ALIASES_SELECTOR)
    cases.append(
        (
            "incomplete actor projection (aliases dropped)",
            case,
            f"{field}.sources.actor_registry.selectors",
        )
    )
    case, _, profile = mutated()
    profile["sources"]["surface_registry"]["selectors"].remove("$.surfaces")
    cases.append(
        (
            "incomplete surface projection (entries dropped)",
            case,
            f"{field}.sources.surface_registry.selectors",
        )
    )
    case, _, profile = mutated()
    profile["sources"]["actor_registry"]["selectors"].append("$.credentials")
    cases.append(
        (
            "selector names a section the actor registry does not have",
            case,
            f"{field}.sources.actor_registry.selectors",
        )
    )
    case, _, profile = mutated()
    profile["output"]["schema"] = "l9.projection.cursor-governance-identity/v2"
    cases.append(("wrong output schema", case, f"{field}.output.schema"))
    case, _, profile = mutated()
    profile["forbidden"].remove("identity_ownership_transfer")
    cases.append(("ownership boundary dropped", case, f"{field}.forbidden"))
    for label, candidate, field_name in cases:
        candidate_report = Report()
        _evaluate_rc019(candidate, candidate_report)
        prefix = f"FAIL RC-019 {PROFILES_PATH} {field_name}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-019",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {PROFILES_PATH} {field_name}",
            )
    if not any(
        f.startswith(f"FAIL RC-019 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-019-NEG",
            f"{len(cases)} identity projection negative cases fail closed for their intended reason",
        )


def check_rc019(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc019(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-019",
            f"{CG_IDENTITY_PROFILE_ID} exists once as a Cursor-Governance consumer profile, projects the "
            "canonical actor and surface entries and typed aliases from the two canonical registries only, "
            f"emits {CG_IDENTITY_OUTPUT_SCHEMA}, and declares its ownership boundaries",
        )
        _check_rc019_negative_cases(docs, report)


# RC-020 Graphiti/Zep technology admission closure (v3.12.0). Two concrete
# provider technologies are admitted to the canonical technology catalog so a
# product may name them in a provider binding. The check governs these exact
# coordinates only: it defines no graph-provider or memory-provider family,
# imposes no rule on any other technology, and does not cap how many
# technologies exist. Registration states technology facts; it grants no
# semantic ownership and authorizes no use.
#
# The admission must reuse what the catalog already admitted. The class and
# role sets are therefore pinned to the v3.11.0 catalog rather than read from
# the live file, so a class or role introduced alongside the admission (or
# beside a decoy registration that uses it) cannot pass as pre-existing. The
# required registration fields are pinned the same way, so relaxing the
# catalog's own grammar cannot excuse a missing field.
TECHNOLOGIES_PATH = "semantics/technology_capabilities.yaml"
RC020_TECHNOLOGY_IDS = ("graphiti-mcp", "zep")
RC020_REQUIRED_FIELDS = ("id", "class", "provides", "target_roles")
# The semantic facts this admission registered, from the provider realization
# l9-graphiti-memory consumes: the class, the minimum provider capability facts,
# and the minimum target role. A successor may add facts or roles; it may not
# substitute or drop these, or the closure would pass on a gutted admission.
RC020_ADMITTED_CLASS = "datastore"
RC020_ADMITTED_PROVIDES = frozenset(
    {"graph_episode_storage", "graph_search", "episode_deletion_by_locator"}
)
RC020_ADMITTED_TARGET_ROLES = frozenset({"persistence_provider"})
RC020_OWNERSHIP_REASON = "does not transfer semantic ownership"
RC020_ADMITTED_CLASSES = frozenset(
    {"language", "framework", "datastore", "transport", "target"}
)
RC020_ADMITTED_ROLES = frozenset(
    {
        "implementation_language",
        "conformance_target",
        "persistence_provider",
        "constellation_transport_binding",
        "late_stage_renderer",
        "schema_target",
        "repository_metadata_target",
        "repository_operator_facade_target",
    }
)


def _rc020_fail(field: str, value: object, message: str, report: Report) -> None:
    report.fail("RC-020", TECHNOLOGIES_PATH, field, value, message)


def _rc020_terms(value: object) -> list[str] | None:
    """A non-empty list of distinct non-empty strings, else None."""
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(term, str) and term.strip() for term in value):
        return None
    return value if len(set(value)) == len(value) else None


def _rc020_grammar(catalog: dict, report: Report) -> set[str] | None:
    """Registration fields the catalog declares, or None after failing closed
    when its grammar is malformed or no longer requires the pinned fields."""
    requirements = catalog.get("registration_requirements")
    required = optional = None
    if isinstance(requirements, dict):
        required = _string_list(requirements.get("required"))
        optional = _string_list(requirements.get("optional"))
    if required is None or optional is None:
        _rc020_fail(
            "registration_requirements",
            requirements,
            "registration grammar must declare required and optional field lists",
            report,
        )
        return None
    missing = sorted(set(RC020_REQUIRED_FIELDS) - set(required))
    if missing:
        _rc020_fail(
            "registration_requirements.required",
            missing,
            "registration grammar no longer requires the pinned registration fields",
            report,
        )
        return None
    return set(required) | set(optional)


def _rc020_class(label: str, cls: object, classes: dict, report: Report) -> None:
    if not isinstance(cls, str) or cls not in classes:
        _rc020_fail(
            f"{label}.class",
            cls,
            "class is not an admitted capability class of the technology catalog",
            report,
        )
    elif cls not in RC020_ADMITTED_CLASSES:
        _rc020_fail(
            f"{label}.class",
            cls,
            "class was not admitted before this registration; the admission must "
            "not introduce a technology class",
            report,
        )
    if cls != RC020_ADMITTED_CLASS:
        _rc020_fail(
            f"{label}.class",
            cls,
            f"admitted class must remain {RC020_ADMITTED_CLASS!r}",
            report,
        )


def _rc020_roles(label: str, value: object, report: Report) -> None:
    roles = _rc020_terms(value)
    if roles is None:
        _rc020_fail(
            f"{label}.target_roles",
            value,
            "target roles must be a non-empty list of distinct explicit roles",
            report,
        )
        return
    for role in roles:
        if role not in RC020_ADMITTED_ROLES:
            _rc020_fail(
                f"{label}.target_roles",
                role,
                "role was not admitted before this registration; the admission "
                "must reuse an existing target role",
                report,
            )
    dropped = sorted(RC020_ADMITTED_TARGET_ROLES - set(roles))
    if dropped:
        _rc020_fail(
            f"{label}.target_roles",
            dropped,
            "admitted target role was dropped; a provider binding relies on it",
            report,
        )


def _rc020_optional(label: str, entry: dict, registered: set, report: Report) -> None:
    for field in ("constraints", "compatible_with", "incompatible_with"):
        if field in entry and _rc020_terms(entry.get(field)) is None:
            _rc020_fail(
                f"{label}.{field}",
                entry.get(field),
                "optional registration field must be a non-empty list of distinct terms",
                report,
            )
    for field in ("compatible_with", "incompatible_with"):
        for ref in _rc020_terms(entry.get(field)) or []:
            if ref not in registered:
                _rc020_fail(
                    f"{label}.{field}",
                    ref,
                    "referenced technology is not registered",
                    report,
                )


def _rc020_ownership(label: str, ownership: object, report: Report) -> None:
    if not (
        isinstance(ownership, dict)
        and set(ownership) == {"implied"}
        and ownership["implied"] is False
    ):
        _rc020_fail(
            f"{label}.semantic_ownership",
            ownership,
            "provider technology must declare exactly {'implied': False}; "
            f"registration {RC020_OWNERSHIP_REASON}",
            report,
        )


def _rc020_registration(
    entry: dict,
    allowed: set[str],
    classes: dict,
    registered: set,
    report: Report,
) -> None:
    label = f"technologies[{entry.get('id')}]"
    for field in RC020_REQUIRED_FIELDS:
        if field not in entry:
            _rc020_fail(
                f"{label}.{field}",
                None,
                "required registration field missing",
                report,
            )
    for field in sorted(set(map(str, entry)) - allowed):
        _rc020_fail(
            f"{label}.{field}",
            entry.get(field),
            "field is not a registration field of the technology catalog",
            report,
        )
    _rc020_class(label, entry.get("class"), classes, report)
    provides = _rc020_terms(entry.get("provides"))
    if provides is None:
        _rc020_fail(
            f"{label}.provides",
            entry.get("provides"),
            "capability claims must be a non-empty list of distinct explicit terms",
            report,
        )
    else:
        dropped = sorted(RC020_ADMITTED_PROVIDES - set(provides))
        if dropped:
            _rc020_fail(
                f"{label}.provides",
                dropped,
                "admitted capability facts were dropped; a provider binding "
                "relies on them",
                report,
            )
    _rc020_roles(label, entry.get("target_roles"), report)
    _rc020_optional(label, entry, registered, report)
    _rc020_ownership(label, entry.get("semantic_ownership"), report)


def _evaluate_rc020(docs: dict[str, dict], report: Report) -> None:
    catalog = docs.get(TECHNOLOGIES_PATH)
    if not isinstance(catalog, dict):
        _rc020_fail("file", "-", "technology catalog missing or unparsable", report)
        return
    technologies = catalog.get("technologies")
    if not isinstance(technologies, list):
        _rc020_fail(
            "technologies",
            type(technologies).__name__,
            "technology list missing",
            report,
        )
        return
    classes = catalog.get("capability_classes")
    if not isinstance(classes, dict):
        _rc020_fail(
            "capability_classes",
            classes,
            "capability classes must be a mapping",
            report,
        )
        return
    allowed = _rc020_grammar(catalog, report)
    if allowed is None:
        return
    registered = {
        entry.get("id")
        for entry in technologies
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    for technology_id in RC020_TECHNOLOGY_IDS:
        entry, count = _unique_entry(technologies, "id", technology_id)
        if count != 1 or entry is None:
            _rc020_fail(
                "technologies",
                technology_id,
                f"technology must be registered exactly once (found {count})",
                report,
            )
            continue
        _rc020_registration(entry, allowed, classes, registered, report)


def _check_rc020_negative_cases(docs: dict[str, dict], report: Report) -> None:
    graphiti, zep = RC020_TECHNOLOGY_IDS
    cases = []

    def mutated(technology_id: str) -> tuple[dict, dict, list, dict]:
        case = copy.deepcopy(docs)
        catalog = case[TECHNOLOGIES_PATH]
        technologies = catalog["technologies"]
        entry, _ = _unique_entry(technologies, "id", technology_id)
        return case, catalog, technologies, entry

    def field(technology_id: str, name: str) -> str:
        return f"technologies[{technology_id}].{name}"

    case, _, technologies, entry = mutated(graphiti)
    technologies.remove(entry)
    cases.append(("Graphiti registration missing", case, "technologies", "found 0"))
    case, _, technologies, entry = mutated(zep)
    technologies.remove(entry)
    cases.append(("Zep registration missing", case, "technologies", "found 0"))
    case, _, technologies, entry = mutated(zep)
    technologies.append(copy.deepcopy(entry))
    cases.append(("duplicate exact technology id", case, "technologies", "found 2"))
    case, _, _, entry = mutated(graphiti)
    del entry["class"]
    cases.append(("class missing", case, field(graphiti, "class"), "field missing"))
    case, catalog, technologies, entry = mutated(zep)
    entry["class"] = "memory_provider"
    other, _ = _unique_entry(technologies, "id", "mongodb")
    other["class"] = "memory_provider"
    cases.append(
        (
            "non-admitted class (also held by another registration)",
            case,
            field(zep, "class"),
            "not an admitted capability class",
        )
    )
    case, catalog, technologies, entry = mutated(zep)
    catalog["capability_classes"]["memory_store"] = {
        "definition": "introduced alongside the admission"
    }
    technologies.append(
        {
            "id": "decoy",
            "class": "memory_store",
            "provides": ["decoy_fact"],
            "target_roles": ["persistence_provider"],
        }
    )
    entry["class"] = "memory_store"
    cases.append(
        (
            "class introduced alongside the admission behind a decoy",
            case,
            field(zep, "class"),
            "must not introduce a technology class",
        )
    )
    case, _, _, entry = mutated(zep)
    entry["class"] = ["datastore"]
    cases.append(
        (
            "class not a scalar",
            case,
            field(zep, "class"),
            "not an admitted capability class",
        )
    )
    case, _, _, entry = mutated(graphiti)
    entry["provides"] = []
    cases.append(
        (
            "empty provides",
            case,
            field(graphiti, "provides"),
            "capability claims must be",
        )
    )
    case, _, _, entry = mutated(zep)
    entry["provides"] = ["unrelated_fact"]
    cases.append(
        (
            "admitted capability facts replaced",
            case,
            field(zep, "provides"),
            "admitted capability facts were dropped",
        )
    )
    case, _, _, entry = mutated(graphiti)
    entry["provides"].remove("graph_search")
    cases.append(
        (
            "one admitted capability fact removed",
            case,
            field(graphiti, "provides"),
            "admitted capability facts were dropped",
        )
    )
    case, _, _, entry = mutated(graphiti)
    entry["class"] = "language"
    cases.append(
        (
            "another already-admitted class substituted",
            case,
            field(graphiti, "class"),
            "admitted class must remain",
        )
    )
    case, _, _, entry = mutated(zep)
    entry["target_roles"] = ["implementation_language"]
    cases.append(
        (
            "another already-admitted target role substituted",
            case,
            field(zep, "target_roles"),
            "admitted target role was dropped",
        )
    )
    case, _, _, entry = mutated(zep)
    del entry["target_roles"]
    cases.append(
        (
            "target_roles missing",
            case,
            field(zep, "target_roles"),
            "field missing",
        )
    )
    case, _, technologies, entry = mutated(graphiti)
    technologies.append(
        {
            "id": "decoy",
            "class": "datastore",
            "provides": ["decoy_fact"],
            "target_roles": ["memory_role"],
        }
    )
    entry["target_roles"] = ["memory_role"]
    cases.append(
        (
            "target role introduced behind a decoy",
            case,
            field(graphiti, "target_roles"),
            "must reuse an existing target role",
        )
    )
    case, _, _, entry = mutated(graphiti)
    entry["semantic_ownership"]["implied"] = True
    cases.append(
        (
            "semantic ownership implied",
            case,
            field(graphiti, "semantic_ownership"),
            RC020_OWNERSHIP_REASON,
        )
    )
    case, _, _, entry = mutated(zep)
    entry["semantic_ownership"]["implied"] = 0
    cases.append(
        (
            "semantic ownership falsy but not false",
            case,
            field(zep, "semantic_ownership"),
            RC020_OWNERSHIP_REASON,
        )
    )
    case, _, _, entry = mutated(zep)
    del entry["semantic_ownership"]
    cases.append(
        (
            "semantic ownership undeclared",
            case,
            field(zep, "semantic_ownership"),
            RC020_OWNERSHIP_REASON,
        )
    )
    case, _, _, entry = mutated(zep)
    entry["owns"] = ["memory_admission"]
    cases.append(
        (
            "ownership claim outside the registration grammar",
            case,
            field(zep, "owns"),
            "not a registration field",
        )
    )
    case, catalog, _, entry = mutated(zep)
    requirements = catalog["registration_requirements"]
    requirements["optional"].extend(requirements["required"])
    requirements["required"] = ["id"]
    del entry["provides"]
    cases.append(
        (
            "registration grammar relaxed to excuse a missing field",
            case,
            "registration_requirements.required",
            "no longer requires the pinned registration fields",
        )
    )
    case, catalog, _, _ = mutated(zep)
    catalog["capability_classes"] = ["datastore"]
    cases.append(
        (
            "capability classes not a mapping",
            case,
            "capability_classes",
            "must be a mapping",
        )
    )
    for label, candidate, field_name, reason in cases:
        candidate_report = Report()
        _evaluate_rc020(candidate, candidate_report)
        prefix = f"FAIL RC-020 {TECHNOLOGIES_PATH} {field_name}="
        if not any(
            f.startswith(prefix) and reason in f for f in candidate_report.failures
        ):
            report.fail(
                "RC-020",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {TECHNOLOGIES_PATH} "
                f"{field_name} for its intended reason ({reason!r})",
            )
    if not any(
        f.startswith(f"FAIL RC-020 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-020-NEG",
            f"{len(cases)} Graphiti/Zep technology admission negative cases fail "
            "closed at their intended field with their intended reason",
        )


def check_rc020(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc020(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-020",
            f"{' and '.join(RC020_TECHNOLOGY_IDS)} are each registered exactly once "
            "with every pinned registration field, a class and target roles "
            "admitted before this registration, the admitted class datastore, "
            "capability claims and target roles that retain the admitted facts, "
            "and "
            "semantic_ownership exactly {implied: false}",
        )
        _check_rc020_negative_cases(docs, report)


# RC-021 Product admission authority identity. ProductTopology.admission
# requires `authority_ref: semantic_ref`, and product topologies name
# l9.authority/product-admission there, so that coordinate must resolve to
# exactly one canonical declaration in the authority model. The check governs
# this coordinate only. It pins the whole declaration, the admission and
# escalation law it inherits, the vocabulary term it names, and the admission
# receipt owner to their admitted bytes rather than reading them from the live
# file. Redefining product admission (dropping a requirement or rule, moving
# the decision off the target-class authority, adding an admitter, letting
# admission imply publication, runtime admission, availability, or invocation)
# therefore cannot pass as resolution. Any other occurrence of the coordinate
# in a ledger must be an exact reference under a `*_ref` / `*_refs` field;
# anything else is a shadow declaration.
RC021_AUTHORITY_ID = "l9.authority/product-admission"
RC021_AUTHORITY_PATH = "semantics/authority_model.yaml"
RC021_DECLARATION_KEY = "product_admission_authority"
RC021_RECEIPTS_PATH = "semantics/receipt_catalog.yaml"
# ProductTopology.admission.authority_ref is validated at ProductTopology intake,
# so that stage must receive the declaration and the law it inherits.
RC021_TOPOLOGY_STAGE_PROFILE = "l9.projection/stage-product-topology@1"
RC021_TOPOLOGY_STAGE_SELECTORS = (
    "$.product_admission_authority",
    "$.admission_rules",
    "$.escalation_rules",
)
RC021_DECISION_AUTHORITY = "applicable_target_class_authority"
RC021_OPERATION = "product_admission"
RC021_GLOBAL_REQUIREMENTS = [
    "exact_subject_identity",
    "exact_subject_revision_or_digest_when_revisioned",
    "target_semantic_or_authority_class",
    "target_class_authority",
    "explicit_decision_record",
    "explicit_compatibility_contract_when_reusing_prior_decision_after_material_change",
]
RC021_NOT_IMPLIED = (
    "publication",
    "runtime_admission",
    "runtime_availability",
    "capability_invocation_authorization",
    "implementation_conformance",
    "consumer_compatibility",
)
RC021_DECLARATION = {
    "id": RC021_AUTHORITY_ID,
    "meaning": "Semantic authority role under which an exact ProductTopology or exact "
    "product release may be admitted by the applicable target-class authority.",
    "global_semantics_owner": "Quantum-L9/.github",
    "decision_authority": RC021_DECISION_AUTHORITY,
    "operation": RC021_OPERATION,
    "subjects": ["exact_product_topology", "exact_product_release"],
    "inherits_global_requirements": RC021_GLOBAL_REQUIREMENTS,
    "inherits_rules": ["admission_rules", "escalation_rules"],
    "candidate_generation_is_not_admission": True,
    "self_admission_without_target_class_authority_forbidden": True,
    "implies": {consequence: False for consequence in RC021_NOT_IMPLIED},
    "rules": [
        "product_admission_binds_exact_subject",
        "compilation_or_validation_is_not_product_admission",
        "candidate_does_not_self_admit_because_validation_passes",
        "global_semantics_owner_does_not_admit_products",
        "product_release_admission_is_not_runtime_admission",
    ],
}
# The inherited law, pinned to the v3.12.0 authority model.
RC021_INHERITED = {
    "admission_rules": {
        "global_requirements": RC021_GLOBAL_REQUIREMENTS,
        "candidate_generation_is_not_admission": True,
        "self_admission_without_target_class_authority_forbidden": True,
        "changed_material_subject_requires_new_decision_unless_compatibility_preserves_it": True,
    },
    "escalation_rules": {
        "authority_missing": "block",
        "semantic_conflict": "block",
        "unknown": "remain_unknown",
        "changed_candidate_after_decision": "require_new_decision",
    },
}
RC021_TERM = {
    "semantic_class": "governance_operation",
    "subtype_of": "admission",
    "rules": [
        "admission_binds_exact_subject",
        "admission_does_not_imply_runtime_availability",
        "admission_does_not_authorize_capability_invocation",
    ],
}


def _rc021_fail(
    path: str, field: str, value: object, message: str, report: Report
) -> None:
    report.fail("RC-021", path, field, value, message)


def _rc021_occurrences(
    node: object, trail: str, parent_key: str, found: list[str]
) -> None:
    """Every place a ledger names the coordinate other than an exact reference."""
    if isinstance(node, dict):
        for key, child in node.items():
            key_text = str(key)
            child_trail = f"{trail}.{key_text}" if trail else key_text
            if RC021_AUTHORITY_ID in key_text:
                found.append(child_trail)
            _rc021_occurrences(child, child_trail, key_text, found)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _rc021_occurrences(child, f"{trail}[{index}]", parent_key, found)
    elif isinstance(node, str) and RC021_AUTHORITY_ID in node:
        is_ref = parent_key.endswith(("_ref", "_refs"))
        if not (is_ref and node == RC021_AUTHORITY_ID):
            found.append(trail)


def _rc021_pinned(
    path: str, field: str, actual: object, expected: dict, report: Report
) -> None:
    """Fail at each key whose value differs from the pinned mapping."""
    if not isinstance(actual, dict):
        _rc021_fail(path, field, actual, "must be the pinned mapping", report)
        return
    for key in sorted(set(expected) | set(actual), key=str):
        if key not in expected:
            _rc021_fail(
                path, f"{field}.{key}", actual[key], "key is not admitted here", report
            )
        elif isinstance(expected[key], dict):
            _rc021_pinned(
                path, f"{field}.{key}", actual.get(key), expected[key], report
            )
        elif actual.get(key) != expected[key] or (
            isinstance(expected[key], bool) and actual.get(key) is not expected[key]
        ):
            _rc021_fail(
                path,
                f"{field}.{key}",
                actual.get(key),
                f"must be exactly {expected[key]!r}",
                report,
            )


def _rc021_projection(docs: dict[str, dict], report: Report) -> None:
    """ProductTopology intake must receive the declaration and the law it inherits."""
    profiles = _mapping(docs.get(PROFILES_PATH)).get("projection_profiles")
    profile, count = _unique_entry(profiles, "id", RC021_TOPOLOGY_STAGE_PROFILE)
    field = f"projection_profiles[{RC021_TOPOLOGY_STAGE_PROFILE}]"
    if count != 1 or profile is None:
        _rc021_fail(
            PROFILES_PATH,
            field,
            count,
            "ProductTopology stage profile must exist exactly once",
            report,
        )
        return
    selectors = _mapping(_mapping(profile.get("sources")).get("authority_model")).get(
        "selectors"
    )
    present = (
        {s for s in selectors if isinstance(s, str)}
        if isinstance(selectors, list)
        else set()
    )
    for selector in RC021_TOPOLOGY_STAGE_SELECTORS:
        if selector not in present:
            _rc021_fail(
                PROFILES_PATH,
                f"{field}.sources.authority_model.selectors",
                selector,
                "ProductTopology intake must project the product admission authority "
                "and every section it inherits",
                report,
            )


def _evaluate_rc021(docs: dict[str, dict], report: Report) -> None:
    path = RC021_AUTHORITY_PATH
    field = RC021_DECLARATION_KEY
    expected = f"{path}#{field}.id"
    found: list[str] = []
    for doc_path in sorted(docs):
        trails: list[str] = []
        _rc021_occurrences(docs[doc_path], "", "", trails)
        found.extend(f"{doc_path}#{trail}" for trail in trails)
    if found != [expected]:
        _rc021_fail(
            path,
            field,
            RC021_AUTHORITY_ID,
            f"authority coordinate must be declared exactly once, at {expected}, and "
            f"otherwise only referenced exactly under *_ref fields (found {found})",
            report,
        )
        return
    model = docs[path]
    _rc021_pinned(path, field, model.get(field), RC021_DECLARATION, report)
    for name, law in RC021_INHERITED.items():
        _rc021_pinned(path, name, model.get(name), law, report)
    _rc021_projection(docs, report)
    term = _mapping(_mapping(docs.get(VOCABULARY_PATH)).get("terms")).get(
        RC021_OPERATION
    )
    term_view = {key: _mapping(term).get(key) for key in RC021_TERM}
    _rc021_pinned(
        VOCABULARY_PATH, f"terms.{RC021_OPERATION}", term_view, RC021_TERM, report
    )
    receipt_owner = _mapping(
        _mapping(_mapping(docs.get(RC021_RECEIPTS_PATH)).get("receipts")).get(
            "admission"
        )
    ).get("semantic_owner")
    if receipt_owner != RC021_DECISION_AUTHORITY:
        _rc021_fail(
            RC021_RECEIPTS_PATH,
            "receipts.admission.semantic_owner",
            receipt_owner,
            f"admission receipts must stay owned by {RC021_DECISION_AUTHORITY}",
            report,
        )


def _check_rc021_negative_cases(docs: dict[str, dict], report: Report) -> None:
    path = RC021_AUTHORITY_PATH
    field = RC021_DECLARATION_KEY
    vocab_field = f"terms.{RC021_OPERATION}"
    cases = []

    def mutated() -> tuple[dict, dict]:
        case = copy.deepcopy(docs)
        return case, case[path][field]

    def add(label: str, case: dict, case_path: str, field_name: str) -> None:
        cases.append((label, case, case_path, field_name))

    case, _ = mutated()
    del case[path][field]
    add("coordinate missing", case, path, field)
    case, decl = mutated()
    case[RC021_RECEIPTS_PATH]["shadow_authority"] = {"id": decl["id"]}
    add("coordinate declared twice", case, path, field)
    case, _ = mutated()
    case[RC021_RECEIPTS_PATH]["shadow"] = {"authority_id": RC021_AUTHORITY_ID}
    add("shadow under another id key", case, path, field)
    case, _ = mutated()
    case[path]["shadow"] = {"id": f"{RC021_AUTHORITY_ID}@1"}
    add("shadow with version suffix", case, path, field)
    case, _ = mutated()
    case[path][RC021_AUTHORITY_ID] = {"decision_authority": "producer"}
    add("shadow as mapping key", case, path, field)
    case, _ = mutated()
    case[path]["shadow"] = {"authority_ref": f"{RC021_AUTHORITY_ID} "}
    add("inexact reference", case, path, field)
    for key, value in (
        ("decision_authority", "Quantum-L9/.github"),
        ("decision_authority", "l9-semantic-compiler"),
        ("decision_authority", ["applicable_target_class_authority"]),
        ("operation", "runtime_admission"),
        ("operation", ["product_admission"]),
        ("subjects", ["exact_product_topology", "deployed_node"]),
        ("subjects", [{"a": 1}, "exact_product_release"]),
        ("subjects", ["exact_product_topology", "exact_product_topology"]),
        ("inherits_global_requirements", RC021_GLOBAL_REQUIREMENTS[:-2]),
        ("inherits_rules", []),
        ("inherits_rules", ["promotion_rules"]),
        ("self_admission_without_target_class_authority_forbidden", False),
        ("candidate_generation_is_not_admission", 1),
        ("global_semantics_owner", "l9-semantic-compiler"),
        ("meaning", "Performed by the semantic compiler; implies publication."),
        ("rules", ["candidate_self_admits_when_validation_passes"]),
        ("alternate_decision_authorities", ["l9-semantic-compiler"]),
        ("may_self_admit", True),
        ("implies", []),
    ):
        case, decl = mutated()
        decl[key] = value
        add(f"{key}={value!r}", case, path, f"{field}.{key}")
    for key in ("rules", "inherits_rules", "global_semantics_owner"):
        case, decl = mutated()
        del decl[key]
        add(f"{key} removed", case, path, f"{field}.{key}")
    for consequence in RC021_NOT_IMPLIED:
        case, decl = mutated()
        decl["implies"][consequence] = True
        add(f"implies {consequence}", case, path, f"{field}.implies.{consequence}")
    case, decl = mutated()
    del decl["implies"]["publication"]
    add(
        "publication non-implication omitted",
        case,
        path,
        f"{field}.implies.publication",
    )
    case, decl = mutated()
    decl["implies"]["deployment"] = True
    add("extra implied consequence", case, path, f"{field}.implies.deployment")
    case, _ = mutated()
    case[path]["admission_rules"] = copy.deepcopy(case[path]["admission_rules"])
    case[path]["admission_rules"][
        "self_admission_without_target_class_authority_forbidden"
    ] = False
    add(
        "inherited self-admission ban lifted",
        case,
        path,
        "admission_rules.self_admission_without_target_class_authority_forbidden",
    )
    case, _ = mutated()
    case[path]["admission_rules"]["global_requirements"].pop()
    add(
        "inherited requirement dropped",
        case,
        path,
        "admission_rules.global_requirements",
    )
    case, _ = mutated()
    case[path]["escalation_rules"]["unknown"] = "default_pass"
    add("unknown defaults to pass", case, path, "escalation_rules.unknown")
    case, _ = mutated()
    case[path]["escalation_rules"]["authority_missing"] = "allow"
    add("missing authority allowed", case, path, "escalation_rules.authority_missing")
    case, _ = mutated()
    del case[path]["escalation_rules"]
    add("escalation law removed", case, path, "escalation_rules")
    case, _ = mutated()
    case[VOCABULARY_PATH]["terms"][RC021_OPERATION]["rules"] = [
        "admission_implies_runtime_availability"
    ]
    add("vocabulary rules rewritten", case, VOCABULARY_PATH, f"{vocab_field}.rules")
    case, _ = mutated()
    case[VOCABULARY_PATH]["terms"][RC021_OPERATION]["subtype_of"] = "promotion"
    add("vocabulary subtype moved", case, VOCABULARY_PATH, f"{vocab_field}.subtype_of")
    stage_field = f"projection_profiles[{RC021_TOPOLOGY_STAGE_PROFILE}]"
    for selector in RC021_TOPOLOGY_STAGE_SELECTORS:
        case, _ = mutated()
        stage, _ = _unique_entry(
            case[PROFILES_PATH]["projection_profiles"],
            "id",
            RC021_TOPOLOGY_STAGE_PROFILE,
        )
        stage["sources"]["authority_model"]["selectors"].remove(selector)
        add(
            f"topology stage does not project {selector}",
            case,
            PROFILES_PATH,
            f"{stage_field}.sources.authority_model.selectors",
        )
    case, _ = mutated()
    stage, _ = _unique_entry(
        case[PROFILES_PATH]["projection_profiles"],
        "id",
        RC021_TOPOLOGY_STAGE_PROFILE,
    )
    stage["sources"]["authority_model"]["selectors"] = [
        {"a": 1},
        *RC021_TOPOLOGY_STAGE_SELECTORS[1:],
    ]
    add(
        "topology stage selector is not a string",
        case,
        PROFILES_PATH,
        f"{stage_field}.sources.authority_model.selectors",
    )
    case, _ = mutated()
    stages = case[PROFILES_PATH]["projection_profiles"]
    stage, _ = _unique_entry(stages, "id", RC021_TOPOLOGY_STAGE_PROFILE)
    stages.remove(stage)
    add("topology stage profile missing", case, PROFILES_PATH, stage_field)
    case, _ = mutated()
    case[RC021_RECEIPTS_PATH]["receipts"]["admission"]["semantic_owner"] = "producer"
    add(
        "admission receipt owner moved",
        case,
        RC021_RECEIPTS_PATH,
        "receipts.admission.semantic_owner",
    )
    for label, candidate, case_path, field_name in cases:
        candidate_report = Report()
        try:
            _evaluate_rc021(candidate, candidate_report)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            # A malformed shape must be a located failure, never a crash.
            report.fail(
                "RC-021",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case raised {type(error).__name__} instead of failing closed",
            )
            continue
        prefix = f"FAIL RC-021 {case_path} {field_name}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-021",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {case_path} {field_name}",
            )
    if not any(
        f.startswith(f"FAIL RC-021 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-021-NEG",
            f"{len(cases)} product admission authority negative cases fail closed at "
            "their intended field",
        )


def check_rc021(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc021(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-021",
            f"{RC021_AUTHORITY_ID} resolves exactly once to {RC021_AUTHORITY_PATH}#"
            f"{RC021_DECLARATION_KEY} and is otherwise only referenced exactly; the "
            f"declaration, the admission and escalation law it inherits, the {RC021_OPERATION} "
            f"term, and the admission receipt owner match their pinned bytes: decided by "
            f"{RC021_DECISION_AUTHORITY}, no self-admission, and no implied publication, runtime "
            "admission, runtime availability, capability invocation, implementation "
            f"conformance, or consumer compatibility; {RC021_TOPOLOGY_STAGE_PROFILE} "
            "projects the declaration and the law it inherits",
        )
        _check_rc021_negative_cases(docs, report)


# RC-022 Admission contract / authority-model requirement closure. The
# authority model owns the universal admission prerequisites
# (`admission_rules.global_requirements`); `l9.authority/product-admission`
# inherits that list by anchor and RC-021 pins it. The contract catalog
# operationalizes the same prerequisites as the base `requires` of
# l9.contract/admission-and-promotion@1. v3.13.0 shipped with that consumer
# drifted from its authority: one requirement carried a stale spelling, and a
# conditional cross-domain evidence obligation sat in the unconditional base
# list. RC-022 proves the contract's base `requires` equals the live
# authority-model sequence exactly, and that the conditional recurrence law
# the base list no longer carries still lives where the contract states it
# (guarantees, prohibitions, and the globalization invariant), so removing
# the witness from `requires` cannot become a weakening. It reads the
# authority list live rather than re-pinning it: pinning is RC-021's job,
# and a second pin would be duplicated doctrine. It governs this one
# contract only (L9-VALIDATION-001).
RC022_CONTRACT_ID = "l9.contract/admission-and-promotion@1"
RC022_STALE_SPELLING = "explicit_compatibility_contract_when_reusing_a_prior_decision_after_material_change"
RC022_CONDITIONAL_WITNESS = "independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence"
# The recurrence / globalization law that keeps cross-domain evidence a
# conditional obligation rather than a base prerequisite (L9-GLOBALIZATION-001).
RC022_RECURRENCE_GUARANTEES = (
    "recurrence_or_validation_creates_no_implicit_promotion",
    "cross_domain_recurrence_claims_are_evidence_bound_when_used_to_support_higher_scope_admission",
    # The witness obligation relocated verbatim out of the unconditional base
    # list: it must stay here (conditional) and must never re-enter requires.
    RC022_CONDITIONAL_WITNESS,
)
RC022_RECURRENCE_FORBIDDEN = (
    "treating_recurrence_as_global_admission",
    "treating_hypothetical_reuse_repeated_assertion_or_single_domain_repetition_as_cross_domain_recurrence",
)
RC022_GLOBALIZATION_INVARIANT = "L9-GLOBALIZATION-001"


def _rc022_fail(
    path: str, field: str, value: object, message: str, report: Report
) -> None:
    report.fail("RC-022", path, field, value, message)


def _rc022_string_list(
    path: str, field: str, value: object, report: Report
) -> list[str] | None:
    """``value`` as a list of strings, else a located failure and ``None``."""
    if not isinstance(value, list) or not value:
        _rc022_fail(path, field, value, "must be a non-empty list", report)
        return None
    if not all(isinstance(item, str) for item in value):
        _rc022_fail(path, field, value, "every entry must be a string", report)
        return None
    return value


def _evaluate_rc022(docs: dict[str, dict], report: Report) -> None:
    authority_field = "admission_rules.global_requirements"
    requirements = _rc022_string_list(
        RC021_AUTHORITY_PATH,
        authority_field,
        _mapping(_mapping(docs.get(RC021_AUTHORITY_PATH)).get("admission_rules")).get(
            "global_requirements"
        ),
        report,
    )
    if requirements is None:
        return
    if len(set(requirements)) != len(requirements):
        _rc022_fail(
            RC021_AUTHORITY_PATH,
            authority_field,
            requirements,
            "global admission requirements must be unique",
            report,
        )
        return
    contract, count = _unique_entry(
        _mapping(docs.get(CONTRACTS_PATH)).get("contracts"), "id", RC022_CONTRACT_ID
    )
    field = f"contracts[{RC022_CONTRACT_ID}]"
    if count != 1 or contract is None:
        _rc022_fail(
            CONTRACTS_PATH,
            field,
            count,
            "admission-and-promotion contract must exist exactly once",
            report,
        )
        return
    requires = _rc022_string_list(
        CONTRACTS_PATH, f"{field}.requires", contract.get("requires"), report
    )
    if requires is not None:
        for requirement in requirements:
            if requirement not in requires:
                hint = (
                    f" (the contract carries the stale spelling {RC022_STALE_SPELLING!r})"
                    if RC022_STALE_SPELLING in requires
                    and requirement != RC022_STALE_SPELLING
                    and requirement.startswith("explicit_compatibility_contract")
                    else ""
                )
                _rc022_fail(
                    CONTRACTS_PATH,
                    f"{field}.requires",
                    requirement,
                    "authority-model global admission requirement is absent from the "
                    f"contract's base requires{hint}",
                    report,
                )
        for requirement in requires:
            if requirement in requirements:
                continue
            if requirement == RC022_CONDITIONAL_WITNESS:
                reason = (
                    "cross-domain witness evidence is a conditional obligation when "
                    "recurrence is actually asserted (L9-GLOBALIZATION-001), not an "
                    "unconditional base admission requirement"
                )
            elif requirement == RC022_STALE_SPELLING:
                reason = (
                    "stale spelling; the canonical requirement identifier is the one "
                    f"in {RC021_AUTHORITY_PATH}#{authority_field}"
                )
            else:
                reason = (
                    "requirement is not in the authority model's global admission "
                    "requirements; a base admission requirement is admitted there first"
                )
            _rc022_fail(
                CONTRACTS_PATH, f"{field}.requires", requirement, reason, report
            )
        if set(requires) == set(requirements) and requires != requirements:
            _rc022_fail(
                CONTRACTS_PATH,
                f"{field}.requires",
                requires,
                f"must equal {RC021_AUTHORITY_PATH}#{authority_field} as an exact "
                "sequence (same order, no duplicates)",
                report,
            )
    guarantees = _rc022_string_list(
        CONTRACTS_PATH, f"{field}.guarantees", contract.get("guarantees"), report
    )
    for guarantee in RC022_RECURRENCE_GUARANTEES:
        if guarantees is not None and guarantee not in guarantees:
            _rc022_fail(
                CONTRACTS_PATH,
                f"{field}.guarantees",
                guarantee,
                "recurrence guarantee must stay declared; it is where the conditional "
                "cross-domain evidence obligation lives",
                report,
            )
    forbidden = _rc022_string_list(
        CONTRACTS_PATH, f"{field}.forbidden", contract.get("forbidden"), report
    )
    for prohibition in RC022_RECURRENCE_FORBIDDEN:
        if forbidden is not None and prohibition not in forbidden:
            _rc022_fail(
                CONTRACTS_PATH,
                f"{field}.forbidden",
                prohibition,
                "recurrence prohibition must stay declared (L9-GLOBALIZATION-001)",
                report,
            )
    invariants = _rc022_string_list(
        CONTRACTS_PATH,
        f"{field}.source_invariants",
        contract.get("source_invariants"),
        report,
    )
    if invariants is not None and RC022_GLOBALIZATION_INVARIANT not in invariants:
        _rc022_fail(
            CONTRACTS_PATH,
            f"{field}.source_invariants",
            RC022_GLOBALIZATION_INVARIANT,
            "the contract must keep citing the globalization invariant",
            report,
        )


def _check_rc022_negative_cases(docs: dict[str, dict], report: Report) -> None:
    field = f"contracts[{RC022_CONTRACT_ID}]"
    authority_field = "admission_rules.global_requirements"
    cases = []

    def mutated() -> tuple[dict, dict]:
        case = copy.deepcopy(docs)
        contract, _ = _unique_entry(
            case[CONTRACTS_PATH]["contracts"], "id", RC022_CONTRACT_ID
        )
        return case, contract

    def add(label: str, case: dict, case_path: str, field_name: str) -> None:
        cases.append((label, case, case_path, field_name))

    case, _ = mutated()
    del case[CONTRACTS_PATH]
    add("contracts ledger missing", case, CONTRACTS_PATH, field)
    case, contract = mutated()
    case[CONTRACTS_PATH]["contracts"].remove(contract)
    add("contract missing", case, CONTRACTS_PATH, field)
    case, contract = mutated()
    case[CONTRACTS_PATH]["contracts"].append(copy.deepcopy(contract))
    add("contract duplicated", case, CONTRACTS_PATH, field)
    case, _ = mutated()
    case[CONTRACTS_PATH]["contracts"] = {"id": RC022_CONTRACT_ID}
    add("contract catalog not a list", case, CONTRACTS_PATH, field)
    for label, value in (
        ("requires is a string", "exact_subject_identity"),
        ("requires is empty", []),
        ("requires holds a mapping", [{"id": "exact_subject_identity"}]),
        ("requires removed", None),
    ):
        case, contract = mutated()
        if value is None:
            del contract["requires"]
        else:
            contract["requires"] = value
        add(label, case, CONTRACTS_PATH, f"{field}.requires")
    case, _ = mutated()
    del case[RC021_AUTHORITY_PATH]["admission_rules"]["global_requirements"]
    add(
        "authority-model admission requirements missing",
        case,
        RC021_AUTHORITY_PATH,
        authority_field,
    )
    case, _ = mutated()
    case[RC021_AUTHORITY_PATH]["admission_rules"] = "exact_subject_identity"
    add(
        "authority-model admission rules not a mapping",
        case,
        RC021_AUTHORITY_PATH,
        authority_field,
    )
    case, _ = mutated()
    case[RC021_AUTHORITY_PATH]["admission_rules"]["global_requirements"] = [
        {"id": "exact_subject_identity"}
    ]
    add(
        "authority-model requirement not a string",
        case,
        RC021_AUTHORITY_PATH,
        authority_field,
    )
    case, _ = mutated()
    case[RC021_AUTHORITY_PATH]["admission_rules"]["global_requirements"].append(
        "exact_subject_identity"
    )
    add(
        "authority-model requirement duplicated",
        case,
        RC021_AUTHORITY_PATH,
        authority_field,
    )
    case, contract = mutated()
    contract["requires"] = contract["requires"][:-1]
    add("requirement missing", case, CONTRACTS_PATH, f"{field}.requires")
    case, contract = mutated()
    contract["requires"] = [*contract["requires"], "producer_attestation"]
    add("extra requirement", case, CONTRACTS_PATH, f"{field}.requires")
    case, contract = mutated()
    contract["requires"] = [
        "subject_identity" if r == "exact_subject_identity" else r
        for r in contract["requires"]
    ]
    add("requirement renamed", case, CONTRACTS_PATH, f"{field}.requires")
    case, contract = mutated()
    contract["requires"] = [
        RC022_STALE_SPELLING if r.startswith("explicit_compatibility_contract") else r
        for r in contract["requires"]
    ]
    add(
        "stale reusing_a_prior_decision spelling",
        case,
        CONTRACTS_PATH,
        f"{field}.requires",
    )
    case, contract = mutated()
    contract["requires"] = [*contract["requires"], RC022_CONDITIONAL_WITNESS]
    add(
        "cross-domain witness reintroduced as unconditional",
        case,
        CONTRACTS_PATH,
        f"{field}.requires",
    )
    case, contract = mutated()
    contract["requires"] = list(reversed(contract["requires"]))
    add("requirement order changed", case, CONTRACTS_PATH, f"{field}.requires")
    case, contract = mutated()
    contract["requires"] = [*contract["requires"], contract["requires"][0]]
    add("requirement duplicated", case, CONTRACTS_PATH, f"{field}.requires")
    case, _ = mutated()
    case[RC021_AUTHORITY_PATH]["admission_rules"]["global_requirements"][0] = (
        "subject_identity"
    )
    add(
        "authority-model requirement renamed under the contract",
        case,
        CONTRACTS_PATH,
        f"{field}.requires",
    )
    for guarantee in RC022_RECURRENCE_GUARANTEES:
        case, contract = mutated()
        contract["guarantees"].remove(guarantee)
        add(f"{guarantee} removed", case, CONTRACTS_PATH, f"{field}.guarantees")
    case, contract = mutated()
    contract["guarantees"] = "recurrence_or_validation_creates_no_implicit_promotion"
    add("guarantees not a list", case, CONTRACTS_PATH, f"{field}.guarantees")
    for prohibition in RC022_RECURRENCE_FORBIDDEN:
        case, contract = mutated()
        contract["forbidden"].remove(prohibition)
        add(f"{prohibition} removed", case, CONTRACTS_PATH, f"{field}.forbidden")
    case, contract = mutated()
    contract["source_invariants"].remove(RC022_GLOBALIZATION_INVARIANT)
    add(
        "globalization invariant no longer cited",
        case,
        CONTRACTS_PATH,
        f"{field}.source_invariants",
    )
    for label, candidate, case_path, field_name in cases:
        candidate_report = Report()
        try:
            _evaluate_rc022(candidate, candidate_report)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            # A malformed shape must be a located failure, never a crash.
            report.fail(
                "RC-022",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case raised {type(error).__name__} instead of failing closed",
            )
            continue
        prefix = f"FAIL RC-022 {case_path} {field_name}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-022",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {case_path} {field_name}",
            )
    if not any(
        f.startswith(f"FAIL RC-022 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-022-NEG",
            f"{len(cases)} admission contract requirement-closure negative cases fail "
            "closed at their intended field",
        )


def check_rc022(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc022(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-022",
            f"{RC022_CONTRACT_ID} exists exactly once and its base requires equals "
            f"{RC021_AUTHORITY_PATH}#admission_rules.global_requirements as an exact "
            "sequence; the stale reusing_a_prior_decision spelling and the unconditional "
            "cross-domain witness are absent; the recurrence guarantees, recurrence "
            f"prohibitions, and {RC022_GLOBALIZATION_INVARIANT} citation that keep "
            "cross-domain evidence conditional stay declared",
        )
        _check_rc022_negative_cases(docs, report)


# RC-023 Repository class / repository registry closure. Until v3.15.0 the
# repository class catalog and the repository registry were registered
# ledgers whose content was an explicit Unknown. v3.15.0 admits exactly one
# RepositoryClass (l9.repository-class/l9@1), one derived memory-namespace
# view over it, and an explicit census of repositories, every one
# assigned that class by decision. RC-023 pins that admission: the class
# identity and its memory obligation, the derived view's selector and output,
# and the exact repository ids and case-sensitive GitHub coordinates. It
# therefore fails on an extra repository, a missing repository, a renamed
# coordinate, a duplicate, a wrong class, an unrecognized lifecycle, and on
# any consumer-side membership expansion or removal. Membership is explicit:
# nothing here infers a class from a repository name, prefix, hosting
# organization, shape, ProductKind or birth profile, and a future repository
# needs a new explicit admission (and a new pin) before it is a member. The
# check governs these two ledgers only (L9-VALIDATION-001).
RC023_CLASSES_PATH = "semantics/repository_classes.yaml"
RC023_REGISTRY_PATH = "semantics/repository_registry.yaml"
RC023_CLASSES_SCHEMA = "l9.repository-classes/v1"
RC023_CLASSES_ARTIFACT_ID = "l9.repository-classes/global@1"
RC023_REGISTRY_SCHEMA = "l9.repository-registry/v1"
RC023_REGISTRY_ARTIFACT_ID = "l9.repository-registry/global@1"
RC023_CLASS_KEY = "l9"
RC023_CLASS_ID = "l9.repository-class/l9@1"
RC023_NAMESPACE = "l9"
RC023_VIEW_KEY = "l9_memory_namespace"
RC023_VIEW_ID = "l9.repository-view/memory-namespace-l9@1"
RC023_VIEW_LIFECYCLES = ["current", "superseded", "retired"]
RC023_VIEW_PRESERVE_FIELDS = ["id", "coordinate", "lifecycle", "class_ref"]
RC023_LIFECYCLES = ("current", "superseded", "retired")
RC023_PROVIDER = "github"
RC023_ORGANIZATION = "Quantum-L9"
# The admitted class declaration, pinned to its admitted bytes (the RC-021
# style). Every key under classes.l9 is law: a key that drifts, disappears, or
# appears beside these fails as a new admission decision. The projection
# obligation deliberately names no projection profile and no compiler
# receipt: whether a derived view is realized through a canonical profile or
# a declared selector contract is owned by l9.contract/projection@1
# (`declared_projection_profile_or_selector_contract`), and the admitted
# memory-namespace view is realized by a selector contract plus a
# deterministic downstream projector with a projection receipt.
RC023_CLASS_DEFINITION = (
    "A repository admitted as part of the governed L9 organization corpus. Its "
    "repository identity and organization participation are governed by Quantum-L9 "
    "organization law. Where organization-level canonical semantic authority exists, "
    "the repository consumes that authority by reference or admitted projection instead "
    "of maintaining a competing local definition.\n"
)
RC023_PROJECTION_OBLIGATION = {
    "generated_materialization_authority_class": "derived",
    "manual_edit_of_generated_projection": "forbidden",
    "source_coordinate_required": True,
    "source_digest_required": True,
    "provenance_required": True,
    "stale_projection_must_not_be_silently_consumed": True,
    "authority_expansion": "forbidden",
}
RC023_MEMORY_OBLIGATION = {
    "namespace": RC023_NAMESPACE,
    "membership": "required",
    "membership_source": "resolved_repository_class",
    "content_selection_owned_by_memory_plane": True,
    "content_authority_remains_with_source_repository": True,
    "memory_representation_authority_class": "derived",
    "consumer_may_not_independently_add_or_remove_members": True,
    "lifecycle_semantics": {
        "current": "current_source",
        "superseded": "historical_source",
        "retired": "historical_source",
    },
}
RC023_CLASS_DECLARATION = {
    "id": RC023_CLASS_ID,
    "status": "current",
    "definition": RC023_CLASS_DEFINITION,
    "organization_membership": RC023_NAMESPACE,
    "obligations": {
        "canonical_authority_consumption": {
            "when_global_canonical_authority_exists": "reference_or_admitted_projection",
            "local_competing_canonical_copy": "forbidden",
            "local_domain_semantics_within_repository_authority": "allowed",
        },
        "projection": RC023_PROJECTION_OBLIGATION,
        "memory": RC023_MEMORY_OBLIGATION,
    },
    "prohibitions": [
        "redefine_existing_global_canonical_semantics_locally",
        "treat_generated_projection_as_canonical_authority",
        "treat_memory_representation_as_source_repository_authority",
        "infer_repository_membership_from_repository_name",
        "infer_repository_membership_from_repository_prefix",
        "infer_repository_membership_from_organization_hosting",
        "infer_product_kind_from_repository_class",
        "infer_birth_profile_from_repository_class",
        "expand_authority_through_projection",
    ],
}
# The explicit census admitted by v3.15.0 and extended by v3.16.0: registry id -> case-sensitive
# GitHub repository coordinate under Quantum-L9. Thirty-two entries, every
# one lifecycle `current` and class l9.repository-class/l9@1. This is a pin,
# not a rule: a repository is listed because it was admitted, and admitting
# another one is a new semantic decision that extends this mapping.
RC023_REPOSITORIES = {
    "dot-github": ".github",
    "cursor-governance": "Cursor-Governance",
    "igorbot": "igorbot",
    "seo-bot": "SEO-Bot",
    "website-bot": "Website-Bot",
    "l9-original-repo": "L9_Original_Repo",
    "l9-assurance": "l9-assurance",
    "l9-ci-core": "l9-ci-core",
    "l9-ci-debt-intelligence": "l9-ci-debt-intelligence",
    "l9-ci-debt-lsp": "l9-ci-debt-lsp",
    "l9-ci-debt-resolver": "l9-ci-debt-resolver",
    "l9-ci-sdk": "l9-ci-sdk",
    "l9-codegen": "l9-codegen",
    "l9-cognitive-runtime": "l9-cognitive-runtime",
    "l9-conformance": "l9-conformance",
    "l9-constellation-ingest": "l9-constellation-ingest",
    "l9-constellation-topology": "l9-constellation-topology",
    "l9-dependency-template": "l9-dependency-template",
    "l9-deploy": "l9-deploy",
    "l9-devpack-compiler": "l9-devpack-compiler",
    "l9-goose": "l9-goose",
    "l9-graphiti-memory": "l9-graphiti-memory",
    "l9-harness": "l9-harness",
    "l9-meta-injector": "l9-meta-injector",
    "l9-node-chain-of-search": "l9-node-chain-of-search",
    "l9-node-template": "l9-node-template",
    "l9-observability-core": "l9-observability-core",
    "l9-ops-mcp": "L9-Ops-MCP",
    "l9-pr-repair": "l9-pr-repair",
    "l9-prompt-generator": "L9-Prompt-Generator",
    "l9-repo-template": "l9-repo-template",
    "l9-semantic-compiler-engine": "l9-semantic-compiler-engine",
    "l9-wip": "l9-wip",
}
RC023_REPOSITORY_COUNT = 33


def _rc023_fail(
    path: str, field: str, value: object, message: str, report: Report
) -> None:
    report.fail("RC-023", path, field, value, message)


def _rc023_expect(
    path: str, field: str, actual: object, expected: object, report: Report
) -> bool:
    """Fail at ``field`` unless ``actual`` equals the pinned ``expected``."""
    if actual != expected:
        _rc023_fail(path, field, actual, f"must equal {expected!r}", report)
        return False
    return True


def _rc023_pinned(
    path: str, field: str, actual: object, expected: dict, report: Report
) -> None:
    """Fail at each pinned key whose value differs; extra keys are admitted."""
    if not isinstance(actual, dict):
        _rc023_fail(path, field, actual, "must be a mapping", report)
        return
    for key, value in expected.items():
        _rc023_expect(path, f"{field}.{key}", actual.get(key), value, report)


def _rc023_exact(
    path: str, field: str, actual: object, expected: dict, report: Report
) -> None:
    """Fail at each key whose value differs from the pinned mapping, recursively.

    A key missing from ``actual`` fails at that key; a key ``expected`` does
    not admit fails at that key as well, so an obligation cannot be added or
    dropped without a new admission decision.
    """
    if not isinstance(actual, dict):
        _rc023_fail(path, field, actual, "must be a mapping", report)
        return
    for key in sorted(set(expected) | set(actual), key=str):
        if key not in expected:
            _rc023_fail(
                path,
                f"{field}.{key}",
                actual[key],
                "key is not admitted here; adding an obligation is a new admission decision",
                report,
            )
        elif isinstance(expected[key], dict):
            _rc023_exact(path, f"{field}.{key}", actual.get(key), expected[key], report)
        else:
            _rc023_expect(
                path, f"{field}.{key}", actual.get(key), expected[key], report
            )


def _evaluate_rc023_classes(docs: dict[str, dict], report: Report) -> None:
    path = RC023_CLASSES_PATH
    catalog = docs.get(path)
    if not isinstance(catalog, dict):
        _rc023_fail(path, "file", "-", "repository class catalog missing", report)
        return
    _rc023_expect(path, "schema", catalog.get("schema"), RC023_CLASSES_SCHEMA, report)
    _rc023_expect(
        path,
        "artifact_id",
        catalog.get("artifact_id"),
        RC023_CLASSES_ARTIFACT_ID,
        report,
    )
    _rc023_expect(path, "canonical", catalog.get("canonical"), True, report)
    classes = catalog.get("classes")
    if not isinstance(classes, dict):
        _rc023_fail(path, "classes", classes, "must be a mapping of classes", report)
        return
    with_id = [
        key for key, cls in classes.items() if _mapping(cls).get("id") == RC023_CLASS_ID
    ]
    if len(with_id) != 1 or RC023_CLASS_KEY not in classes:
        _rc023_fail(
            path,
            f"classes[{RC023_CLASS_ID}]",
            len(with_id),
            f"the l9 class must exist exactly once under classes.{RC023_CLASS_KEY}",
            report,
        )
        return
    if set(classes) != {RC023_CLASS_KEY}:
        _rc023_fail(
            path,
            "classes",
            sorted(str(key) for key in classes),
            f"only the admitted class key {RC023_CLASS_KEY!r} may be defined; any "
            "other class is a new admission decision",
            report,
        )
    field = f"classes.{RC023_CLASS_KEY}"
    _rc023_exact(
        path, field, classes.get(RC023_CLASS_KEY), RC023_CLASS_DECLARATION, report
    )
    admitted = _mapping(catalog.get("catalog_status")).get("admitted_classes")
    _rc023_expect(
        path, "catalog_status.admitted_classes", admitted, [RC023_CLASS_ID], report
    )
    views = catalog.get("derived_views")
    if not isinstance(views, dict):
        _rc023_fail(path, "derived_views", views, "must be a mapping of views", report)
        return
    with_view_id = [
        key for key, view in views.items() if _mapping(view).get("id") == RC023_VIEW_ID
    ]
    if len(with_view_id) != 1 or RC023_VIEW_KEY not in views:
        _rc023_fail(
            path,
            f"derived_views[{RC023_VIEW_ID}]",
            len(with_view_id),
            f"the memory-namespace view must exist exactly once under derived_views.{RC023_VIEW_KEY}",
            report,
        )
        return
    if set(views) != {RC023_VIEW_KEY}:
        _rc023_fail(
            path,
            "derived_views",
            sorted(str(key) for key in views),
            f"only the admitted view key {RC023_VIEW_KEY!r} may be defined; any "
            "other derived view is a new admission decision",
            report,
        )
    view = _mapping(views.get(RC023_VIEW_KEY))
    vfield = f"derived_views.{RC023_VIEW_KEY}"
    _rc023_expect(path, f"{vfield}.id", view.get("id"), RC023_VIEW_ID, report)
    selector = _mapping(view.get("selector"))
    _rc023_expect(
        path,
        f"{vfield}.selector.class_ref",
        selector.get("class_ref"),
        RC023_CLASS_ID,
        report,
    )
    _rc023_expect(
        path,
        f"{vfield}.selector.lifecycle_in",
        selector.get("lifecycle_in"),
        RC023_VIEW_LIFECYCLES,
        report,
    )
    _rc023_pinned(
        path,
        f"{vfield}.output",
        view.get("output"),
        {
            "namespace": RC023_NAMESPACE,
            "authority_class": "derived",
            "preserve_fields": RC023_VIEW_PRESERVE_FIELDS,
            "consumer_may_not_add_unregistered_members": True,
            "consumer_may_not_remove_required_members": True,
        },
        report,
    )


def _evaluate_rc023_registry(docs: dict[str, dict], report: Report) -> None:
    path = RC023_REGISTRY_PATH
    registry = docs.get(path)
    if not isinstance(registry, dict):
        _rc023_fail(path, "file", "-", "repository registry missing", report)
        return
    _rc023_expect(path, "schema", registry.get("schema"), RC023_REGISTRY_SCHEMA, report)
    _rc023_expect(
        path,
        "artifact_id",
        registry.get("artifact_id"),
        RC023_REGISTRY_ARTIFACT_ID,
        report,
    )
    _rc023_expect(path, "canonical", registry.get("canonical"), True, report)
    _rc023_expect(
        path,
        "class_catalog_ref",
        registry.get("class_catalog_ref"),
        RC023_CLASSES_ARTIFACT_ID,
        report,
    )
    repositories = registry.get("repositories")
    if not isinstance(repositories, list):
        _rc023_fail(
            path,
            "repositories",
            repositories,
            "must be a list of repository entries",
            report,
        )
        return
    if len(repositories) != RC023_REPOSITORY_COUNT:
        _rc023_fail(
            path,
            "repositories",
            len(repositories),
            f"exactly {RC023_REPOSITORY_COUNT} repositories are admitted",
            report,
        )
    seen_ids: dict[str, int] = {}
    seen_coordinates: dict[tuple[str, str, str], int] = {}
    for index, entry in enumerate(repositories):
        field = f"repositories[{index}]"
        if not isinstance(entry, dict):
            _rc023_fail(
                path, field, entry, "repository entry must be a mapping", report
            )
            continue
        rid = entry.get("id")
        if not isinstance(rid, str) or not rid:
            _rc023_fail(
                path, f"{field}.id", rid, "repository id must be a string", report
            )
            continue
        field = f"repositories[{rid}]"
        seen_ids[rid] = seen_ids.get(rid, 0) + 1
        coordinate = entry.get("coordinate")
        if not isinstance(coordinate, dict):
            _rc023_fail(
                path,
                f"{field}.coordinate",
                coordinate,
                "coordinate must be a mapping",
                report,
            )
        else:
            _rc023_expect(
                path,
                f"{field}.coordinate.provider",
                coordinate.get("provider"),
                RC023_PROVIDER,
                report,
            )
            _rc023_expect(
                path,
                f"{field}.coordinate.organization",
                coordinate.get("organization"),
                RC023_ORGANIZATION,
                report,
            )
            key = (
                str(coordinate.get("provider")),
                str(coordinate.get("organization")),
                str(coordinate.get("repository")),
            )
            seen_coordinates[key] = seen_coordinates.get(key, 0) + 1
            if rid in RC023_REPOSITORIES:
                _rc023_expect(
                    path,
                    f"{field}.coordinate.repository",
                    coordinate.get("repository"),
                    RC023_REPOSITORIES[rid],
                    report,
                )
        lifecycle = entry.get("lifecycle")
        if lifecycle not in RC023_LIFECYCLES:
            _rc023_fail(
                path,
                f"{field}.lifecycle",
                lifecycle,
                f"lifecycle must be one of {list(RC023_LIFECYCLES)}",
                report,
            )
        elif lifecycle != "current":
            _rc023_fail(
                path,
                f"{field}.lifecycle",
                lifecycle,
                "every admitted repository is lifecycle current in this release",
                report,
            )
        _rc023_expect(
            path, f"{field}.class_ref", entry.get("class_ref"), RC023_CLASS_ID, report
        )
    for rid, count in sorted(seen_ids.items()):
        if count > 1:
            _rc023_fail(
                path,
                f"repositories[{rid}].id",
                count,
                "repository id is registered more than once",
                report,
            )
        if rid not in RC023_REPOSITORIES:
            _rc023_fail(
                path,
                f"repositories[{rid}].id",
                rid,
                "repository is not admitted by this release; admission is an explicit "
                "semantic decision, never inferred from a name, prefix, or hosting",
                report,
            )
    for rid in sorted(set(RC023_REPOSITORIES) - set(seen_ids)):
        _rc023_fail(
            path,
            f"repositories[{rid}].id",
            None,
            "admitted repository is missing from the registry",
            report,
        )
    for key, count in sorted(seen_coordinates.items()):
        if count > 1:
            _rc023_fail(
                path,
                "repositories[].coordinate",
                "/".join(key),
                "provider coordinate is registered more than once",
                report,
            )
    expected_coordinates = {
        (RC023_PROVIDER, RC023_ORGANIZATION, repo)
        for repo in RC023_REPOSITORIES.values()
    }
    for key in sorted(expected_coordinates - set(seen_coordinates)):
        _rc023_fail(
            path,
            "repositories[].coordinate",
            "/".join(key),
            "admitted coordinate is missing from the registry",
            report,
        )


def _evaluate_rc023(docs: dict[str, dict], report: Report) -> None:
    _evaluate_rc023_classes(docs, report)
    _evaluate_rc023_registry(docs, report)


def _check_rc023_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases = []

    def mutated() -> tuple[dict, dict, dict]:
        case = copy.deepcopy(docs)
        return (
            case,
            case[RC023_CLASSES_PATH],
            case[RC023_REGISTRY_PATH],
        )

    def add(label: str, case: dict, case_path: str, field_name: str) -> None:
        cases.append((label, case, case_path, field_name))

    def entry(registry: dict, rid: str) -> dict:
        found, _ = _unique_entry(registry["repositories"], "id", rid)
        assert found is not None
        return found

    cp, rp = RC023_CLASSES_PATH, RC023_REGISTRY_PATH
    cls_field = f"classes.{RC023_CLASS_KEY}"
    view_field = f"derived_views.{RC023_VIEW_KEY}"
    # Class catalog identity.
    case, catalog, _ = mutated()
    del case[cp]
    add("class catalog missing", case, cp, "file")
    for label, key, value in (
        ("class catalog schema wrong", "schema", "l9.repository-classes/v2"),
        (
            "class catalog artifact_id wrong",
            "artifact_id",
            "l9.repository-classes/global@2",
        ),
        ("class catalog not canonical", "canonical", False),
    ):
        case, catalog, _ = mutated()
        catalog[key] = value
        add(label, case, cp, key)
    case, catalog, _ = mutated()
    catalog["classes"] = []
    add("classes not a mapping", case, cp, "classes")
    case, catalog, _ = mutated()
    del catalog["classes"][RC023_CLASS_KEY]
    add("l9 class missing", case, cp, f"classes[{RC023_CLASS_ID}]")
    case, catalog, _ = mutated()
    catalog["classes"]["l9_again"] = copy.deepcopy(catalog["classes"][RC023_CLASS_KEY])
    add("l9 class duplicated", case, cp, f"classes[{RC023_CLASS_ID}]")
    case, catalog, _ = mutated()
    catalog["classes"]["org_auxiliary"] = {
        "id": "l9.repository-class/org-auxiliary@1",
        "status": "current",
        "organization_membership": "auxiliary",
    }
    add("unadmitted class defined beside l9", case, cp, "classes")
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["status"] = "retired"
    add("l9 class not current", case, cp, f"{cls_field}.status")
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["organization_membership"] = "auxiliary"
    add("l9 class membership wrong", case, cp, f"{cls_field}.organization_membership")
    for key, value in (
        ("namespace", "main"),
        ("membership", "optional"),
        ("membership_source", "repository_name"),
        ("consumer_may_not_independently_add_or_remove_members", False),
    ):
        case, catalog, _ = mutated()
        catalog["classes"][RC023_CLASS_KEY]["obligations"]["memory"][key] = value
        add(
            f"memory obligation {key} wrong",
            case,
            cp,
            f"{cls_field}.obligations.memory.{key}",
        )
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["obligations"]["memory"] = "l9"
    add("memory obligation not a mapping", case, cp, f"{cls_field}.obligations.memory")
    for key in ("projection_profile_required", "projection_profile_digest_required"):
        case, catalog, _ = mutated()
        catalog["classes"][RC023_CLASS_KEY]["obligations"]["projection"][key] = True
        add(
            f"projection obligation reintroduces {key}",
            case,
            cp,
            f"{cls_field}.obligations.projection.{key}",
        )
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["obligations"]["projection"][
        "compiler_receipt_required"
    ] = True
    add(
        "projection obligation reintroduces compiler_receipt_required",
        case,
        cp,
        f"{cls_field}.obligations.projection.compiler_receipt_required",
    )
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["obligations"]["projection"][
        "source_digest_required"
    ] = False
    add(
        "projection obligation drops source digest",
        case,
        cp,
        f"{cls_field}.obligations.projection.source_digest_required",
    )
    case, catalog, _ = mutated()
    del catalog["classes"][RC023_CLASS_KEY]["obligations"]["projection"][
        "provenance_required"
    ]
    add(
        "projection obligation missing provenance_required",
        case,
        cp,
        f"{cls_field}.obligations.projection.provenance_required",
    )
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["obligations"]["identity_materialization"] = {
        "actor_registry_ref": "l9.actor-registry/global@1"
    }
    add(
        "unadmitted obligation reintroduced",
        case,
        cp,
        f"{cls_field}.obligations.identity_materialization",
    )
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["prohibitions"].remove(
        "infer_repository_membership_from_repository_name"
    )
    add("prohibition dropped", case, cp, f"{cls_field}.prohibitions")
    case, catalog, _ = mutated()
    catalog["classes"][RC023_CLASS_KEY]["definition"] = (
        "Any repository hosted under Quantum-L9."
    )
    add("class definition rewritten", case, cp, f"{cls_field}.definition")
    case, catalog, _ = mutated()
    catalog["catalog_status"]["admitted_classes"].append(
        "l9.repository-class/org-auxiliary@1"
    )
    add(
        "unadmitted class listed as admitted",
        case,
        cp,
        "catalog_status.admitted_classes",
    )
    # Derived memory-namespace view.
    case, catalog, _ = mutated()
    catalog["derived_views"] = "l9_memory_namespace"
    add("derived views not a mapping", case, cp, "derived_views")
    case, catalog, _ = mutated()
    del catalog["derived_views"][RC023_VIEW_KEY]
    add("memory-namespace view missing", case, cp, f"derived_views[{RC023_VIEW_ID}]")
    case, catalog, _ = mutated()
    catalog["derived_views"]["again"] = copy.deepcopy(
        catalog["derived_views"][RC023_VIEW_KEY]
    )
    add("memory-namespace view duplicated", case, cp, f"derived_views[{RC023_VIEW_ID}]")
    case, catalog, _ = mutated()
    catalog["derived_views"]["l9_everything"] = {
        "id": "l9.repository-view/everything@1",
        "selector": {"class_ref": RC023_CLASS_ID},
        "output": {"namespace": "main", "authority_class": "derived"},
    }
    add("unrelated extra derived view", case, cp, "derived_views")
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["selector"]["class_ref"] = (
        "l9.repository-class/org-auxiliary@1"
    )
    add("view selects a different class", case, cp, f"{view_field}.selector.class_ref")
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["selector"]["lifecycle_in"] = ["current"]
    add(
        "view lifecycle selector narrowed",
        case,
        cp,
        f"{view_field}.selector.lifecycle_in",
    )
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["output"]["namespace"] = "default"
    add("view namespace wrong", case, cp, f"{view_field}.output.namespace")
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["output"]["authority_class"] = "canonical"
    add(
        "view claims canonical authority",
        case,
        cp,
        f"{view_field}.output.authority_class",
    )
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["output"]["preserve_fields"] = [
        "id",
        "coordinate",
    ]
    add("view drops preserved fields", case, cp, f"{view_field}.output.preserve_fields")
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["output"][
        "consumer_may_not_add_unregistered_members"
    ] = False
    add(
        "view allows consumer membership expansion",
        case,
        cp,
        f"{view_field}.output.consumer_may_not_add_unregistered_members",
    )
    case, catalog, _ = mutated()
    catalog["derived_views"][RC023_VIEW_KEY]["output"][
        "consumer_may_not_remove_required_members"
    ] = False
    add(
        "view allows consumer membership removal",
        case,
        cp,
        f"{view_field}.output.consumer_may_not_remove_required_members",
    )
    # Registry identity.
    case, _, registry = mutated()
    del case[rp]
    add("registry missing", case, rp, "file")
    for label, key, value in (
        ("registry schema wrong", "schema", "l9.repository-registry/v2"),
        (
            "registry artifact_id wrong",
            "artifact_id",
            "l9.repository-registry/global@2",
        ),
        ("registry not canonical", "canonical", False),
        (
            "registry class catalog ref wrong",
            "class_catalog_ref",
            "l9.repository-classes/global@2",
        ),
    ):
        case, _, registry = mutated()
        registry[key] = value
        add(label, case, rp, key)
    case, _, registry = mutated()
    registry["repositories"] = {"id": "dot-github"}
    add("repositories not a list", case, rp, "repositories")
    # Census pins.
    case, _, registry = mutated()
    registry["repositories"].append(
        {
            "id": "gate-sdk",
            "coordinate": {
                "provider": "github",
                "organization": "Quantum-L9",
                "repository": "Gate_SDK",
            },
            "lifecycle": "current",
            "class_ref": RC023_CLASS_ID,
        }
    )
    add("extra repository admitted", case, rp, "repositories[gate-sdk].id")
    case, _, registry = mutated()
    registry["repositories"].append(
        {
            "id": "l9-anything",
            "coordinate": {
                "provider": "github",
                "organization": "Quantum-L9",
                "repository": "l9-anything",
            },
            "lifecycle": "current",
            "class_ref": RC023_CLASS_ID,
        }
    )
    add(
        "l9-prefixed repository not admitted by name",
        case,
        rp,
        "repositories[l9-anything].id",
    )
    case, _, registry = mutated()
    registry["repositories"].remove(entry(registry, "l9-goose"))
    add("admitted repository missing", case, rp, "repositories[l9-goose].id")
    case, _, registry = mutated()
    entry(registry, "l9-ops-mcp")["coordinate"]["repository"] = "l9-ops-mcp"
    add(
        "coordinate case changed",
        case,
        rp,
        "repositories[l9-ops-mcp].coordinate.repository",
    )
    case, _, registry = mutated()
    entry(registry, "cursor-governance")["coordinate"]["repository"] = "Cursor-Gov"
    add(
        "coordinate renamed",
        case,
        rp,
        "repositories[cursor-governance].coordinate.repository",
    )
    case, _, registry = mutated()
    entry(registry, "l9-harness")["coordinate"]["organization"] = "quantum-l9"
    add(
        "organization case changed",
        case,
        rp,
        "repositories[l9-harness].coordinate.organization",
    )
    case, _, registry = mutated()
    entry(registry, "l9-harness")["coordinate"]["provider"] = "gitlab"
    add("provider changed", case, rp, "repositories[l9-harness].coordinate.provider")
    case, _, registry = mutated()
    entry(registry, "l9-harness")["coordinate"] = "Quantum-L9/l9-harness"
    add("coordinate not a mapping", case, rp, "repositories[l9-harness].coordinate")
    case, _, registry = mutated()
    registry["repositories"].append(copy.deepcopy(entry(registry, "l9-deploy")))
    add("repository id duplicated", case, rp, "repositories[l9-deploy].id")
    case, _, registry = mutated()
    duplicate = copy.deepcopy(entry(registry, "l9-deploy"))
    duplicate["id"] = "l9-deploy-again"
    registry["repositories"].append(duplicate)
    add("provider coordinate duplicated", case, rp, "repositories[].coordinate")
    case, _, registry = mutated()
    entry(registry, "l9-goose")["class_ref"] = "l9.repository-class/external-fork@1"
    add("wrong class", case, rp, "repositories[l9-goose].class_ref")
    case, _, registry = mutated()
    del entry(registry, "l9-wip")["class_ref"]
    add("class_ref missing", case, rp, "repositories[l9-wip].class_ref")
    case, _, registry = mutated()
    entry(registry, "l9-wip")["lifecycle"] = "archived"
    add("unrecognized lifecycle", case, rp, "repositories[l9-wip].lifecycle")
    case, _, registry = mutated()
    entry(registry, "l9-wip")["lifecycle"] = "retired"
    add("admitted repository not current", case, rp, "repositories[l9-wip].lifecycle")
    case, _, registry = mutated()
    registry["repositories"][0] = "dot-github"
    add("repository entry not a mapping", case, rp, "repositories[0]")
    case, _, registry = mutated()
    del registry["repositories"][0]["id"]
    add("repository id missing", case, rp, "repositories[0].id")
    for label, candidate, case_path, field_name in cases:
        candidate_report = Report()
        try:
            _evaluate_rc023(candidate, candidate_report)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            # A malformed shape must be a located failure, never a crash.
            report.fail(
                "RC-023",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case raised {type(error).__name__} instead of failing closed",
            )
            continue
        prefix = f"FAIL RC-023 {case_path} {field_name}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-023",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {case_path} {field_name}",
            )
    if not any(
        f.startswith(f"FAIL RC-023 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-023-NEG",
            f"{len(cases)} repository class / registry closure negative cases fail "
            "closed at their intended field",
        )


def check_rc023(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc023(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-023",
            f"{RC023_CLASS_ID} is the single admitted repository class and its whole "
            "declaration matches the pinned bytes (current, memory namespace "
            f"{RC023_NAMESPACE}, membership required from the resolved class, projection "
            f"obligation naming no profile or compiler receipt); {RC023_VIEW_ID} selects it over current/superseded/retired and "
            f"derives namespace {RC023_NAMESPACE} preserving id, coordinate, lifecycle, "
            f"class_ref with no consumer membership expansion or removal; the registry "
            f"holds exactly the {RC023_REPOSITORY_COUNT} admitted repositories with "
            "unique ids and unique case-sensitive github/Quantum-L9 coordinates, every "
            "one current and assigned that class",
        )
        _check_rc023_negative_cases(docs, report)


def check_rc006(docs: dict[str, dict], report: Report) -> None:
    registry_path = "semantics/canonical_sources.yaml"
    manifest_path = "semantics/generic_compiler_manifest.yaml"
    registry = docs.get(registry_path)
    manifest = docs.get(manifest_path)
    if registry is None or manifest is None:
        report.fail(
            "RC-006",
            registry_path if registry is None else manifest_path,
            "file",
            "-",
            "required ledger missing or unparsable",
        )
        return
    requires = manifest.get("requires")
    if not isinstance(requires, dict) or not isinstance(
        requires.get("semantic_catalogs"), list
    ):
        report.fail(
            "RC-006",
            manifest_path,
            "requires.semantic_catalogs",
            None,
            "generic compiler manifest declares no semantic catalog class",
        )
        return
    before = len(report.failures)
    registered = [
        str(s.get("path", "")).removeprefix("semantics/")
        for s in registry.get("sources") or []
        if isinstance(s, dict)
    ]
    expected = set(requires["semantic_catalogs"])
    for name in sorted(expected - set(registered)):
        report.fail(
            "RC-006",
            registry_path,
            "sources",
            f"semantics/{name}",
            "semantic catalog declared by the generic compiler manifest is not registered",
        )
    for name in sorted(set(registered) - expected):
        report.fail(
            "RC-006",
            registry_path,
            "sources",
            f"semantics/{name}",
            "registered source is not a semantic catalog of the generic compiler manifest",
        )
    classified: dict[str, list[str]] = {}
    for cls, names in requires.items():
        for name in names if isinstance(names, list) else []:
            classified.setdefault(str(name), []).append(str(cls))
    ledgers = {p.removeprefix("semantics/") for p in docs}
    # The manifest cannot require itself; it is the one self-reference exemption.
    manifest_name = manifest_path.removeprefix("semantics/")
    for name in sorted(ledgers - set(classified) - {manifest_name}):
        report.fail(
            "RC-006",
            manifest_path,
            "requires",
            f"semantics/{name}",
            "canonical ledger is not classified by the generic compiler manifest",
        )
    for name, classes in sorted(classified.items()):
        if len(classes) > 1:
            report.fail(
                "RC-006",
                manifest_path,
                "requires",
                f"semantics/{name}",
                f"ledger is classified more than once: {classes}",
            )
        elif name not in ledgers:
            report.fail(
                "RC-006",
                manifest_path,
                f"requires.{classes[0]}",
                f"semantics/{name}",
                "classified ledger does not exist",
            )
    if len(report.failures) == before:
        report.ok(
            "RC-006",
            f"registry equals the {len(expected)} semantic catalogs of the generic compiler "
            f"manifest; the other {len(ledgers) - 1} ledgers are classified exactly once "
            "(the manifest itself is exempt)",
        )


def check_rc009(docs: dict[str, dict], report: Report) -> None:
    model_path = "semantics/artifact_model.yaml"
    model = docs.get(model_path)
    if model is None:
        report.fail(
            "RC-009", model_path, "file", "-", "artifact model missing or unparsable"
        )
        return
    required = ((model.get("artifacts") or {}).get("product_manifest") or {}).get(
        "required"
    )
    if not isinstance(required, list):
        report.fail(
            "RC-009",
            model_path,
            "artifacts.product_manifest.required",
            required,
            "required-field list missing",
        )
        return
    duplicates = sorted({f for f in required if required.count(f) > 1})
    for field in duplicates:
        report.fail(
            "RC-009",
            model_path,
            "artifacts.product_manifest.required",
            field,
            "required field is declared more than once",
        )
    if not duplicates:
        report.ok(
            "RC-009",
            f"ProductManifest declares {len(required)} required fields with no duplicates",
        )


# RC-024 Strategy semantic-root closure. Strategy must be independently defined
# without using strategy/strategic to define itself, and the current strategic
# semantic family must resolve through that root.
RC024_STRATEGY_DEFINITION = (
    "An integrated theory of intended change that identifies desired future conditions, causal beliefs about "
    "how relevant conditions and actions may influence those conditions, and chosen courses of action under uncertainty."
)
RC024_INTENT_DEFINITION = "The purpose supplied by an applicable authority that constrains what the current Strategy is intended to advance."
RC024_PLAN_DEFINITION = (
    "The authoritative maintained record of the current Strategy within a scope for which the Plan Keeper has "
    "been granted Strategic Authority."
)
RC024_AUTHORITY_DEFINITION = (
    "Explicitly granted authority to create, revise, or supersede the Strategy represented by the Strategic Plan "
    "within a bounded scope."
)
RC024_GHOSTS = {
    "maintained_strategic_direction",
    "revise_strategic_direction_within_explicitly_granted_strategic_authority",
    "revise_strategic_direction_beyond_granted_strategic_authority",
    "strategic_plan_owns_strategy_not_reality",
    "semantic_class: strategic_direction",
}


def _rc024_norm(value: object) -> str:
    return " ".join(str(value or "").split())


def _evaluate_rc024(docs: dict[str, dict], report: Report) -> None:
    cognition = _mapping(docs.get(STRATEGY_MODEL_PATH))
    concepts = _mapping(cognition.get("concepts"))
    strategy = _mapping(concepts.get("strategy"))
    root = _rc024_norm(strategy.get("definition"))
    if root != RC024_STRATEGY_DEFINITION:
        report.fail(
            "RC-024",
            STRATEGY_MODEL_PATH,
            "concepts.strategy.definition",
            strategy.get("definition"),
            "Strategy must match the admitted semantic-root definition",
        )
    if re.search(r"\bstrateg(?:y|ic)\b", root, flags=re.IGNORECASE):
        report.fail(
            "RC-024",
            STRATEGY_MODEL_PATH,
            "concepts.strategy.definition",
            strategy.get("definition"),
            "Strategy may not define itself using strategy or strategic",
        )

    intent = _mapping(concepts.get("strategic_intent"))
    if (
        _rc024_norm(intent.get("definition")) != RC024_INTENT_DEFINITION
        or intent.get("authority_ref") != "authority_model.yaml#strategic_authority"
    ):
        report.fail(
            "RC-024",
            STRATEGY_MODEL_PATH,
            "concepts.strategic_intent",
            intent,
            "Strategic Intent must constrain Strategy and resolve Strategic Authority",
        )

    plan = _mapping(concepts.get("strategic_plan"))
    if _rc024_norm(plan.get("definition")) != RC024_PLAN_DEFINITION:
        report.fail(
            "RC-024",
            STRATEGY_MODEL_PATH,
            "concepts.strategic_plan.definition",
            plan.get("definition"),
            "Strategic Plan must be the authoritative maintained record of current Strategy",
        )

    authority = _mapping(
        _mapping(docs.get(STRATEGY_AUTHORITY_PATH)).get("strategic_authority")
    )
    if (
        _rc024_norm(authority.get("definition")) != RC024_AUTHORITY_DEFINITION
        or authority.get("strategy_concept_ref")
        != "strategic_cognition_model.yaml#concepts.strategy"
    ):
        report.fail(
            "RC-024",
            STRATEGY_AUTHORITY_PATH,
            "strategic_authority",
            authority,
            "Strategic Authority must be explicit and resolve to the Strategy root",
        )
    if authority.get("grant_must_be_explicit") is not True:
        report.fail(
            "RC-024",
            STRATEGY_AUTHORITY_PATH,
            "strategic_authority.grant_must_be_explicit",
            authority.get("grant_must_be_explicit"),
            "Strategic Authority must be explicitly granted",
        )

    resolution = _mapping(
        _mapping(docs.get(STRATEGY_AUTHORITY_PATH)).get("strategic_cognition_authority")
    )
    if resolution.get("strategic_plan_authority_source") != "strategic_authority":
        report.fail(
            "RC-024",
            STRATEGY_AUTHORITY_PATH,
            "strategic_cognition_authority.strategic_plan_authority_source",
            resolution.get("strategic_plan_authority_source"),
            "Strategic Plan authority must resolve to Strategic Authority",
        )

    plan_model = _mapping(docs.get(PLAN_MODEL_PATH))
    reused = _mapping(plan_model.get("reused_concepts"))
    if reused.get("strategy") != {
        "concept_ref": "strategic_cognition_model.yaml#concepts.strategy",
        "owned_here": False,
    }:
        report.fail(
            "RC-024",
            PLAN_MODEL_PATH,
            "reused_concepts.strategy",
            reused.get("strategy"),
            "Strategic Plan content must reuse Strategy without ownership transfer",
        )

    vocab = _mapping(_mapping(docs.get(VOCABULARY_PATH)).get("terms"))
    expected = {
        "strategy": (RC024_STRATEGY_DEFINITION, "strategic_cognition_model.yaml"),
        "strategic_intent": (RC024_INTENT_DEFINITION, "strategic_cognition_model.yaml"),
        "strategic_plan": (RC024_PLAN_DEFINITION, "strategic_cognition_model.yaml"),
        "strategic_authority": (RC024_AUTHORITY_DEFINITION, "authority_model.yaml"),
    }
    for name, (definition, model_name) in expected.items():
        term = _mapping(vocab.get(name))
        if (
            _rc024_norm(term.get("definition")) != definition
            or term.get("detailed_model") != model_name
        ):
            report.fail(
                "RC-024",
                VOCABULARY_PATH,
                f"terms.{name}",
                term,
                "strategy-family vocabulary must mirror its canonical semantic owner",
            )

    serialized = "\n".join(
        (_rc024_norm(cognition), _rc024_norm(plan_model), _rc024_norm(vocab))
    )
    for ghost in sorted(RC024_GHOSTS):
        if ghost in serialized:
            report.fail(
                "RC-024",
                STRATEGY_MODEL_PATH,
                "ghost_semantics",
                ghost,
                "retired strategic-direction semantics must be absent from current canonical strategy ledgers",
            )


def _check_rc024_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases = []

    case = copy.deepcopy(docs)
    case[STRATEGY_MODEL_PATH]["concepts"]["strategy"]["definition"] = (
        "The strategic direction maintained by the Strategic Plan."
    )
    cases.append(
        (
            "circular Strategy definition",
            case,
            STRATEGY_MODEL_PATH,
            "concepts.strategy.definition",
        )
    )

    case = copy.deepcopy(docs)
    del case[STRATEGY_AUTHORITY_PATH]["strategic_authority"]
    cases.append(
        (
            "Strategic Authority removed",
            case,
            STRATEGY_AUTHORITY_PATH,
            "strategic_authority",
        )
    )

    case = copy.deepcopy(docs)
    case[STRATEGY_MODEL_PATH]["roles"][PLAN_KEEPER]["may"][0] = (
        "revise_strategic_direction_within_explicitly_granted_strategic_authority"
    )
    cases.append(
        (
            "ghost Plan Keeper permission restored",
            case,
            STRATEGY_MODEL_PATH,
            "ghost_semantics",
        )
    )

    case = copy.deepcopy(docs)
    del case[PLAN_MODEL_PATH]["reused_concepts"]["strategy"]
    cases.append(
        (
            "Strategic Plan detached from Strategy root",
            case,
            PLAN_MODEL_PATH,
            "reused_concepts.strategy",
        )
    )

    case = copy.deepcopy(docs)
    case[VOCABULARY_PATH]["terms"]["strategy"]["definition"] = (
        "A maintained strategic direction."
    )
    cases.append(
        (
            "vocabulary drifts from Strategy root",
            case,
            VOCABULARY_PATH,
            "terms.strategy",
        )
    )

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc024(candidate, candidate_report)
        prefix = f"FAIL RC-024 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-024",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )

    if not any(
        f.startswith(f"FAIL RC-024 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-024-NEG",
            f"{len(cases)} Strategy semantic-root negative cases fail closed for their intended reason",
        )


def check_rc024(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc024(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-024",
            "Strategy is a non-circular semantic root and Intent, Plan, Authority, Plan content, and vocabulary resolve through it without strategic-direction ghosts",
        )
        _check_rc024_negative_cases(docs, report)


# RC-025 Federated authority graphs + Strategic Plan Graph representation closure.
PLAN_GRAPH_SCHEMA_PATH = "semantics/strategic_plan_graph.schema.yaml"
PLAN_GRAPH_SCHEMA_ID = "l9.schema/strategic-plan-graph@1"
PLAN_GRAPH_SOURCE_ID = "l9.source/strategic-plan-graph-schema@1"
PLAN_GRAPH_SCOPE = "l9_global_strategic_plan_graph_schema"
FEDERATED_GRAPH_PATTERN_ID = "l9.pattern/federated-authority-graphs@1"
PLAN_GRAPH_REQUIRED = {
    "schema",
    "plan_ref",
    "revision_ref",
    "strategic_authority_ref",
    "scope",
    "strategic_intent_refs",
    "objective_refs",
    "nodes",
    "relations",
    "provenance",
    "graph_digest",
}
PLAN_GRAPH_NODE_KINDS = {
    "strategic_goal",
    "strategic_target",
    "strategic_hypothesis",
    "strategic_commitment",
}
PLAN_GRAPH_RELATION_KINDS = {
    "advances",
    "enables",
    "depends_on",
    "conflicts_with",
    "supersedes",
}
PLAN_GRAPH_FORBIDDEN_KEYS = {
    "confidence",
    "probability",
    "horizon",
    "duration",
    "date",
    "start_date",
    "end_date",
    "deadline",
    "budget",
    "priority",
    "resource_allocation",
    "owner_actor_id",
    "executor",
    "task",
    "campaign",
    "status",
    "progress",
    "progress_percentage",
    "affected_strategic_closure",
    "graphiti_id",
    "neo4j_id",
    "database_id",
}


def _rc025_pattern(docs: dict[str, dict], report: Report) -> None:
    patterns_doc = _mapping(docs.get("semantics/architecture_patterns.yaml"))
    matches = [
        item
        for item in _list(patterns_doc.get("patterns"))
        if _mapping(item).get("id") == FEDERATED_GRAPH_PATTERN_ID
    ]
    if len(matches) != 1:
        report.fail(
            "RC-025",
            "semantics/architecture_patterns.yaml",
            "patterns",
            len(matches),
            "federated authority graph pattern must exist exactly once",
        )
        return
    pattern = _mapping(matches[0])
    if pattern.get("class") != "projection":
        report.fail(
            "RC-025",
            "semantics/architecture_patterns.yaml",
            "pattern.class",
            pattern.get("class"),
            "federated authority graphs are a projection/composition pattern",
        )
    refs = _mapping(pattern.get("reference_model"))
    if (
        refs.get("authoritative_direction") != "downstream_to_upstream"
        or refs.get("reverse_traversal") != "derived_reverse_adjacency"
    ):
        report.fail(
            "RC-025",
            "semantics/architecture_patterns.yaml",
            "pattern.reference_model",
            refs,
            "reference direction must be downstream-to-upstream with derived reverse adjacency",
        )
    comp = _mapping(pattern.get("composition"))
    if (
        comp.get("profile_ref") != "l9.compose/consumer-view@1"
        or comp.get("output_authority_class") != "derived"
    ):
        report.fail(
            "RC-025",
            "semantics/architecture_patterns.yaml",
            "pattern.composition",
            comp,
            "cross-graph composition must reuse consumer-view and remain derived",
        )
    required_forbidden = {
        "mega_graph_becomes_canonical_authority",
        "cross_domain_reference_transfers_ownership",
        "upstream_authority_tracks_downstream_consumer_inventory",
        "composed_view_mutates_authoritative_sources",
        "graph_database_or_index_provider_becomes_semantic_owner",
        "unresolved_reference_is_silently_treated_as_resolved",
    }
    if not required_forbidden <= set(_list(pattern.get("forbidden"))):
        report.fail(
            "RC-025",
            "semantics/architecture_patterns.yaml",
            "pattern.forbidden",
            pattern.get("forbidden"),
            "federation anti-authority and fail-closed rules must remain explicit",
        )


def _rc025_schema(docs: dict[str, dict], report: Report) -> None:
    graph = _mapping(docs.get(PLAN_GRAPH_SCHEMA_PATH))
    if (
        graph.get("schema") != "l9.schema-definition/v1"
        or graph.get("artifact_id") != PLAN_GRAPH_SCHEMA_ID
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "identity",
            graph.get("artifact_id"),
            "Strategic Plan Graph schema identity must be canonical v1",
        )
    authority = _mapping(graph.get("authority"))
    if (
        graph.get("canonical") is not True
        or authority.get("owner") != STRATEGY_OWNER
        or authority.get("scope") != PLAN_GRAPH_SCOPE
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "authority",
            authority,
            "Strategic Plan Graph schema must be canonical and globally owned by .github",
        )
    if set(_list(graph.get("required"))) != PLAN_GRAPH_REQUIRED:
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "required",
            graph.get("required"),
            "Strategic Plan Graph top-level required fields must remain minimal and exact",
        )
    props = _mapping(graph.get("properties"))
    node = _mapping(_mapping(_mapping(props.get("nodes")).get("items")).get("fields"))
    kinds = set(_list(_mapping(node.get("kind")).get("enum")))
    if kinds != PLAN_GRAPH_NODE_KINDS:
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "properties.nodes.items.fields.kind.enum",
            sorted(kinds),
            "exactly the four admitted Plan-owned primitive kinds may be local nodes",
        )
    relation = _mapping(
        _mapping(_mapping(props.get("relations")).get("items")).get("fields")
    )
    relation_kinds = set(_list(_mapping(relation.get("relation")).get("enum")))
    if relation_kinds != PLAN_GRAPH_RELATION_KINDS:
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "properties.relations.items.fields.relation.enum",
            sorted(relation_kinds),
            "exactly the five admitted strategic relation kinds are representable",
        )
    if "strategy" in kinds:
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "properties.nodes.items.fields.kind.enum",
            "strategy",
            "Strategy is the integrated meaning of the graph, never a fifth node kind",
        )
    found = [
        path for path, key in _key_paths(graph) if key in PLAN_GRAPH_FORBIDDEN_KEYS
    ]
    if found:
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "forbidden_representation_keys",
            found,
            "v3.18 Plan Graph must not absorb deferred planning, execution, storage, or closure fields",
        )
    refs = _mapping(graph.get("reference_rules"))
    if (
        refs.get("external_references_remain_externally_owned") is not True
        or refs.get("reverse_adjacency_is_derived") is not True
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "reference_rules",
            refs,
            "external reference ownership and derived reverse adjacency must remain explicit",
        )
    if refs.get("unresolved_external_reference_result") != "unknown":
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "reference_rules.unresolved_external_reference_result",
            refs.get("unresolved_external_reference_result"),
            "unresolved external references must preserve Unknown",
        )
    constraints = _mapping(graph.get("relation_constraints"))
    all_rules = _mapping(constraints.get("all"))
    enables = _mapping(constraints.get("enables"))
    supersedes = _mapping(constraints.get("supersedes"))
    if (
        all_rules.get("at_least_one_endpoint_must_resolve_to_local_plan_node")
        is not True
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "relation_constraints.all",
            all_rules,
            "every strategic relation must touch at least one local Plan node",
        )
    if (
        enables.get("hypothesis_ref_required") is not True
        or enables.get("hypothesis_ref_must_resolve_to_local_kind")
        != "strategic_hypothesis"
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "relation_constraints.enables",
            enables,
            "enables must remain attributable to one local Strategic Hypothesis",
        )
    if (
        supersedes.get("source_must_resolve_to_local_plan_node") is not True
        or supersedes.get("target_must_resolve_to_same_primitive_kind") is not True
        or supersedes.get("target_may_resolve_to_prior_revision_same_plan_lineage")
        is not True
    ):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "relation_constraints.supersedes",
            supersedes,
            "supersedes must preserve same-kind Plan lineage across immutable revisions",
        )
    revisions = _mapping(graph.get("revision_rules"))
    required_revision_rules = {
        "graph_represents_exactly_one_plan_revision",
        "content_change_requires_new_revision_ref",
        "predecessor_when_present_must_reference_prior_revision_same_plan_lineage",
        "prior_revisions_remain_addressable",
        "historical_revision_content_is_immutable",
        "graph_digest_binds_exact_revision_content",
    }
    if not all(revisions.get(rule) is True for rule in required_revision_rules):
        report.fail(
            "RC-025",
            PLAN_GRAPH_SCHEMA_PATH,
            "revision_rules",
            revisions,
            "Plan revision identity, immutability, lineage, and digest binding must remain closed",
        )


def _rc025_registration(docs: dict[str, dict], report: Report) -> None:
    registry = _mapping(docs.get("semantics/canonical_sources.yaml"))
    entries = [
        item
        for item in _list(registry.get("sources"))
        if _mapping(item).get("id") == PLAN_GRAPH_SOURCE_ID
    ]
    if len(entries) != 1 or _mapping(entries[0]).get("path") != PLAN_GRAPH_SCHEMA_PATH:
        report.fail(
            "RC-025",
            "semantics/canonical_sources.yaml",
            "sources",
            entries,
            "Strategic Plan Graph schema must be registered exactly once as a canonical source",
        )
    manifest = _mapping(docs.get("semantics/generic_compiler_manifest.yaml"))
    requires = _mapping(manifest.get("requires"))
    semantic_catalogs = _list(requires.get("semantic_catalogs"))
    artifact_schemas = _list(requires.get("artifact_schemas"))
    filename = PLAN_GRAPH_SCHEMA_PATH.removeprefix("semantics/")
    if semantic_catalogs.count(filename) != 1:
        report.fail(
            "RC-025",
            "semantics/generic_compiler_manifest.yaml",
            "requires.semantic_catalogs",
            semantic_catalogs,
            "authoritative Strategic Plan Graph schema must be a semantic catalog exactly once",
        )
    if filename in artifact_schemas:
        report.fail(
            "RC-025",
            "semantics/generic_compiler_manifest.yaml",
            "requires.artifact_schemas",
            artifact_schemas,
            "authoritative Strategic Plan Graph schema must not be misclassified as compiler-output artifact schema",
        )


def _evaluate_rc025(docs: dict[str, dict], report: Report) -> None:
    _rc025_pattern(docs, report)
    _rc025_schema(docs, report)
    _rc025_registration(docs, report)


def _check_rc025_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases = []
    model = PLAN_GRAPH_SCHEMA_PATH
    pattern_path = "semantics/architecture_patterns.yaml"
    registry_path = "semantics/canonical_sources.yaml"
    manifest_path = "semantics/generic_compiler_manifest.yaml"

    def pattern(case):
        return next(
            item
            for item in case[pattern_path]["patterns"]
            if item.get("id") == FEDERATED_GRAPH_PATTERN_ID
        )

    case = copy.deepcopy(docs)
    case[model]["properties"]["nodes"]["items"]["fields"]["kind"]["enum"].append(
        "capability"
    )
    cases.append(
        (
            "fifth local primitive",
            case,
            model,
            "properties.nodes.items.fields.kind.enum",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["properties"]["relations"]["items"]["fields"]["relation"][
        "enum"
    ].append("causes")
    cases.append(
        (
            "sixth strategic relation",
            case,
            model,
            "properties.relations.items.fields.relation.enum",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["properties"]["nodes"]["items"]["fields"]["kind"]["enum"].append(
        "strategy"
    )
    cases.append(
        (
            "Strategy becomes local node",
            case,
            model,
            "properties.nodes.items.fields.kind.enum",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["required"].remove("strategic_authority_ref")
    cases.append(("authority ref becomes optional", case, model, "required"))
    case = copy.deepcopy(docs)
    case[model]["properties"]["confidence"] = {"type": "number"}
    cases.append(
        (
            "confidence leaks into Plan Graph",
            case,
            model,
            "forbidden_representation_keys",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["properties"]["affected_strategic_closure"] = {"type": "array"}
    cases.append(
        ("Affected Closure serialized", case, model, "forbidden_representation_keys")
    )
    case = copy.deepcopy(docs)
    case[model]["relation_constraints"]["all"][
        "at_least_one_endpoint_must_resolve_to_local_plan_node"
    ] = False
    cases.append(
        ("world graph relation permitted", case, model, "relation_constraints.all")
    )
    case = copy.deepcopy(docs)
    case[model]["relation_constraints"]["enables"]["hypothesis_ref_required"] = False
    cases.append(
        (
            "enables loses hypothesis attribution",
            case,
            model,
            "relation_constraints.enables",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["relation_constraints"]["enables"][
        "hypothesis_ref_must_resolve_to_local_kind"
    ] = "strategic_commitment"
    cases.append(
        (
            "enables attributed to wrong primitive",
            case,
            model,
            "relation_constraints.enables",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["relation_constraints"]["supersedes"][
        "target_must_resolve_to_same_primitive_kind"
    ] = False
    cases.append(
        (
            "cross-kind supersession allowed",
            case,
            model,
            "relation_constraints.supersedes",
        )
    )
    case = copy.deepcopy(docs)
    case[model]["reference_rules"]["external_references_remain_externally_owned"] = (
        False
    )
    cases.append(("external ownership absorbed", case, model, "reference_rules"))
    case = copy.deepcopy(docs)
    case[model]["reference_rules"]["unresolved_external_reference_result"] = "resolved"
    cases.append(
        (
            "Unknown coerced to resolved",
            case,
            model,
            "reference_rules.unresolved_external_reference_result",
        )
    )
    case = copy.deepcopy(docs)
    pattern(case)["composition"]["output_authority_class"] = "canonical"
    cases.append(
        ("management view becomes authority", case, pattern_path, "pattern.composition")
    )
    case = copy.deepcopy(docs)
    pattern(case)["reference_model"]["authoritative_direction"] = (
        "upstream_to_downstream"
    )
    cases.append(
        ("upstream tracks downstream", case, pattern_path, "pattern.reference_model")
    )
    case = copy.deepcopy(docs)
    case[manifest_path]["requires"]["semantic_catalogs"].remove(
        "strategic_plan_graph.schema.yaml"
    )
    case[manifest_path]["requires"]["artifact_schemas"].append(
        "strategic_plan_graph.schema.yaml"
    )
    cases.append(
        (
            "schema misclassified as compiler output",
            case,
            manifest_path,
            "requires.semantic_catalogs",
        )
    )
    case = copy.deepcopy(docs)
    case[registry_path]["sources"] = [
        x for x in case[registry_path]["sources"] if x.get("id") != PLAN_GRAPH_SOURCE_ID
    ]
    cases.append(("schema registration removed", case, registry_path, "sources"))

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc025(candidate, candidate_report)
        prefix = f"FAIL RC-025 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-025",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith(f"FAIL RC-025 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-025-NEG",
            f"{len(cases)} federation / Strategic Plan Graph negative cases fail closed for their intended reason",
        )


def check_rc025(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc025(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-025",
            "federated authority graphs preserve independent ownership and Strategic Plan Graph v1 admits only the minimal 4-node / 5-relation representation with authority, reference, causal-attribution, revision, and compiler-registration closure",
        )
        _check_rc025_negative_cases(docs, report)


# RC-026 Strategic planning cognition representation closure. These schemas
# freeze the Planner / Meta-Planner handoff without admitting runtime algorithms
# or allowing reasoning artifacts to acquire Strategic Authority.
AFFECTED_CLOSURE_SCHEMA_PATH = "semantics/affected_strategic_closure.schema.yaml"
PLANNING_EPISODE_SCHEMA_PATH = "semantics/strategic_planning_episode.schema.yaml"
PLAN_REVISION_CANDIDATE_SCHEMA_PATH = (
    "semantics/strategic_plan_revision_candidate.schema.yaml"
)
METACOG_ANALYSIS_SCHEMA_PATH = (
    "semantics/strategic_plan_metacognitive_analysis.schema.yaml"
)
STRATEGIC_COGNITION_MODEL_PATH = "semantics/strategic_cognition_model.yaml"
STRATEGIC_PLAN_MODEL_PATH = "semantics/strategic_plan_model.yaml"

RC026_SCHEMA_IDS = {
    AFFECTED_CLOSURE_SCHEMA_PATH: "l9.schema/affected-strategic-closure@1",
    PLANNING_EPISODE_SCHEMA_PATH: "l9.schema/strategic-planning-episode@1",
    PLAN_REVISION_CANDIDATE_SCHEMA_PATH: "l9.schema/strategic-plan-revision-candidate@1",
    METACOG_ANALYSIS_SCHEMA_PATH: "l9.schema/strategic-plan-metacognitive-analysis@1",
}
RC026_SOURCE_IDS = {
    AFFECTED_CLOSURE_SCHEMA_PATH: "l9.source/affected-strategic-closure-schema@1",
    PLANNING_EPISODE_SCHEMA_PATH: "l9.source/strategic-planning-episode-schema@1",
    PLAN_REVISION_CANDIDATE_SCHEMA_PATH: "l9.source/strategic-plan-revision-candidate-schema@1",
    METACOG_ANALYSIS_SCHEMA_PATH: "l9.source/strategic-plan-metacognitive-analysis-schema@1",
}
RC026_FILENAMES = [path.removeprefix("semantics/") for path in RC026_SCHEMA_IDS]


def _rc026_fields(node: object) -> dict:
    return _mapping(_mapping(node).get("fields"))


def _rc026_required(schema: dict) -> set[str]:
    return {item for item in _list(schema.get("required")) if isinstance(item, str)}


def _rc026_schema_identity(path: str, schema: dict, report: Report) -> None:
    expected_id = RC026_SCHEMA_IDS[path]
    if schema.get("schema") != "l9.schema-definition/v1":
        report.fail(
            "RC-026",
            path,
            "schema",
            schema.get("schema"),
            "schema-definition identity drift",
        )
    if schema.get("artifact_id") != expected_id:
        report.fail(
            "RC-026",
            path,
            "artifact_id",
            schema.get("artifact_id"),
            f"expected {expected_id}",
        )
    if schema.get("canonical") is not True:
        report.fail(
            "RC-026",
            path,
            "canonical",
            schema.get("canonical"),
            "planning cognition schema must remain canonical",
        )
    authority = _mapping(schema.get("authority"))
    if (
        authority.get("owner") != "Quantum-L9/.github"
        or authority.get("authority_class") != "canonical"
    ):
        report.fail(
            "RC-026",
            path,
            "authority",
            authority,
            "schema authority must remain canonical .github law",
        )


def _rc026_closure(docs: dict[str, dict], report: Report) -> None:
    path = AFFECTED_CLOSURE_SCHEMA_PATH
    schema = _mapping(docs.get(path))
    _rc026_schema_identity(path, schema, report)
    inst = _mapping(schema.get("instance_semantics"))
    if (
        inst.get("authority_class") != "derived"
        or inst.get("authoritative") is not False
        or inst.get("authority_effect") != "none"
    ):
        report.fail(
            "RC-026",
            path,
            "instance_semantics",
            inst,
            "Affected Closure must remain derived, non-authoritative, and effect-free",
        )
    required = _rc026_required(schema)
    expected = {
        "schema",
        "closure_ref",
        "plan_ref",
        "plan_revision_ref",
        "plan_graph_digest",
        "trigger_sources",
        "affected_plan_refs",
        "provenance",
        "closure_digest",
    }
    if required != expected:
        report.fail(
            "RC-026",
            path,
            "required",
            sorted(required),
            "Affected Closure required field set drifted",
        )
    rules = _mapping(schema.get("closure_rules"))
    required_rules = {
        "affected_refs_must_resolve_to_plan_owned_claims_in_bound_revision",
        "empty_closure_is_valid_when_no_plan_owned_claim_materially_depends_on_trigger",
        "unresolved_dependency_is_preserved_as_unknown",
        "closure_algorithm_is_not_defined_by_this_schema",
        "closure_result_is_invalidated_by_bound_plan_revision_or_trigger_digest_change",
    }
    if not all(rules.get(key) is True for key in required_rules):
        report.fail(
            "RC-026",
            path,
            "closure_rules",
            rules,
            "closure must remain bounded, Unknown-preserving, digest-bound, and algorithm-neutral",
        )
    semantic = set(_list(schema.get("semantic_rules")))
    needed = {
        "closure_does_not_decide_strategy",
        "closure_does_not_modify_or_invalidate_strategic_plan",
        "closure_does_not_mark_plan_claims_false_or_stale_automatically",
        "closure_does_not_transfer_truth_source_ownership",
    }
    if not needed <= semantic:
        report.fail(
            "RC-026",
            path,
            "semantic_rules",
            sorted(semantic),
            "Affected Closure anti-authority rules missing",
        )


def _rc026_episode(docs: dict[str, dict], report: Report) -> None:
    path = PLANNING_EPISODE_SCHEMA_PATH
    schema = _mapping(docs.get(path))
    _rc026_schema_identity(path, schema, report)
    inst = _mapping(schema.get("instance_semantics"))
    if (
        inst.get("authority_class") != "derived"
        or inst.get("authoritative") is not False
        or inst.get("authority_effect") != "none"
        or inst.get("producer_role") != "plan_keeper"
    ):
        report.fail(
            "RC-026",
            path,
            "instance_semantics",
            inst,
            "Planning Episode must remain Plan-Keeper-produced derived reasoning with zero authority effect",
        )
    required = _rc026_required(schema)
    expected = {
        "schema",
        "episode_ref",
        "plan_ref",
        "plan_revision_ref",
        "plan_graph_digest",
        "strategic_authority_ref",
        "strategic_intent_refs",
        "objective_refs",
        "current_meta_view",
        "trigger_sources",
        "workspace",
        "recommendation",
        "provenance",
        "episode_digest",
    }
    if required != expected:
        report.fail(
            "RC-026",
            path,
            "required",
            sorted(required),
            "Planning Episode required field set drifted",
        )
    props = _mapping(schema.get("properties"))
    workspace = _mapping(props.get("workspace"))
    workspace_required = set(_list(workspace.get("required")))
    expected_workspace = {
        "decision_question",
        "observations",
        "assumptions",
        "candidate_paths",
        "evaluations",
        "material_unknowns",
    }
    if workspace_required != expected_workspace:
        report.fail(
            "RC-026",
            path,
            "properties.workspace.required",
            sorted(workspace_required),
            "reasoning workspace partitions or material Unknown closure drifted",
        )
    wf = _rc026_fields(workspace)
    candidate_paths = _mapping(wf.get("candidate_paths"))
    cp_fields = _rc026_fields(_mapping(candidate_paths.get("items")))
    disposition = set(_list(_mapping(cp_fields.get("disposition")).get("enum")))
    if disposition != {"considered", "rejected", "recommended_for_candidate"}:
        report.fail(
            "RC-026",
            path,
            "properties.workspace.fields.candidate_paths.items.fields.disposition.enum",
            sorted(disposition),
            "candidate path disposition must never imply commitment",
        )
    evaluations = _mapping(wf.get("evaluations"))
    ev_fields = _rc026_fields(_mapping(evaluations.get("items")))
    ev_results = set(_list(_mapping(ev_fields.get("result")).get("enum")))
    if ev_results != {"favorable", "unfavorable", "mixed", "unknown"}:
        report.fail(
            "RC-026",
            path,
            "properties.workspace.fields.evaluations.items.fields.result.enum",
            sorted(ev_results),
            "evaluation result algebra drifted",
        )
    rec = _mapping(props.get("recommendation"))
    rf = _rc026_fields(rec)
    outcomes = set(_list(_mapping(rf.get("outcome")).get("enum")))
    if outcomes != {"retain_current_plan", "propose_revision", "unresolved"}:
        report.fail(
            "RC-026",
            path,
            "properties.recommendation.fields.outcome.enum",
            sorted(outcomes),
            "Planning Episode recommendation outcomes drifted",
        )
    authority_effect = _mapping(rf.get("authority_effect")).get("const")
    if authority_effect != "none":
        report.fail(
            "RC-026",
            path,
            "properties.recommendation.fields.authority_effect",
            authority_effect,
            "recommendation may not create strategic authority",
        )
    rules = _mapping(schema.get("workspace_rules"))
    required_rules = {
        "observations_reference_sources_but_do_not_take_truth_ownership",
        "assumptions_are_provisional_reasoning_objects_not_plan_owned_beliefs",
        "candidate_paths_are_not_strategic_commitments",
        "evaluations_do_not_create_objective_or_evidence_authority",
        "recommendation_is_not_a_strategic_decision",
        "propose_revision_outcome_requires_separate_revision_candidate_artifact",
        "changed_bound_input_digest_invalidates_episode_currentness",
    }
    if not all(rules.get(key) is True for key in required_rules):
        report.fail(
            "RC-026",
            path,
            "workspace_rules",
            rules,
            "Planning Episode workspace / Strategy boundary drifted",
        )


def _rc026_candidate(docs: dict[str, dict], report: Report) -> None:
    path = PLAN_REVISION_CANDIDATE_SCHEMA_PATH
    schema = _mapping(docs.get(path))
    _rc026_schema_identity(path, schema, report)
    inst = _mapping(schema.get("instance_semantics"))
    if (
        inst.get("authority_class") != "candidate"
        or inst.get("authoritative") is not False
        or inst.get("authority_effect") != "none_until_admitted"
        or inst.get("producer_role") != "plan_keeper"
    ):
        report.fail(
            "RC-026",
            path,
            "instance_semantics",
            inst,
            "Revision Candidate must remain non-authoritative candidate output from Plan Keeper",
        )
    required = _rc026_required(schema)
    expected = {
        "schema",
        "candidate_ref",
        "plan_ref",
        "predecessor",
        "proposed_graph",
        "reasoning_episode",
        "strategic_authority_ref",
        "rationale_refs",
        "provenance",
        "candidate_digest",
    }
    if required != expected:
        report.fail(
            "RC-026",
            path,
            "required",
            sorted(required),
            "Revision Candidate required field set drifted",
        )
    props = _mapping(schema.get("properties"))
    pg = _mapping(props.get("proposed_graph"))
    pg_fields = _rc026_fields(pg)
    schema_ref = _mapping(pg_fields.get("schema_ref")).get("const")
    if schema_ref != "l9.schema/strategic-plan-graph@1":
        report.fail(
            "RC-026",
            path,
            "properties.proposed_graph.fields.schema_ref",
            schema_ref,
            "proposed graph must bind canonical Strategic Plan Graph schema",
        )
    if set(_list(pg.get("required"))) != {"ref", "schema_ref", "digest"}:
        report.fail(
            "RC-026",
            path,
            "properties.proposed_graph.required",
            pg.get("required"),
            "proposed graph exact ref/schema/digest binding required",
        )
    rules = _mapping(schema.get("candidate_rules"))
    required_rules = {
        "proposed_graph_must_conform_to_strategic_plan_graph_schema",
        "proposed_graph_plan_ref_must_equal_candidate_plan_ref",
        "proposed_graph_predecessor_must_bind_exact_predecessor",
        "predecessor_must_be_current_at_admission_or_admission_fails_closed",
        "admission_must_bind_candidate_digest_and_proposed_graph_digest",
        "candidate_change_requires_new_authority_decision",
        "proposed_graph_change_requires_new_authority_decision",
        "candidate_may_be_rejected_without_mutating_current_plan",
    }
    if not all(rules.get(key) is True for key in required_rules):
        report.fail(
            "RC-026",
            path,
            "candidate_rules",
            rules,
            "candidate digest/admission/predecessor closure drifted",
        )
    semantic = set(_list(schema.get("semantic_rules")))
    needed = {
        "revision_candidate_is_candidate_not_strategy",
        "revision_candidate_does_not_self_admit",
        "revision_candidate_does_not_modify_strategic_plan",
        "admission_is_external_to_candidate_artifact",
        "authorization_must_bind_exact_candidate_and_proposed_graph_digests",
    }
    if not needed <= semantic:
        report.fail(
            "RC-026",
            path,
            "semantic_rules",
            sorted(semantic),
            "candidate anti-self-admission / anti-mutation rules missing",
        )


def _rc026_meta(docs: dict[str, dict], report: Report) -> None:
    path = METACOG_ANALYSIS_SCHEMA_PATH
    schema = _mapping(docs.get(path))
    _rc026_schema_identity(path, schema, report)
    inst = _mapping(schema.get("instance_semantics"))
    if (
        inst.get("authority_class") != "derived"
        or inst.get("authoritative") is not False
        or inst.get("output_authority") != "advisory"
        or inst.get("authority_effect") != "none"
        or inst.get("producer_role") != "strategic_plan_metacognitive_reasoner"
    ):
        report.fail(
            "RC-026",
            path,
            "instance_semantics",
            inst,
            "Metacognitive Analysis must remain derived, advisory, and non-authoritative",
        )
    required = _rc026_required(schema)
    expected = {
        "schema",
        "analysis_ref",
        "plan_ref",
        "subject_episodes",
        "plan_revision_refs",
        "outcome_evidence_refs",
        "findings",
        "patterns",
        "lessons",
        "provenance",
        "analysis_digest",
    }
    if required != expected:
        report.fail(
            "RC-026",
            path,
            "required",
            sorted(required),
            "Metacognitive Analysis required field set drifted",
        )
    props = _mapping(schema.get("properties"))
    findings = _mapping(props.get("findings"))
    f_fields = _rc026_fields(_mapping(findings.get("items")))
    finding_kinds = set(_list(_mapping(f_fields.get("kind")).get("enum")))
    expected_findings = {
        "reasoning_strength",
        "reasoning_failure",
        "expectation_outcome_mismatch",
        "revision_pattern",
        "unknown",
    }
    if finding_kinds != expected_findings:
        report.fail(
            "RC-026",
            path,
            "properties.findings.items.fields.kind.enum",
            sorted(finding_kinds),
            "metacognitive findings must remain reasoning-focused",
        )
    patterns = _mapping(props.get("patterns"))
    p_fields = _rc026_fields(_mapping(patterns.get("items")))
    pattern_kinds = set(_list(_mapping(p_fields.get("kind")).get("enum")))
    expected_patterns = {
        "recurring_reasoning_strength",
        "recurring_reasoning_failure",
        "recurring_expectation_outcome_pattern",
        "unknown",
    }
    if pattern_kinds != expected_patterns:
        report.fail(
            "RC-026",
            path,
            "properties.patterns.items.fields.kind.enum",
            sorted(pattern_kinds),
            "metacognitive patterns must remain reasoning-focused",
        )
    lessons = _mapping(props.get("lessons"))
    l_fields = _rc026_fields(_mapping(lessons.get("items")))
    lesson_effect = _mapping(l_fields.get("authority_effect")).get("const")
    if lesson_effect != "none":
        report.fail(
            "RC-026",
            path,
            "properties.lessons.items.fields.authority_effect",
            lesson_effect,
            "planning cognition lesson must remain advisory",
        )
    rules = _mapping(schema.get("analysis_rules"))
    required_rules = {
        "findings_must_trace_to_exact_episode_revision_or_evidence_refs",
        "recurring_pattern_requires_multiple_occurrence_refs",
        "lessons_must_trace_to_findings_patterns_or_exact_source_refs",
        "lesson_is_advisory_input_to_plan_keeper_only",
        "metacognitive_analysis_cannot_modify_or_supersede_strategic_plan",
        "metacognitive_analysis_cannot_grant_strategic_authority",
        "metacognitive_analysis_cannot_reinterpret_external_evidence_as_owned_truth",
        "metacognitive_analysis_is_not_universal_metacognitive_authority",
    }
    if not all(rules.get(key) is True for key in required_rules):
        report.fail(
            "RC-026",
            path,
            "analysis_rules",
            rules,
            "Meta-Planner advisory / ownership boundary drifted",
        )


def _rc026_semantic_anchors(docs: dict[str, dict], report: Report) -> None:
    cognition = _mapping(docs.get(STRATEGIC_COGNITION_MODEL_PATH))
    artifacts = _mapping(cognition.get("reasoning_artifacts"))
    expected = {
        "strategic_planning_episode": "l9.schema/strategic-planning-episode@1",
        "strategic_plan_revision_candidate": "l9.schema/strategic-plan-revision-candidate@1",
        "strategic_plan_metacognitive_analysis": "l9.schema/strategic-plan-metacognitive-analysis@1",
    }
    for name, schema_ref in expected.items():
        item = _mapping(artifacts.get(name))
        if item.get("schema_ref") != schema_ref:
            report.fail(
                "RC-026",
                STRATEGIC_COGNITION_MODEL_PATH,
                f"reasoning_artifacts.{name}.schema_ref",
                item.get("schema_ref"),
                f"expected {schema_ref}",
            )
    plan_keeper = _mapping(_mapping(cognition.get("roles")).get("plan_keeper"))
    may = set(_list(plan_keeper.get("may")))
    if (
        not {
            "emit_strategic_planning_episode",
            "emit_strategic_plan_revision_candidate",
        }
        <= may
    ):
        report.fail(
            "RC-026",
            STRATEGIC_COGNITION_MODEL_PATH,
            "roles.plan_keeper.may",
            sorted(may),
            "Plan Keeper must own emission of planning episode and revision candidate",
        )
    meta = _mapping(
        _mapping(cognition.get("roles")).get("strategic_plan_metacognitive_reasoner")
    )
    meta_may = set(_list(meta.get("may")))
    if "emit_strategic_plan_metacognitive_analysis" not in meta_may:
        report.fail(
            "RC-026",
            STRATEGIC_COGNITION_MODEL_PATH,
            "roles.strategic_plan_metacognitive_reasoner.may",
            sorted(meta_may),
            "Meta-Planner must own its analysis output",
        )
    plan = _mapping(docs.get(STRATEGIC_PLAN_MODEL_PATH))
    closure = _mapping(
        _mapping(plan.get("reasoning_concepts")).get("affected_strategic_closure")
    )
    if (
        closure.get("representation_schema_ref")
        != "l9.schema/affected-strategic-closure@1"
        or closure.get("authority_class") != "derived"
        or closure.get("authoritative") is not False
        or closure.get("representation_does_not_define_closure_algorithm") is not True
    ):
        report.fail(
            "RC-026",
            STRATEGIC_PLAN_MODEL_PATH,
            "reasoning_concepts.affected_strategic_closure",
            closure,
            "Affected Strategic Closure semantic owner must bind derived schema while deferring algorithm",
        )


def _rc026_registration(docs: dict[str, dict], report: Report) -> None:
    registry_path = "semantics/canonical_sources.yaml"
    registry = _mapping(docs.get(registry_path))
    sources = _list(registry.get("sources"))
    for path, source_id in RC026_SOURCE_IDS.items():
        entries = [item for item in sources if _mapping(item).get("id") == source_id]
        if len(entries) != 1 or _mapping(entries[0]).get("path") != path:
            report.fail(
                "RC-026",
                registry_path,
                "sources",
                entries,
                f"{source_id} must register {path} exactly once",
            )
    manifest_path = "semantics/generic_compiler_manifest.yaml"
    manifest = _mapping(docs.get(manifest_path))
    requires = _mapping(manifest.get("requires"))
    semantic_catalogs = _list(requires.get("semantic_catalogs"))
    artifact_schemas = _list(requires.get("artifact_schemas"))
    for filename in RC026_FILENAMES:
        if semantic_catalogs.count(filename) != 1:
            report.fail(
                "RC-026",
                manifest_path,
                "requires.semantic_catalogs",
                semantic_catalogs,
                f"{filename} must be consumed exactly once as a semantic catalog",
            )
        if filename in artifact_schemas:
            report.fail(
                "RC-026",
                manifest_path,
                "requires.artifact_schemas",
                artifact_schemas,
                f"{filename} must not be misclassified as compiler-output artifact schema",
            )


def _evaluate_rc026(docs: dict[str, dict], report: Report) -> None:
    _rc026_closure(docs, report)
    _rc026_episode(docs, report)
    _rc026_candidate(docs, report)
    _rc026_meta(docs, report)
    _rc026_semantic_anchors(docs, report)
    _rc026_registration(docs, report)


def _check_rc026_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases = []

    case = copy.deepcopy(docs)
    case[AFFECTED_CLOSURE_SCHEMA_PATH]["instance_semantics"]["authority_class"] = (
        "canonical"
    )
    cases.append(
        (
            "closure authority inflation",
            case,
            AFFECTED_CLOSURE_SCHEMA_PATH,
            "instance_semantics",
        )
    )

    case = copy.deepcopy(docs)
    case[AFFECTED_CLOSURE_SCHEMA_PATH]["closure_rules"][
        "closure_algorithm_is_not_defined_by_this_schema"
    ] = False
    cases.append(
        (
            "closure algorithm capture",
            case,
            AFFECTED_CLOSURE_SCHEMA_PATH,
            "closure_rules",
        )
    )

    case = copy.deepcopy(docs)
    case[AFFECTED_CLOSURE_SCHEMA_PATH]["semantic_rules"].remove(
        "closure_does_not_modify_or_invalidate_strategic_plan"
    )
    cases.append(
        (
            "closure Plan mutation permission",
            case,
            AFFECTED_CLOSURE_SCHEMA_PATH,
            "semantic_rules",
        )
    )

    case = copy.deepcopy(docs)
    case[PLANNING_EPISODE_SCHEMA_PATH]["instance_semantics"]["authority_class"] = (
        "canonical"
    )
    cases.append(
        (
            "Planning Episode authority inflation",
            case,
            PLANNING_EPISODE_SCHEMA_PATH,
            "instance_semantics",
        )
    )

    case = copy.deepcopy(docs)
    case[PLANNING_EPISODE_SCHEMA_PATH]["properties"]["recommendation"]["fields"][
        "authority_effect"
    ]["const"] = "strategic"
    cases.append(
        (
            "Planning Episode recommendation authority inflation",
            case,
            PLANNING_EPISODE_SCHEMA_PATH,
            "properties.recommendation.fields.authority_effect",
        )
    )

    case = copy.deepcopy(docs)
    case[PLANNING_EPISODE_SCHEMA_PATH]["properties"]["workspace"]["fields"][
        "candidate_paths"
    ]["items"]["fields"]["disposition"]["enum"].append("committed")
    cases.append(
        (
            "candidate path silently becomes commitment",
            case,
            PLANNING_EPISODE_SCHEMA_PATH,
            "properties.workspace.fields.candidate_paths.items.fields.disposition.enum",
        )
    )

    case = copy.deepcopy(docs)
    case[PLANNING_EPISODE_SCHEMA_PATH]["properties"]["workspace"]["required"].remove(
        "material_unknowns"
    )
    cases.append(
        (
            "material Unknown becomes optional",
            case,
            PLANNING_EPISODE_SCHEMA_PATH,
            "properties.workspace.required",
        )
    )

    case = copy.deepcopy(docs)
    case[STRATEGIC_COGNITION_MODEL_PATH]["reasoning_artifacts"][
        "strategic_planning_episode"
    ]["schema_ref"] = "l9.schema/other@1"
    cases.append(
        (
            "Planning Episode semantic-owner schema drift",
            case,
            STRATEGIC_COGNITION_MODEL_PATH,
            "reasoning_artifacts.strategic_planning_episode.schema_ref",
        )
    )

    case = copy.deepcopy(docs)
    case[PLAN_REVISION_CANDIDATE_SCHEMA_PATH]["instance_semantics"][
        "authority_class"
    ] = "canonical"
    cases.append(
        (
            "Revision Candidate authority inflation",
            case,
            PLAN_REVISION_CANDIDATE_SCHEMA_PATH,
            "instance_semantics",
        )
    )

    case = copy.deepcopy(docs)
    case[PLAN_REVISION_CANDIDATE_SCHEMA_PATH]["properties"]["proposed_graph"]["fields"][
        "schema_ref"
    ]["const"] = "l9.schema/other@1"
    cases.append(
        (
            "proposed graph schema drift",
            case,
            PLAN_REVISION_CANDIDATE_SCHEMA_PATH,
            "properties.proposed_graph.fields.schema_ref",
        )
    )

    case = copy.deepcopy(docs)
    case[PLAN_REVISION_CANDIDATE_SCHEMA_PATH]["candidate_rules"][
        "admission_must_bind_candidate_digest_and_proposed_graph_digest"
    ] = False
    cases.append(
        (
            "admission loses proposed graph digest binding",
            case,
            PLAN_REVISION_CANDIDATE_SCHEMA_PATH,
            "candidate_rules",
        )
    )

    case = copy.deepcopy(docs)
    case[PLAN_REVISION_CANDIDATE_SCHEMA_PATH]["semantic_rules"].remove(
        "revision_candidate_does_not_self_admit"
    )
    cases.append(
        (
            "candidate self-admission semantics",
            case,
            PLAN_REVISION_CANDIDATE_SCHEMA_PATH,
            "semantic_rules",
        )
    )

    case = copy.deepcopy(docs)
    case[METACOG_ANALYSIS_SCHEMA_PATH]["instance_semantics"]["output_authority"] = (
        "canonical"
    )
    cases.append(
        (
            "Meta-Planner output authority inflation",
            case,
            METACOG_ANALYSIS_SCHEMA_PATH,
            "instance_semantics",
        )
    )

    case = copy.deepcopy(docs)
    case[METACOG_ANALYSIS_SCHEMA_PATH]["properties"]["lessons"]["items"]["fields"][
        "authority_effect"
    ]["const"] = "strategic"
    cases.append(
        (
            "metacognitive lesson authority inflation",
            case,
            METACOG_ANALYSIS_SCHEMA_PATH,
            "properties.lessons.items.fields.authority_effect",
        )
    )

    case = copy.deepcopy(docs)
    case[METACOG_ANALYSIS_SCHEMA_PATH]["properties"]["findings"]["items"]["fields"][
        "kind"
    ]["enum"].append("strategic_decision")
    cases.append(
        (
            "metacognitive strategic-decision category",
            case,
            METACOG_ANALYSIS_SCHEMA_PATH,
            "properties.findings.items.fields.kind.enum",
        )
    )

    case = copy.deepcopy(docs)
    case[METACOG_ANALYSIS_SCHEMA_PATH]["analysis_rules"][
        "metacognitive_analysis_cannot_modify_or_supersede_strategic_plan"
    ] = False
    cases.append(
        (
            "metacognitive Plan mutation permission",
            case,
            METACOG_ANALYSIS_SCHEMA_PATH,
            "analysis_rules",
        )
    )

    case = copy.deepcopy(docs)
    case[STRATEGIC_PLAN_MODEL_PATH]["reasoning_concepts"]["affected_strategic_closure"][
        "representation_schema_ref"
    ] = "l9.schema/other@1"
    cases.append(
        (
            "Affected Closure semantic-owner schema drift",
            case,
            STRATEGIC_PLAN_MODEL_PATH,
            "reasoning_concepts.affected_strategic_closure",
        )
    )

    case = copy.deepcopy(docs)
    source_id = RC026_SOURCE_IDS[AFFECTED_CLOSURE_SCHEMA_PATH]
    case["semantics/canonical_sources.yaml"]["sources"] = [
        x
        for x in case["semantics/canonical_sources.yaml"]["sources"]
        if x.get("id") != source_id
    ]
    cases.append(
        (
            "canonical registration loss",
            case,
            "semantics/canonical_sources.yaml",
            "sources",
        )
    )

    case = copy.deepcopy(docs)
    filename = "strategic_planning_episode.schema.yaml"
    case["semantics/generic_compiler_manifest.yaml"]["requires"][
        "semantic_catalogs"
    ].remove(filename)
    case["semantics/generic_compiler_manifest.yaml"]["requires"][
        "artifact_schemas"
    ].append(filename)
    cases.append(
        (
            "compiler schema misclassification",
            case,
            "semantics/generic_compiler_manifest.yaml",
            "requires.semantic_catalogs",
        )
    )

    case = copy.deepcopy(docs)
    case[STRATEGIC_COGNITION_MODEL_PATH]["reasoning_artifacts"][
        "strategic_plan_metacognitive_analysis"
    ]["schema_ref"] = "l9.schema/other@1"
    cases.append(
        (
            "Meta-Planner semantic-owner schema drift",
            case,
            STRATEGIC_COGNITION_MODEL_PATH,
            "reasoning_artifacts.strategic_plan_metacognitive_analysis.schema_ref",
        )
    )

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc026(candidate, candidate_report)
        prefix = f"FAIL RC-026 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-026",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith(f"FAIL RC-026 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-026-NEG",
            f"{len(cases)} Strategic Planning cognition negative cases fail closed for their intended reason",
        )


def check_rc026(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    _evaluate_rc026(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-026",
            "Planner / Meta-Planner cognitive interfaces preserve exact source coordinates, workspace/Strategy separation, candidate admission binding, Meta-Planner advisory authority, semantic-owner anchors, and compiler/registry closure",
        )
        _check_rc026_negative_cases(docs, report)


# RC-027 cross-ledger reference closure. The byte-digest checks (SC-008,
# RC-001, RC-002, RC-011) are regenerated at every release, so a dangling
# contract or invariant reference introduced inside a release PR used to pass:
# no check resolved the references themselves (RC-017 pins only the validation
# contract's own invariants). RC-027 resolves the two typed reference lists a
# ledger may carry: ``contracts[*].source_invariants`` against invariants.yaml,
# and ``governed_by.contracts`` / ``governed_by.invariants`` against the two
# canonical catalogs. Anchor-form references (``<ledger>.yaml#path``) stay with
# the checks that pin them (RC-024 .. RC-026).
GOVERNED_BY_FIELD = "governed_by"
RC027_PROBE_CONTRACT_LEDGER = "semantics/product_kinds.yaml"
RC027_PROBE_INVARIANT_LEDGER = "semantics/strategic_plan_model.yaml"


def _rc027_declared_ids(
    docs: dict[str, dict], path: str, collection: str, report: Report
) -> set[str]:
    """Ids declared exactly once in ``path`` ``collection``.

    A missing or duplicate id is reported here: a reference can only resolve
    to exactly one canonical entry, so an ambiguous coordinate is a closure
    failure, not a resolved one.
    """
    declared: set[str] = set()
    for index, entry in enumerate(_list(_mapping(docs.get(path)).get(collection))):
        entry_id = _mapping(entry).get("id")
        label = f"{collection}[{index}].id"
        if not isinstance(entry_id, str) or not entry_id:
            report.fail(
                "RC-027",
                path,
                label,
                entry_id,
                "catalog entry declares no string id; no reference can resolve to it",
            )
        elif entry_id in declared:
            report.fail(
                "RC-027",
                path,
                label,
                entry_id,
                "duplicate catalog id; a reference to it would be ambiguous",
            )
        else:
            declared.add(entry_id)
    return declared


def _rc027_contract_citations(
    docs: dict[str, dict], invariant_ids: set[str], report: Report
) -> int:
    resolved = 0
    for index, entry in enumerate(
        _list(_mapping(docs.get(CONTRACTS_PATH)).get("contracts"))
    ):
        contract = _mapping(entry)
        label = f"contracts[{contract.get('id') or index}].source_invariants"
        cited = contract.get("source_invariants")
        if not isinstance(cited, list):
            report.fail(
                "RC-027",
                CONTRACTS_PATH,
                label,
                cited,
                "source_invariants must be a list of declared invariant ids",
            )
            continue
        for ref in cited:
            if isinstance(ref, str) and ref in invariant_ids:
                resolved += 1
            else:
                report.fail(
                    "RC-027",
                    CONTRACTS_PATH,
                    label,
                    ref,
                    "contract cites an invariant that invariants.yaml does not declare",
                )
    return resolved


def _rc027_governed_by(
    path: str,
    doc: dict,
    catalogs: tuple[tuple[str, set[str], str], ...],
    report: Report,
) -> int:
    """Resolve one ledger's ``governed_by`` reference lists; absent is legal."""
    if GOVERNED_BY_FIELD not in doc:
        return 0
    governed = doc.get(GOVERNED_BY_FIELD)
    if not isinstance(governed, dict):
        report.fail(
            "RC-027",
            path,
            GOVERNED_BY_FIELD,
            governed,
            f"{GOVERNED_BY_FIELD} must be a mapping; a present non-mapping value "
            "drops every governing reference",
        )
        return 0
    resolved = 0
    for field, declared, kind in catalogs:
        if field not in governed:
            continue
        refs = governed.get(field)
        label = f"{GOVERNED_BY_FIELD}.{field}"
        if not isinstance(refs, list):
            report.fail(
                "RC-027",
                path,
                label,
                refs,
                f"{label} must be a list of declared {kind} ids",
            )
            continue
        for ref in refs:
            if isinstance(ref, str) and ref in declared:
                resolved += 1
            else:
                report.fail(
                    "RC-027",
                    path,
                    label,
                    ref,
                    f"ledger is governed by a {kind} that the canonical catalog does not declare",
                )
    return resolved


def _evaluate_rc027(docs: dict[str, dict], report: Report) -> int:
    before = len(report.failures)
    invariant_ids = _rc027_declared_ids(docs, INVARIANTS_PATH, "invariants", report)
    contract_ids = _rc027_declared_ids(docs, CONTRACTS_PATH, "contracts", report)
    if not invariant_ids:
        report.fail(
            "RC-027",
            INVARIANTS_PATH,
            "invariants",
            None,
            "invariant catalog declares no ids; references cannot be resolved",
        )
    if not contract_ids:
        report.fail(
            "RC-027",
            CONTRACTS_PATH,
            "contracts",
            None,
            "contract catalog declares no ids; references cannot be resolved",
        )
    if len(report.failures) != before:
        # An empty, duplicated, or id-less catalog cannot resolve anything
        # unambiguously; do not count references against it.
        return 0
    catalogs = (
        ("contracts", contract_ids, "contract"),
        ("invariants", invariant_ids, "invariant"),
    )
    resolved = _rc027_contract_citations(docs, invariant_ids, report)
    for path, doc in sorted(docs.items()):
        resolved += _rc027_governed_by(path, _mapping(doc), catalogs, report)
    return resolved


def _check_rc027_negative_cases(docs: dict[str, dict], report: Report) -> None:
    cases: list[tuple[str, dict, str, str]] = []

    case = copy.deepcopy(docs)
    contract = _mapping(_list(case[CONTRACTS_PATH]["contracts"])[-1])
    contract["source_invariants"][0] = "L9-NOPE-999"
    cases.append(
        (
            "contract cites an undeclared invariant",
            case,
            CONTRACTS_PATH,
            f"contracts[{contract.get('id')}].source_invariants",
        )
    )

    case = copy.deepcopy(docs)
    case[RC027_PROBE_CONTRACT_LEDGER][GOVERNED_BY_FIELD]["contracts"][0] = (
        "l9.contract/nope@1"
    )
    cases.append(
        (
            "ledger governed by an undeclared contract",
            case,
            RC027_PROBE_CONTRACT_LEDGER,
            f"{GOVERNED_BY_FIELD}.contracts",
        )
    )

    case = copy.deepcopy(docs)
    case[RC027_PROBE_INVARIANT_LEDGER][GOVERNED_BY_FIELD]["invariants"][0] = (
        "L9-NOPE-999"
    )
    cases.append(
        (
            "ledger governed by an undeclared invariant",
            case,
            RC027_PROBE_INVARIANT_LEDGER,
            f"{GOVERNED_BY_FIELD}.invariants",
        )
    )

    case = copy.deepcopy(docs)
    case[RC027_PROBE_CONTRACT_LEDGER][GOVERNED_BY_FIELD]["contracts"] = (
        "l9.contract/product-kind@1"
    )
    cases.append(
        (
            "governed_by.contracts collapsed to a scalar",
            case,
            RC027_PROBE_CONTRACT_LEDGER,
            f"{GOVERNED_BY_FIELD}.contracts",
        )
    )

    case = copy.deepcopy(docs)
    case[RC027_PROBE_CONTRACT_LEDGER][GOVERNED_BY_FIELD] = "invalid"
    cases.append(
        (
            "governed_by replaced by a scalar",
            case,
            RC027_PROBE_CONTRACT_LEDGER,
            GOVERNED_BY_FIELD,
        )
    )

    case = copy.deepcopy(docs)
    contracts = case[CONTRACTS_PATH]["contracts"]
    contracts.append(copy.deepcopy(contracts[0]))
    cases.append(
        (
            "duplicate contract id admitted",
            case,
            CONTRACTS_PATH,
            f"contracts[{len(contracts) - 1}].id",
        )
    )

    case = copy.deepcopy(docs)
    invariants = case[INVARIANTS_PATH]["invariants"]
    invariants.append(copy.deepcopy(invariants[0]))
    cases.append(
        (
            "duplicate invariant id admitted",
            case,
            INVARIANTS_PATH,
            f"invariants[{len(invariants) - 1}].id",
        )
    )

    case = copy.deepcopy(docs)
    case[CONTRACTS_PATH]["contracts"] = []
    cases.append(("contract catalog emptied", case, CONTRACTS_PATH, "contracts"))

    for label, candidate, path, field in cases:
        candidate_report = Report()
        _evaluate_rc027(candidate, candidate_report)
        prefix = f"FAIL RC-027 {path} {field}="
        if not any(f.startswith(prefix) for f in candidate_report.failures):
            report.fail(
                "RC-027",
                VALIDATOR_PATH,
                "negative_case",
                label,
                f"negative case did not fail closed at {path} {field}",
            )
    if not any(
        f.startswith(f"FAIL RC-027 {VALIDATOR_PATH} negative_case")
        for f in report.failures
    ):
        report.ok(
            "RC-027-NEG",
            f"{len(cases)} cross-ledger reference negative cases fail closed at their intended field",
        )


def check_rc027(docs: dict[str, dict], report: Report) -> None:
    before = len(report.failures)
    resolved = _evaluate_rc027(docs, report)
    if len(report.failures) == before:
        report.ok(
            "RC-027",
            f"{resolved} typed cross-ledger references resolve: every contracts[*].source_invariants "
            "entry names a declared invariant and every governed_by.contracts / governed_by.invariants "
            "entry names a declared contract or invariant",
        )
        _check_rc027_negative_cases(docs, report)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--release",
        default=None,
        help="release record version under docs/semantic-foundation/ (default: highest)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not (root / "semantics").is_dir():
        print(f"FAIL SC-000 validator: {root} has no semantics/ directory")
        return 2
    report = Report()
    docs = check_sc001(root, report)
    check_sc002(root, docs, report)
    check_sc003(docs, report)
    check_sc004(root, docs, report)
    check_sc005(docs, report)
    check_sc006(docs, report)
    check_sc007(docs, report)
    check_sc008(root, args.release, report)
    check_derivation_sources(
        "RC-001", "semantics/capabilities.yaml", root, docs, report
    )
    check_derivation_sources("RC-002", "semantics/lifecycle.yaml", root, docs, report)
    check_derivation_sources(
        "RC-011", "semantics/receipt_catalog.yaml", root, docs, report
    )
    check_rc003(docs, report)
    check_rc004(docs, report)
    check_rc005(docs, report)
    check_rc006(docs, report)
    check_rc009(docs, report)
    check_rc012(docs, report)
    check_rc013(docs, report)
    check_rc014(docs, report)
    check_rc015(docs, report)
    check_rc016(docs, report)
    check_rc017(docs, report)
    check_rc018(docs, report)
    check_rc019(docs, report)
    check_rc020(docs, report)
    check_rc021(docs, report)
    check_rc022(docs, report)
    check_rc023(docs, report)
    check_rc024(docs, report)
    check_rc025(docs, report)
    check_rc026(docs, report)
    check_rc027(docs, report)
    for line in report.passes:
        print(line)
    for line in report.failures:
        print(line)
    print("PASS SC-009 validation was observational: no file was written")
    if report.failures:
        print(
            f"FAIL semantic-foundation closure: {len(report.failures)} unresolved (SC-010 fail-closed)"
        )
        return 1
    print("PASS SC-010 no unresolved references")
    print("PASS semantic-foundation closure")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
