"""Structural tests for the source-class dispatch candidate pack. Candidate only.

Run from the repository root:

    python3 -m unittest discover -s docs/candidates/source-class-dispatch-v2/tests

The @1 records are read from this branch's semantics/, which the pack never
changes, so the tests need no git history.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

PACK = Path(__file__).resolve().parents[1]
REPO = PACK.parents[2]
SEMANTICS = REPO / "semantics"
PROTOCOL = {"protocol": "l9.payload-validation/source-class-dispatch@1"}
PAIRS = ("identity-assurance", "strategic-planning-context", "strategic-metacognition")
SYNTHESIZED = PAIRS
INFERRED = {"required", "const", "enum", "min_items"}
LEGACY_GRAMMAR = {"type", "properties", "fields", "required", "items", "const", "enum"}


def _manifest() -> dict:
    return json.loads((PACK / "MANIFEST.json").read_text("utf-8"))


def _load(path: Path):
    return yaml.safe_load(path.read_text("utf-8"))


def _overlay(name: str):
    return _load(PACK / "overlays" / name)


def _v1_projection(name: str) -> dict:
    records = _load(SEMANTICS / "projection_profiles.yaml")["projection_profiles"]
    return next(r for r in records if r["id"] == f"l9.projection/{name}@1")


def _v1_composition(name: str) -> dict:
    records = _load(SEMANTICS / "composition_profiles.yaml")["profiles"]
    return next(r for r in records if r["id"] == f"l9.compose/{name}@1")


def _keywords(descriptor: dict) -> set[str]:
    found = set(descriptor)
    for child in descriptor.get("fields", {}).values():
        found |= _keywords(child)
    if "items" in descriptor:
        found |= _keywords(descriptor["items"])
    return found


class ProfileOverlays(unittest.TestCase):
    def setUp(self) -> None:
        self.projections = {
            r["id"]: r for r in _overlay("projection_profile_additions.yaml")["records"]
        }
        self.compositions = {
            r["id"]: r
            for r in _overlay("composition_profile_additions.yaml")["records"]
        }
        self.restored = _overlay("projection_profile_additions.yaml")[
            "restored_source_classes"
        ]

    def test_projection_successor_differs_from_v1_only_as_declared(self) -> None:
        self.assertEqual(sorted(self.restored), sorted(PAIRS))
        self.assertEqual(sum(len(v) for v in self.restored.values()), 7)
        for name in PAIRS:
            v1 = _v1_projection(name)
            v2 = self.projections[f"l9.projection/{name}@2"]
            self.assertEqual(v2["successor_of"], v1["id"])
            self.assertEqual(v2["output"], {"schema": f"l9.projection.{name}/v2"})
            self.assertEqual(v2["payload_validation"], PROTOCOL)
            for cls, spec in v1["sources"].items():
                expected = list(spec["selectors"])
                if cls in self.restored[name]:
                    # Every @1 selector is kept, so PROJECTION-014 removes nothing.
                    expected.append("$")
                self.assertEqual(v2["sources"][cls]["selectors"], expected, (name, cls))
            rebuilt = copy.deepcopy(v2)
            for key in ("successor_of", "payload_validation"):
                rebuilt.pop(key)
            rebuilt["id"], rebuilt["output"], rebuilt["sources"] = (
                v1["id"],
                v1["output"],
                v1["sources"],
            )
            self.assertEqual(rebuilt, v1, name)

    def test_composition_successor_differs_from_v1_only_as_declared(self) -> None:
        for name in PAIRS:
            v1 = _v1_composition(name)
            v2 = self.compositions[f"l9.compose/{name}@2"]
            self.assertEqual(
                v2["composes"], {"projection_profile": f"l9.projection/{name}@2"}
            )
            self.assertEqual(
                v2["output"], {"schema": f"l9.composed-projection.{name}/v2"}
            )
            self.assertEqual(v2["payload_validation"], PROTOCOL)
            rebuilt = {k: v for k, v in v2.items() if k != "payload_validation"}
            rebuilt["id"], rebuilt["composes"], rebuilt["output"] = (
                v1["id"],
                v1["composes"],
                v1["output"],
            )
            self.assertEqual(rebuilt, v1, name)

    def test_successors_are_absent_from_semantics(self) -> None:
        text = (SEMANTICS / "projection_profiles.yaml").read_text("utf-8")
        text += (SEMANTICS / "composition_profiles.yaml").read_text("utf-8")
        self.assertNotIn("payload_validation", text)
        for name in PAIRS:
            self.assertNotIn(f"l9.projection/{name}@2", text)


class CandidateStatus(unittest.TestCase):
    def test_overlays_claim_no_admission(self) -> None:
        for path in sorted((PACK / "overlays").glob("*.yaml")):
            document = _load(path)
            self.assertEqual(document["status"], "candidate", path.name)
            self.assertEqual(document["admission"], "not_granted", path.name)

    def test_governance_documents_are_candidates(self) -> None:
        for name in PAIRS:
            pack = REPO / f"docs/candidates/schema-grammar-{name}-v2"
            documents = [
                pack / n for n in ("operation.yaml", "dialect.yaml", "bindings.yaml")
            ]
            documents += sorted((pack / "grammars").glob("*.yaml"))
            self.assertGreater(len(documents), 3, name)
            for path in documents:
                document = _load(path)
                self.assertEqual(document["approval_status"], "candidate", path)
                self.assertIs(document["canonical"], False, path)
                self.assertEqual(document["admission"], "not_granted", path)

    def test_grammars_infer_no_constraint(self) -> None:
        for name in PAIRS:
            for path in (
                REPO / f"docs/candidates/schema-grammar-{name}-v2/grammars"
            ).glob("*.yaml"):
                grammar = _load(path)["grammar"]
                self.assertFalse(_keywords(grammar) & INFERRED, path)


class RegisteredSchemas(unittest.TestCase):
    def test_registrations_are_source_specific_and_bound(self) -> None:
        projections = {
            r["id"]: r for r in _overlay("projection_profile_additions.yaml")["records"]
        }
        compositions = {
            r["id"]: r
            for r in _overlay("composition_profile_additions.yaml")["records"]
        }
        for name in SYNTHESIZED:
            for kind, profiles, profile_id, field in (
                (
                    "projection",
                    projections,
                    f"l9.projection/{name}@2",
                    "projection_profile_ref",
                ),
                (
                    "composition",
                    compositions,
                    f"l9.compose/{name}@2",
                    "composition_profile_ref",
                ),
            ):
                path = (
                    PACK
                    / "overlays/registered_schemas"
                    / f"{name.replace('-', '_')}_{kind}_v2.schema.yaml"
                )
                document = _load(path)
                self.assertFalse(set(document) & LEGACY_GRAMMAR, path.name)
                self.assertEqual(
                    document["schema"], "l9.source-class-payload-schema/v1"
                )
                self.assertEqual(document["admission"], "not_granted")
                self.assertEqual(document["payload_validation"], PROTOCOL)
                self.assertEqual(document["governed_by"], {field: profile_id})
                self.assertEqual(
                    document["schema_id"], profiles[profile_id]["output"]["schema"]
                )
                classes = list(projections[f"l9.projection/{name}@2"]["sources"])
                self.assertEqual(
                    [s["source_class"] for s in document["source_shapes"]], classes
                )

    def test_every_pair_has_both_registrations(self) -> None:
        names = {p.name for p in (PACK / "overlays/registered_schemas").glob("*.yaml")}
        expected = {
            f"{n.replace('-', '_')}_{kind}_v2.schema.yaml"
            for n in PAIRS
            for kind in ("projection", "composition")
        }
        self.assertEqual(names, expected)

    def test_semantics_manifest_names_no_candidate_registration(self) -> None:
        manifest = _load(SEMANTICS / "generic_compiler_manifest.yaml")
        registered = set(manifest["requires"]["artifact_schemas"])
        candidates = {
            p.name for p in (PACK / "overlays/registered_schemas").glob("*.yaml")
        }
        self.assertFalse(registered & candidates)


class Evidence(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads((PACK / "evidence/rehearsal.json").read_text("utf-8"))

    def test_synthesized_pairs_pass_end_to_end(self) -> None:
        for name in SYNTHESIZED:
            producer = self.report["pairs"][name]["producer"]
            self.assertEqual(
                (producer["project_exit"], producer["compose_exit"]), (0, 0)
            )
            receipts = [r for r in producer["receipts"].values() if "operation" in r]
            self.assertEqual(len(receipts), len(_v1_projection(name)["sources"]) + 1)
            for receipt in receipts:
                self.assertEqual(receipt["result"], "pass")
                self.assertEqual(receipt["coverage"], "complete")
                self.assertEqual(receipt["payload_schema"], "pass")
                self.assertEqual(
                    receipt["dispatch_basis"],
                    "verified_profile_output_schema_and_verified_source_class",
                )

    def test_restored_sources_keep_their_schema_field(self) -> None:
        restored = _overlay("projection_profile_additions.yaml")[
            "restored_source_classes"
        ]
        kept = [
            r["payload_schema_field"]
            for name in SYNTHESIZED
            for r in self.report["pairs"][name]["producer"]["receipts"].values()
            if r.get("payload_schema_field")
        ]
        self.assertEqual(len(kept), sum(len(restored[n]) for n in SYNTHESIZED))

    def test_every_pair_synthesized_without_a_diagnostic(self) -> None:
        for name in PAIRS:
            pair = self.report["pairs"][name]
            self.assertEqual(pair["synthesis"], "candidate_pair_produced", name)
            self.assertEqual(pair["synthesis_exit"], 0, name)
            self.assertNotIn("synthesis_diagnostic", pair)

    def test_rehearsal_executed_the_pinned_compiler(self) -> None:
        compiler = self.report["compiler"]
        self.assertEqual(compiler["revision"], _manifest()["compiler"]["revision"])
        # rehearse.py refuses to run unless this module came from --compiler-root.
        self.assertEqual(
            compiler["executed_module"], "src/l9_semantic_compiler/__init__.py"
        )

    def test_evidence_base_matches_the_pack_base(self) -> None:
        self.assertEqual(self.report["base"]["revision"], _manifest()["base_sha"])
        for name in ("projection_profile_additions.yaml", "vocabulary_additions.yaml"):
            self.assertEqual(_overlay(name)["base_sha"], _manifest()["base_sha"])

    def test_every_pack_grammar_compiled(self) -> None:
        written = {n: self.report["pairs"][n]["grammars_written"] for n in PAIRS}
        self.assertEqual(written, {n: len(_v1_projection(n)["sources"]) for n in PAIRS})
        self.assertTrue(
            all(not self.report["pairs"][n]["inexpressible"] for n in PAIRS)
        )


class Integrity(unittest.TestCase):
    def test_sha256sums_match(self) -> None:
        lines = (PACK / "SHA256SUMS.txt").read_text("utf-8").splitlines()
        self.assertTrue(lines)
        for line in lines:
            digest, rel = line.split("  ", 1)
            raw = (REPO / rel).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, rel)


class RehearsalGuards(unittest.TestCase):
    def setUp(self) -> None:
        spec = importlib.util.spec_from_file_location("rehearse", PACK / "rehearse.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.module.main([]), 0)

    def test_refuses_a_disposable_inside_this_checkout(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            self.module.main(["--disposable", str(PACK / "not-allowed")])
        self.assertIn("outside this checkout", str(caught.exception))

    def test_refuses_an_existing_directory(self) -> None:
        with (
            tempfile.TemporaryDirectory() as existing,
            self.assertRaises(SystemExit) as caught,
        ):
            self.module.main(["--disposable", existing])
        self.assertIn("must be new", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
