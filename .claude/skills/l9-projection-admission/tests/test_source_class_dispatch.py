"""Registration and downstream checks for source-class payload schemas (compiler 0.10.0).

A profile that declares `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`
resolves its output schema through a `l9.source-class-payload-schema/v1` registration whose
identity is its own `schema_id`. These tests swap the fixture's x pair to that protocol and
move one fact at a time; the legacy fixture stays covered by the other modules.
"""

import json
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_admission_closure as cac
import verify_admission_evidence as vae
from test_check_admission_closure import (
    CANDIDATE,
    COMPOSITION,
    LEDGERS,
    PROFILE,
    PROFILES_HEAD,
    _Fixture,
)

PROTOCOL = "  payload_validation:\n    protocol: l9.payload-validation/source-class-dispatch@1\n"
DESCRIPTOR = {
    "type": "object",
    "additional_properties": False,
    "required": ["value"],
    "fields": {
        "value": {"type": "integer"},
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "additional_properties": False,
                "fields": {"id": {"type": "string"}, "v": {"type": "integer"}},
            },
        },
    },
}


def registration(kind: str, identity: str, profile_ref: str, **overrides) -> str:
    doc = {
        "schema": cac.SOURCE_CLASS_SCHEMA,
        "canonical": True,
        "artifact_id": f"l9.schema/x-{kind}@1",
        "authority": {"owner": "Quantum-L9/.github"},
        "schema_id": identity,
        "document_kind": f"{kind}_payload_schema",
        "payload_validation": dict(cac.SOURCE_CLASS_DISPATCH),
        "descriptor_dialect": "l9.schema-dialect/candidate-v2@1",
        "governed_by": {f"{kind}_profile_ref": profile_ref},
        "source_shapes": [
            {
                "source_class": "x_model",
                "source_ref": "l9.source/x-model@1",
                "descriptor": DESCRIPTOR,
            }
        ],
    }
    doc.update(overrides)
    return json.dumps({k: v for k, v in doc.items() if v is not None})


class _Dispatch(_Fixture):
    def setUp(self):
        super().setUp()
        # Registration happens before admission: a candidate release, so the x pair is not
        # an admitted version being edited in place (PROJECTION-013).
        self.rebuild(status=CANDIDATE)

    def use_protocol(self, *, projection=True, composition=True, **schema):
        profile = PROFILE + (PROTOCOL if projection else "")
        compose = COMPOSITION + (PROTOCOL if composition else "")
        self.repo.write(
            "semantics/projection_profiles.yaml",
            PROFILES_HEAD + "projection_profiles:\n" + profile,
        )
        self.repo.write("semantics/composition_profiles.yaml", "profiles:\n" + compose)
        self.repo.write(
            "semantics/x_projection.schema.yaml",
            registration(
                "projection",
                "l9.projection.x/v1",
                "l9.projection/x@1",
                **schema.get("projection_schema", {}),
            ),
        )
        self.repo.write(
            "semantics/x_composition.schema.yaml",
            registration(
                "composition",
                "l9.composed-projection.x/v1",
                "l9.compose/x@1",
                **schema.get("composition_schema", {}),
            ),
        )

    def gaps(self) -> list[str]:
        return self.verdict()["registration"]["gaps"]


