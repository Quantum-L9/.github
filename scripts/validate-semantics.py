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
    "strategic_cognition",
    "strategic_plan",
    PLAN_KEEPER,
    METACOGNITIVE_REASONER,
    "current_meta_view",
)
STRATEGY_AUTHORITY_SOURCE = "explicitly_granted_strategic_authority"
STRATEGY_RESOLUTION_REF = "authority_model.yaml#strategic_cognition_authority"
STRATEGY_COMPILER_BOUNDARY_REF = "vocabulary.yaml#stage_rules.reasoning_plane_rule"
METACOGNITION_DENIED = {
    "strategic_plan_mutation",
    "strategic_plan_supersession",
    "strategic_authority",
}
# The Plan Keeper's admitted permissions, exactly. An allowlist, not a
# blocklist: any other grant is authority self-expansion and fails closed.
PLAN_KEEPER_MAY = {
    "revise_strategic_direction_within_explicitly_granted_strategic_authority",
    "consume_planning_cognition_lessons",
}
PLAN_KEEPER_MAY_NOT = {
    "acquire_truth_source_ownership_by_consuming_projections",
    "derive_authority_from_reasoning_capability",
    "become_execution_or_implementation_authority_by_implication",
    "revise_strategic_direction_beyond_granted_strategic_authority",
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
METACOGNITION_MAY = {
    "analyze_plan_keeper_reasoning_episodes",
    "compare_planning_reasoning_expectations_outcomes_and_revisions",
    "identify_recurring_planning_reasoning_strengths_and_failure_patterns",
    "emit_planning_cognition_lessons_for_plan_keeper",
}
# Model sections admitted by v3.8.0. Anything else (plan graph, runtime,
# prompts, actor bindings, capabilities, artifact classes) is out of scope.
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
            "authority.owner",
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
        "revise_strategic_direction_without_authority"
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
        "revise_strategic_direction_beyond_granted_strategic_authority"
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
            "authority.owner",
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
    "strategic_plan_owns_strategy_not_reality",
    "strategic_hypothesis_is_plan_owned_belief_not_authoritative_truth",
    "reality_change_may_require_reconsideration_but_never_directly_modifies_or_invalidates_strategic_plan",
    "reasoning_workspace_content_is_not_strategic_plan_content_without_authorized_decision",
    "planning_horizon_does_not_create_primitive_types",
    "compound_causal_claims_are_expressible_by_one_strategic_hypothesis",
    "outcome_of_one_primitive_does_not_establish_correctness_of_another",
}
PLAN_REUSED_CONCEPTS = {
    "objective": "vocabulary.yaml#terms.objective",
    "strategic_intent": "strategic_cognition_model.yaml#concepts.strategic_intent",
}
PLAN_CLOSURE = "affected_strategic_closure"
PLAN_CLOSURE_KEYS = {"definition", "purpose", "may_not"}
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
    authority = model.get("authority") or {}
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
            "authority.owner",
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
    sources = (docs.get(registry_path) or {}).get("sources") or []
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
    requires = (docs.get(manifest_path) or {}).get("requires") or {}
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
    governed = model.get("governed_by") or {}
    invariant_ids = {
        i.get("id")
        for i in (docs.get("semantics/invariants.yaml") or {}).get("invariants") or []
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
        for c in (docs.get(CONTRACTS_PATH) or {}).get("contracts") or []
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
            "concepts.strategic_plan",
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


def _rc018_representation(model: dict, report: Report) -> None:
    found: list[str] = []

    def walk(node: object, trail: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                path = f"{trail}.{key}" if trail else str(key)
                if str(key) in PLAN_REPRESENTATION_KEYS:
                    found.append(path)
                walk(value, path)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{trail}[{index}]")

    walk(model, "")
    if found:
        report.fail(
            "RC-018",
            PLAN_MODEL_PATH,
            "representation_keys",
            found,
            "Strategic Plan representation is not admitted by the semantic model",
        )


def _rc018_terms(docs: dict[str, dict], report: Report) -> None:
    terms = (docs.get(VOCABULARY_PATH) or {}).get("terms") or {}
    for term in PLAN_TERMS:
        if (terms.get(term) or {}).get("detailed_model") != PLAN_MODEL_NAME:
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
        ("Strategic Plan semantics owned by a store", case, model, "authority.owner")
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
            "concepts.strategic_plan",
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
            "concepts.strategic_plan",
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
