"""Tests for ops/admit-profiles.py: the real tool against fixture catalogs and a copy of this tree."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "admit_profiles", ROOT / "ops" / "admit-profiles.py"
)
assert spec is not None and spec.loader is not None
ap = importlib.util.module_from_spec(spec)
sys.modules["admit_profiles"] = ap
spec.loader.exec_module(ap)

ARCHETYPE = "l9.node-archetype/authoritative-state@1"
SCOPE = {"product_kind": "node", "archetype_ref": ARCHETYPE}
REVISION = "a" * 40


def profile_id(cls: str) -> str:
    return f"l9.fixture-profile/fixture-{cls}@1"


def make_catalog(
    base: Path, *, unresolved: bool = False, membership: bool = True
) -> Path:
    cat = base / "l9-conformance"
    (cat / "catalog").mkdir(parents=True)
    entries = []
    for cls in ("core", "adapter"):
        rel = f"catalog/fixture-{cls}-1.yaml"
        body = {
            "schema": "l9-conformance/fixture-profile@1",
            "id": profile_id(cls),
            "status": "candidate",
            "conformance_class": cls,
            "scope": SCOPE,
            "membership": [f"l9.fixture/{cls}@1"] if membership else [],
        }
        if unresolved:
            body["unresolved"] = [
                {
                    "id": f"U-{cls.upper()}-1",
                    "kind": "obligation_content",
                    "statement": f"No law defines class {cls}.",
                    "resolution_requires": "canonical law",
                }
            ]
        (cat / rel).write_text(yaml.safe_dump(body, sort_keys=False))
        digest = "sha256:" + hashlib.sha256((cat / rel).read_bytes()).hexdigest()
        entries.append(
            {
                "id": profile_id(cls),
                "path": rel,
                "digest": digest,
                "status": "candidate",
            }
        )
    (cat / ap.CATALOG_INDEX).write_text(yaml.safe_dump({"profiles": entries}))
    return cat


def make_requirements(base: Path, refs: dict[str, str | None]) -> Path:
    path = base / "birth-requirements.json"
    path.write_text(
        json.dumps(
            {
                "schema": ap.REQUIREMENTS_SCHEMA,
                "product_ref": "l9.fixture",
                "conformance": {
                    "required": True,
                    "admission_candidates": [
                        {"conformance_class": cls, "scope": SCOPE, "profile_ref": ref}
                        for cls, ref in refs.items()
                    ],
                },
            }
        )
    )
    return path


ALL = {"core": profile_id("core"), "adapter": profile_id("adapter")}


class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _check(self, catalog: Path, refs: dict[str, str | None], admitted=()) -> dict:
        _, candidates = ap.load_candidates(make_requirements(self.tmp, refs))
        return ap.check(candidates=candidates, catalog=catalog, admitted=list(admitted))

    def test_specified_catalog_profiles_are_admissible(self) -> None:
        report = self._check(make_catalog(self.tmp), ALL)
        self.assertEqual(report["status"], "admissible")
        self.assertEqual([e["id"] for e in report["admissible"]], list(ALL.values()))
        self.assertEqual(
            report["admissible"][0]["distribution_repository"], ap.CATALOG_REPOSITORY
        )

    def test_every_unresolved_entry_is_reported_as_underspecified(self) -> None:
        report = self._check(make_catalog(self.tmp, unresolved=True), ALL)
        self.assertEqual(report["status"], "refused")
        self.assertEqual(
            [
                (g["conformance_class"], g["code"], g["unknown_id"])
                for g in report["gaps"]
            ],
            [
                ("core", "underspecified", "U-CORE-1"),
                ("adapter", "underspecified", "U-ADAPTER-1"),
            ],
        )
        self.assertEqual(report["admissible"], [])

    def test_undeclared_unknown_and_tampered_profiles_are_gaps(self) -> None:
        catalog = make_catalog(self.tmp)
        (catalog / "catalog/fixture-adapter-1.yaml").write_text("tampered: true\n")
        report = self._check(
            catalog, {"core": None, "adapter": profile_id("adapter"), "runtime": "x@1"}
        )
        self.assertEqual(
            [g["code"] for g in report["gaps"]],
            ["identity_undeclared", "digest_mismatch", "not_in_catalog"],
        )

    def test_empty_membership_is_a_gap(self) -> None:
        report = self._check(
            make_catalog(self.tmp, membership=False), {"core": profile_id("core")}
        )
        self.assertEqual([g["code"] for g in report["gaps"]], ["membership_empty"])

    def test_an_admitted_profile_at_another_digest_is_never_rewritten(self) -> None:
        report = self._check(
            make_catalog(self.tmp),
            {"core": profile_id("core")},
            admitted=[{"id": profile_id("core"), "digest": "sha256:" + "0" * 64}],
        )
        self.assertEqual(
            [g["code"] for g in report["gaps"]], ["admitted_profile_changed"]
        )

    def test_an_identically_admitted_profile_is_present(self) -> None:
        catalog = make_catalog(self.tmp)
        first = self._check(catalog, {"core": profile_id("core")})
        report = self._check(
            catalog, {"core": profile_id("core")}, admitted=first["admissible"]
        )
        self.assertEqual(
            (report["status"], report["present"]), ("admissible", [profile_id("core")])
        )

    def test_malformed_requirements_are_unresolved(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"schema": "other"}))
        with self.assertRaises(ap.AdmissionInputError):
            ap.load_candidates(bad)

    def test_cli_exit_codes(self) -> None:
        catalog = make_catalog(self.tmp, unresolved=True)
        args = ["check", "--requirements", str(make_requirements(self.tmp, ALL))]
        args += [
            "--catalog",
            str(catalog),
            "--catalog-revision",
            REVISION,
            "--checkout",
            str(ROOT),
        ]
        self.assertEqual(ap.main(args), 1)
        self.assertEqual(
            ap.main(
                [*args[:-4], "--catalog-revision", "short", "--checkout", str(ROOT)]
            ),
            2,
        )


class ApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.checkout = self.tmp / "github"
        shutil.copytree(ROOT, self.checkout, ignore=shutil.ignore_patterns(".git"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_apply_adds_the_ledger_entries_and_a_validated_candidate_release(
        self,
    ) -> None:
        catalog = make_catalog(self.tmp)
        result = ap.apply(
            requirements=make_requirements(self.tmp, ALL),
            catalog=catalog,
            catalog_revision=REVISION,
            checkout=self.checkout,
        )
        self.assertEqual(result["status"], "proposed")
        admitted = {e["id"]: e for e in ap.ledger_entries(self.checkout)}
        for ref in ALL.values():
            self.assertIn(ref, admitted)
        release = self.checkout / ap.RELEASES_PATH / result["release"]
        self.assertIn(ap.STATUS, (release / "README.md").read_text())
        self.assertIn(ap.LEDGER_PATH, result["changed_paths"])
        again = ap.apply(
            requirements=make_requirements(self.tmp, ALL),
            catalog=catalog,
            catalog_revision=REVISION,
            checkout=self.checkout,
        )
        self.assertEqual(again["status"], "present")

    def test_apply_refuses_an_underspecified_profile_and_writes_nothing(self) -> None:
        before = (self.checkout / ap.LEDGER_PATH).read_text()
        requirements = make_requirements(self.tmp, ALL)
        catalog = make_catalog(self.tmp, unresolved=True)
        with self.assertRaises(ap.AdmissionRefused):
            ap.apply(
                requirements=requirements,
                catalog=catalog,
                catalog_revision=REVISION,
                checkout=self.checkout,
            )
        self.assertEqual((self.checkout / ap.LEDGER_PATH).read_text(), before)

    def test_cli_refuses_a_requirements_path_outside_allowed_roots(self) -> None:
        self.assertEqual(
            ap.main(
                [
                    "check",
                    "--requirements",
                    "/etc/passwd",
                    "--catalog",
                    str(self.tmp),
                    "--catalog-revision",
                    REVISION,
                    "--checkout",
                    str(self.checkout),
                ]
            ),
            2,
        )

    def test_catalog_index_path_cannot_escape_the_catalog(self) -> None:
        with self.assertRaises(ap.AdmissionInputError):
            ap._confined(self.tmp, "../../etc/passwd", "catalog profile")


if __name__ == "__main__":
    unittest.main()
