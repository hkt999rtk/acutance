from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_literal_parity_next_family import build_payload, render_markdown


class BuildLiteralParityNextFamilyTest(unittest.TestCase):
    def test_payload_selects_measured_oecf_family_and_keeps_separation(self) -> None:
        payload = build_payload(self.repo_root())

        self.assertEqual(payload["issue"], 71)
        self.assertEqual(
            payload["selected_family_id"],
            "literal_measured_oecf_on_sensor_comp",
        )
        self.assertIn("20260318_deadleaf_13b10", payload["storage_policy"]["golden_reference_roots"])
        for row in payload["candidates"]:
            for path in row["storage"]["fitted_profile_paths"]:
                self.assertFalse(path.startswith("20260318_deadleaf_13b10"))

    def test_markdown_mentions_required_sections(self) -> None:
        payload = build_payload(self.repo_root())
        markdown = render_markdown(payload)

        self.assertIn("# Literal Parity Next Family", markdown)
        self.assertIn("## Selected Route", markdown)
        self.assertIn("## Storage Separation", markdown)
        self.assertIn("literal/measured_oecf_on_sensor_comp", markdown)
        self.assertIn("literal/intrinsic_full_reference", markdown)
        self.assertIn("generic direct-method retunes", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