class Registration(_Dispatch):
    def test_source_class_registration_registers(self):
        self.use_protocol()
        self.assertEqual(self.gaps(), [])

    def test_identity_is_schema_id_not_a_payload_marker(self):
        self.use_protocol()
        registry = cac.schema_registry(cac.Tree(self.repo.root, None))
        self.assertEqual(
            registry["consts"]["l9.projection.x/v1"], ["x_projection.schema.yaml"]
        )

    def test_protocol_on_a_legacy_schema_is_refused(self):
        self.use_protocol()
        self.repo.write(
            "semantics/x_projection.schema.yaml", LEDGERS["x_projection.schema.yaml"]
        )
        self.assertTrue(
            any("is not a l9.source-class-payload-schema/v1" in g for g in self.gaps())
        )

    def test_source_class_schema_without_the_protocol_is_refused(self):
        self.use_protocol(projection=False, composition=False)
        gaps = self.gaps()
        self.assertTrue(any("declares no payload_validation" in g for g in gaps))

    def test_unsupported_protocol_is_refused(self):
        self.use_protocol()
        profiles = self.repo.read("semantics/projection_profiles.yaml").replace(
            "source-class-dispatch@1", "source-class-dispatch@2"
        )
        self.repo.write("semantics/projection_profiles.yaml", profiles)
        self.assertTrue(
            any("is not a protocol compiler 0.10.0" in g for g in self.gaps())
        )

    def test_shape_coverage_must_equal_the_profile_classes(self):
        self.use_protocol(
            projection_schema={
                "source_shapes": [
                    {
                        "source_class": "other",
                        "source_ref": "l9.source/x-model@1",
                        "descriptor": DESCRIPTOR,
                    }
                ]
            }
        )
        self.assertTrue(any("not exactly ['x_model']" in g for g in self.gaps()))

    def test_shape_bound_to_another_source_is_refused(self):
        self.use_protocol(
            projection_schema={
                "source_shapes": [
                    {
                        "source_class": "x_model",
                        "source_ref": "l9.source/invariants@1",
                        "descriptor": DESCRIPTOR,
                    }
                ]
            }
        )
        self.assertTrue(any("not the registered source" in g for g in self.gaps()))

    def test_legacy_union_grammar_is_refused(self):
        self.use_protocol(projection_schema={"properties": {"schema": {"const": "x"}}})
        self.assertTrue(any("legacy union grammar" in g for g in self.gaps()))

    def test_missing_schema_id_is_refused(self):
        self.use_protocol(projection_schema={"schema_id": None})
        self.assertTrue(any("no schema_id declared" in g for g in self.gaps()))

    def test_wrong_document_kind_is_refused(self):
        self.use_protocol(
            projection_schema={"document_kind": "composition_payload_schema"}
        )
        self.assertTrue(
            any("not a projection_payload_schema" in g for g in self.gaps())
        )

    def test_composition_must_compose_a_dispatching_projection(self):
        self.use_protocol(projection=False)
        self.repo.write(
            "semantics/x_projection.schema.yaml", LEDGERS["x_projection.schema.yaml"]
        )
        self.assertTrue(
            any(
                "does not declare the same payload_validation" in g for g in self.gaps()
            )
        )

    def test_one_identity_declared_by_both_shapes_is_ambiguous(self):
        self.use_protocol()
        self.repo.write(
            "semantics/x_projection_copy.schema.yaml",
            LEDGERS["x_projection.schema.yaml"],
        )
        manifest = self.repo.read("semantics/generic_compiler_manifest.yaml").replace(
            "x_composition.schema.yaml]",
            "x_composition.schema.yaml, x_projection_copy.schema.yaml]",
        )
        self.repo.write("semantics/generic_compiler_manifest.yaml", manifest)
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn(
            "l9.projection.x/v1 is declared by 2 registered schemas",
            "\n".join(report["registration"]["gaps"]),
        )


class DownstreamDispatch(unittest.TestCase):
    """The verifier picks the descriptor from the verified source class, never the payload."""

    SCHEMA = json.loads(registration("projection", "l9.projection.x/v1", "p"))
    COMPOSED = json.loads(
        registration("composition", "l9.composed-projection.x/v1", "c")
    )

    def run_gaps(self, payload, schema, source):
        calls = []

        def fake(compiler_src, batch):
            calls.extend(batch)
            return [[] for _ in batch]

        with unittest.mock.patch.object(vae, "native_strict_violations", fake):
            gaps = vae._schema_gaps("ref", payload, schema, Path("/c"), source=source)
        return gaps, calls

    def test_projection_uses_its_verified_source_class_shape(self):
        payload = {"schema": "l9.x-model/v1", "value": 1}
        gaps, calls = self.run_gaps(
            payload, self.SCHEMA, ("x_model", "l9.source/x-model@1")
        )
        self.assertEqual(gaps, [])
        self.assertEqual(calls, [(payload, DESCRIPTOR)])

    def test_source_identity_outside_the_schema_is_a_gap(self):
        gaps, calls = self.run_gaps(
            {"value": 1}, self.SCHEMA, ("x_model", "l9.source/other@1")
        )
        self.assertEqual(calls, [])
        self.assertIn("is not a source shape", gaps[0])

    def test_composition_checks_exact_namespaces_each_by_its_shape(self):
        gaps, calls = self.run_gaps({"x_model": {"value": 1}}, self.COMPOSED, None)
        self.assertEqual((gaps, calls), ([], [({"value": 1}, DESCRIPTOR)]))
        gaps, calls = self.run_gaps({"x_model": {}, "extra": {}}, self.COMPOSED, None)
        self.assertEqual(calls, [])
        self.assertIn("are not exactly the schema's source classes", gaps[0])

    def test_interpreter_findings_are_reported(self):
        def fake(compiler_src, batch):
            return [["STRUCTURAL_VALIDATION_FAILED: mismatch"] for _ in batch]

        with unittest.mock.patch.object(vae, "native_strict_violations", fake):
            gaps = vae._schema_gaps(
                "ref",
                {"value": "x"},
                self.SCHEMA,
                Path("/c"),
                source=("x_model", "l9.source/x-model@1"),
            )
        self.assertEqual(
            gaps,
            [
                "ref: payload schema (native strict, x_model): STRUCTURAL_VALIDATION_FAILED: mismatch"
            ],
        )

    def test_a_compiler_without_the_strict_interpreter_is_unresolved(self):
        with self.assertRaises(cac.InputError):
            vae.native_strict_violations(Path("/nonexistent"), [({}, DESCRIPTOR)])


if __name__ == "__main__":
    unittest.main()
