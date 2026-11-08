"""Tests for discover_admission_subject.py: deterministic discovery and scope closure."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_admission_closure as cac
import discover_admission_subject as das
from test_check_admission_closure import CANDIDATE, LEDGERS, SUBJECT, _Fixture


class Discovery(_Fixture):
    def discover(self, candidate=None):
        base = das.admitted_base(
            self.repo.root, cac.Tree(self.repo.root, "origin/main")
        )
        return das.discover(
            self.repo.root, base["tree"], cac.Tree(self.repo.root, candidate)
        )

    def add_invariant(self, ident="L9-X-002"):
        self.repo.write(
            "semantics/invariants.yaml",
            self.repo.read("semantics/invariants.yaml")
            + f"- id: {ident}\n  statement: {ident} holds\n  scope: global\n  owner: o\n",
        )

    def test_admitted_base_is_the_verified_admission_commit(self):
        base = das.admitted_base(
            self.repo.root, cac.Tree(self.repo.root, "origin/main")
        )
        self.assertEqual(base["release"], "v1.0.0")
        self.assertEqual(base["admission_commit"], self.repo.git("rev-parse", "HEAD"))

    def test_nothing_changed_discovers_nothing(self):
        found = self.discover()
        self.assertEqual(found["status"], "pass", found["gaps"])
        self.assertFalse(any(found["admission_subjects"].values()))

    def test_new_invariant_is_discovered_without_changing_its_host_ledger(self):
        self.add_invariant()
        found = self.discover()
        self.assertEqual(found["admission_subjects"]["invariants"], ["L9-X-002"])
        # invariants.yaml changed, but only inside its hosted collection.
        self.assertEqual(found["admission_subjects"]["canonical_sources"], [])
        self.assertEqual(found["revisions"], [])

    def test_changed_identity_needs_a_declared_revision(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("purpose: x", "purpose: changed"),
        )
        found = self.discover()
        self.assertEqual(
            found["identities"]["contracts"]["changed"], ["l9.contract/x@1"]
        )
        self.assertEqual(found["revisions"], ["contracts:l9.contract/x@1"])

    def test_model_ledger_content_change_is_a_subject_without_a_revision(self):
        self.repo.write("semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "more: 1\n")
        found = self.discover()
        self.assertEqual(
            found["admission_subjects"]["canonical_sources"], ["l9.source/x-model@1"]
        )
        self.assertEqual(found["revisions"], [])

    def test_derivation_only_change_is_a_derived_coordinate_not_a_subject(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"] + "derivation:\n  source_digest_sha256: abc\n",
        )
        found = self.discover()
        self.assertFalse(any(found["admission_subjects"].values()), found)
        self.assertEqual(
            found["changed_derived_coordinates"],
            [
                {
                    "file": "semantics/contracts.yaml",
                    "path": "$.derivation.source_digest_sha256",
                }
            ],
        )

    def test_governing_text_inside_derivation_is_meaning_not_a_coordinate(self):
        # Review finding 6: a `derivation.rule` rewrite was hidden as a derived coordinate.
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"]
            + "derivation:\n  rule: every x is now forbidden\n",
        )
        found = self.discover()
        self.assertEqual(
            found["admission_subjects"]["canonical_sources"], ["l9.source/contracts@1"]
        )
        self.assertEqual(found["changed_derived_coordinates"], [])

    def test_removed_identity_fails_closure(self):
        self.repo.write("semantics/vocabulary.yaml", "terms: {}\n")
        found = self.discover()
        self.assertEqual(found["status"], "fail")
        self.assertIn("vocabulary_terms x_term: removed", "\n".join(found["gaps"]))

    def test_unclassified_semantics_file_fails_closure(self):
        self.repo.write("semantics/compiler_contract.yaml", "rules: {a: 1}\n")
        found = self.discover()
        self.assertIn("semantics/compiler_contract.yaml", found["unclassified_changes"])
        self.assertEqual(found["status"], "fail")

    def test_profile_edited_in_place_fails_closure(self):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace(
                "purpose: project x", "purpose: y"
            ),
        )
        found = self.discover()
        self.assertIn("immutable (PROJECTION-013)", "\n".join(found["gaps"]))

    def test_successor_profile_is_new_and_reported_superseding(self):
        successor = (
            "- id: l9.projection/x@2\n  class: consumer\n  consumer: x-consumer\n"
            "  purpose: x again\n  successor_of: l9.projection/x@1\n  sources:\n"
            "    x_model:\n      selectors: [$.value]\n  output:\n    schema: l9.projection.x/v1\n"
        )
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"] + successor,
        )
        found = self.discover()
        self.assertEqual(
            found["admission_subjects"]["projection_profiles"], ["l9.projection/x@2"]
        )
        self.assertEqual(
            found["superseded"],
            [{"profile": "l9.projection/x@2", "successor_of": "l9.projection/x@1"}],
        )
        deps = {d["dependency"]: d["state"] for d in found["required_dependencies"]}
        self.assertEqual(deps["projection_profiles:l9.projection/x@1"], "admitted")
        self.assertEqual(deps["source_classes:x_model"], "admitted")

    def test_dependency_that_does_not_resolve_fails_closure(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"]
            + "- id: l9.contract/y@1\n  purpose: y\n  scope: g\n  owner: o\n"
            "  source_invariants: [L9-NOPE-001]\n",
        )
        found = self.discover()
        self.assertIn(
            "contracts:l9.contract/y@1 depends on invariants:L9-NOPE-001, which does not "
            "resolve in the candidate",
            found["gaps"],
        )

    def test_discovery_is_deterministic(self):
        self.add_invariant()
        first, second = self.discover(), self.discover()
        self.assertEqual(
            json.dumps(das.public(first), sort_keys=True),
            json.dumps(das.public(second), sort_keys=True),
        )


class NamedBase(Discovery):
    """A release main admitted but the verifier rejects is measured from, never waived."""

    def admit_v11_without_target_row(self):
        self.add_invariant("L9-Y-001")
        self.repo.admit("v1.1.0", 2, ["L9-Y-001"], target_row=False)
        return self.repo.commit("admit v1.1.0")

    def main_tree(self):
        return cac.Tree(self.repo.root, "origin/main")

    def test_unverified_release_is_skipped_by_admitted_base(self):
        self.admit_v11_without_target_row()
        base = das.admitted_base(self.repo.root, self.main_tree())
        self.assertEqual(base["release"], "v1.0.0")
        self.assertIn("target authority class", base["tried"][0]["reason"])

    def test_named_base_measures_from_it_and_reports_its_gaps(self):
        commit = self.admit_v11_without_target_row()
        base = das.named_admitted_base(self.repo.root, self.main_tree(), "v1.1.0")
        self.assertEqual(
            (base["release"], base["admission_commit"]), ("v1.1.0", commit)
        )
        self.assertEqual(base["verified_base"], "v1.0.0")
        self.assertTrue(
            any("target authority class" in g for g in base["verification_gaps"])
        )
        found = das.discover(self.repo.root, base["tree"], cac.Tree(self.repo.root))
        # L9-Y-001 was admitted by v1.1.0, so it is not this candidate's subject.
        self.assertFalse(any(found["admission_subjects"].values()))

    def test_named_base_must_be_admitted(self):
        self.add_invariant("L9-Y-001")
        self.repo.release("v1.1.0", CANDIDATE)
        self.repo.commit("candidate v1.1.0")
        with self.assertRaises(cac.InputError):
            das.named_admitted_base(self.repo.root, self.main_tree(), "v1.1.0")

    def test_named_base_cannot_be_older_than_the_verified_base(self):
        self.add_invariant("L9-Y-001")
        self.repo.admit("v1.1.0", 2, ["L9-Y-001"])
        self.repo.commit("admit v1.1.0")
        with self.assertRaises(cac.InputError):
            das.named_admitted_base(self.repo.root, self.main_tree(), "v1.0.0")

    def test_closure_gate_scopes_from_the_named_base(self):
        self.admit_v11_without_target_row()
        self.add_invariant("L9-Y-002")
        self.candidate("v1.2.0")
        subject = self.subject(invariants=["L9-Y-002"])
        report = self.verdict(subject, admitted_base_version="v1.1.0")
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE", report.get("scope"))
        self.assertTrue(report["admitted_base"]["verification_gaps"])
        # Measured from the verified v1.0.0, v1.1.0's own L9-Y-001 is an omitted subject.
        self.assertEqual(self.verdict(subject)["verdict"], "REGISTERED")

    def test_command_line_named_base(self):
        self.admit_v11_without_target_row()
        main = ["--checkout", str(self.repo.root)]
        self.assertEqual(das.main([*main, "--admitted-base", "v1.1.0"]), 0)
        self.assertEqual(
            das.main([*main, "--admitted-base", "v1.1.0", "--base", "HEAD"]), 2
        )


class Scope(Discovery):
    def declared(self, **items):
        return cac.load_subject(self._subject({"schema": cac.SUBJECT_SCHEMA, **items}))

    def test_omitted_subject_fails(self):
        self.add_invariant()
        self.add_invariant("L9-X-003")
        scope = das.scope_check(self.discover(), self.declared(invariants=["L9-X-002"]))
        self.assertEqual(scope["omitted"], ["invariants:L9-X-003"])
        self.assertEqual(scope["status"], "fail")

    def test_declared_revision_that_changes_nothing_fails(self):
        scope = das.scope_check(
            self.discover(),
            self.declared(invariants=["L9-X-001"], revisions=["invariants:L9-X-001"]),
        )
        self.assertIn("does not change an admitted identity", "\n".join(scope["gaps"]))

    def test_declaring_an_admitted_dependency_is_informational(self):
        self.add_invariant()
        scope = das.scope_check(
            self.discover(), self.declared(invariants=["L9-X-002", "L9-X-001"])
        )
        self.assertEqual(scope["status"], "pass", scope["gaps"])
        self.assertEqual(scope["declared_already_admitted"], ["invariants:L9-X-001"])

    def test_generated_subject_passes_its_own_scope(self):
        self.add_invariant()
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("purpose: x", "purpose: changed"),
        )
        found = self.discover()
        path = self.tmp / "generated.json"
        path.write_text(json.dumps(das.subject_document(found)))
        scope = das.scope_check(found, cac.load_subject(path))
        self.assertEqual(scope["status"], "pass", scope["gaps"])


class CommandLine(Discovery):
    def run_main(self, *args):
        return das.main(["--checkout", str(self.repo.root), *args])

    def test_write_subject_then_declare_it(self):
        self.add_invariant()
        out = self.tmp / "out.json"
        self.assertEqual(self.run_main("--write-subject", str(out)), 0)
        written = json.loads(out.read_text())
        self.assertEqual(written["invariants"], ["L9-X-002"])
        self.assertEqual(self.run_main("--declared", str(out)), 0)

    def test_incomplete_declaration_exits_one(self):
        self.add_invariant()
        self.add_invariant("L9-X-003")
        path = self._subject({"schema": cac.SUBJECT_SCHEMA, "invariants": ["L9-X-002"]})
        self.assertEqual(self.run_main("--declared", str(path)), 1)

    def test_explicit_base_ref_and_candidate_ref(self):
        self.add_invariant()
        self.repo.release("v1.1.0", CANDIDATE)
        self.repo.commit("candidate")
        self.assertEqual(self.run_main("--base", "HEAD~1", "--candidate", "HEAD"), 0)

    def test_nothing_to_write_is_unresolved(self):
        self.assertEqual(self.run_main("--write-subject", str(self.tmp / "x.json")), 2)

    def test_unknown_base_is_unresolved(self):
        self.assertEqual(self.run_main("--base", "no-such-ref"), 2)

    def test_whole_fixture_subject_is_already_admitted(self):
        path = self._subject(SUBJECT)
        self.assertEqual(self.run_main("--declared", str(path)), 0)


if __name__ == "__main__":
    unittest.main()
