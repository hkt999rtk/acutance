from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue81_next_slice import (
    ISSUE47_LABEL,
    ISSUE81_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue81NextSliceTest(unittest.TestCase):
    def test_payload_selects_readout_reconnect_slice(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue81_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 83)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue81_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("compensated_mtf", selected["minimum_implementation_boundary"][0])
        self.assertEqual(len(selected["runtime_boundary_evidence"]), 2)
        self.assertEqual(
            payload["comparison_records"][ISSUE81_LABEL]["curve_mae_mean"],
            payload["comparison_records"][ISSUE47_LABEL]["curve_mae_mean"],
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_runtime_boundary_and_exclusions(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue81_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 81 Next Slice", markdown)
        self.assertIn("## Runtime Boundary Evidence", markdown)
        self.assertIn("compensated_mtf_for_acutance", markdown)
        self.assertIn("reopen measured OECF", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
