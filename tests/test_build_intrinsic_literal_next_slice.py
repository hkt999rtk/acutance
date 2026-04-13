from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_literal_next_slice import (
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicLiteralNextSliceTest(unittest.TestCase):
    def test_payload_selects_quality_loss_isolation_slice_and_keeps_storage_separate(self) -> None:
        payload = build_payload(self.repo_root())

        self.assertEqual(payload["issue"], 79)
        self.assertEqual(payload["summary_kind"], "intrinsic_literal_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("replace_all", selected["minimum_implementation_boundary"][0])
        self.assertIn("acutance_only", selected["minimum_implementation_boundary"][0])
        self.assertEqual(
            payload["family_context"]["issue77_outcome"]["status"],
            "bounded_negative",
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_selected_slice_and_excluded_routes(self) -> None:
        payload = build_payload(self.repo_root())
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Literal Next Slice", markdown)
        self.assertIn("## Selected Slice", markdown)
        self.assertIn("## Excluded Routes", markdown)
        self.assertIn(SELECTED_SLICE_ID, markdown)
        self.assertIn("reopen measured OECF", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
