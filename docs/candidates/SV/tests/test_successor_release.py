"""Identity selection of the successor-release machinery (owner decisions D4/D5)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "prepare_successor_release", ROOT / "tools" / "prepare_successor_release.py"
)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def checkout(releases, adrs):
    root = Path(tempfile.mkdtemp())
    for version in releases:
        (root / "docs" / "semantic-foundation" / version).mkdir(parents=True)
    (root / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    for number in adrs:
        (root / "docs" / "adr" / f"ADR-{number:03d}-x.md").write_text("x")
    (root / "docs" / "adr" / "README.md").write_text("x")
    return root


class Selection(unittest.TestCase):
    def test_merged_state_alone_selects_the_next_identity(self):
        sel = tool.select(checkout(["v3.28.0", "v3.29.0", "v3.9.0"], range(1, 27)), [])
        self.assertEqual(
            (sel["predecessor"], sel["version"], sel["adr"]),
            ("v3.29.0", "v3.30.0", "ADR-027"),
        )

    def test_queued_claims_are_skipped_not_reused(self):
        sel = tool.select(
            checkout(["v3.29.0"], range(1, 27)), ["v3.30.0:ADR-027", "v3.31.0:ADR-028"]
        )
        self.assertEqual((sel["version"], sel["adr"]), ("v3.32.0", "ADR-029"))
        self.assertEqual(
            (sel["merged_next_version"], sel["merged_next_adr"]), ("v3.30.0", "ADR-027")
        )

    def test_after_the_queue_merges_selection_follows_merged_state(self):
        merged = checkout(["v3.29.0", "v3.30.0", "v3.31.0"], range(1, 29))
        self.assertEqual(tool.select(merged, [])["version"], "v3.32.0")
        self.assertEqual(tool.select(merged, [])["adr"], "ADR-029")

    def test_malformed_queue_claim_is_refused(self):
        with self.assertRaises(tool.Refused):
            tool.select(checkout(["v3.29.0"], [1]), ["v3.30.0"])

    def test_adr_ranges_render_gaps_honestly(self):
        self.assertEqual(tool.adr_ranges([1, 2, 3]), "ADR-001 through ADR-003")
        self.assertEqual(
            tool.adr_ranges([1, 2, 3, 6]), "ADR-001 through ADR-003 and ADR-006"
        )


if __name__ == "__main__":
    unittest.main()
