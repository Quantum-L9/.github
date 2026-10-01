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
