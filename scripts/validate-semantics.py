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
    if len(report.failures) == before:
        report.ok(
            "SC-002",
            f"{len(sources)} registered canonical sources resolve to existing files with unique ids and paths",
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
    # field name). Pattern-level ``required_capabilities`` is not typed as a
    # capability reference by any registered ledger and is deliberately not
    # resolved here; resolving it would misread architectural traits as
    # capability identities.
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
        versions = (
            sorted(p.name for p in base.iterdir() if p.is_dir())
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
