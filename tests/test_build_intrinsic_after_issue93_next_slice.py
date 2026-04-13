from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue93_next_slice import (
    ISSUE93_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue93NextSliceTest(unittest.TestCase):
    def test_payload_selects_readout_disconnect_boundary(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue91_artifact_path=Path("artifacts/intrinsic_after_issue89_next_slice_benchmark.json"),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue89_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"
            ),
            issue93_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 95)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue93_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("compensated_mtf_for_acutance", selected["minimum_implementation_boundary"][1])
        self.assertIn("compensated_mtf", selected["minimum_implementation_boundary"][1])
        self.assertIn("bundle_pr30_observable_stack_into_issue93_now", payload["candidate_slices"][1]["slice_id"])
        self.assertTrue(
            payload["residual_gap_evidence"]["issue93_preserves_issue89_quality_loss"][
                "overall_quality_loss_mae_mean"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue93_preserves_issue85_readout"][
                "mtf_abs_signed_rel_mean"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue93_still_trails_pr30"][
                "overall_quality_loss_mae_mean"
            ]
        )
        self.assertIn("calibration_file", payload["pipeline_delta_summary"])
        self.assertEqual(
            payload["pipeline_delta_summary"]["intrinsic_full_reference_scope"][ISSUE93_LABEL],
            "readout_reconnect_quality_loss_isolation_downstream_matched_ori_only",
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_readout_disconnect_and_quality_loss_split(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue91_artifact_path=Path("artifacts/intrinsic_after_issue89_next_slice_benchmark.json"),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue89_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"
            ),
            issue93_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 93 Next Slice", markdown)
        self.assertIn("## Residual Gap Evidence", markdown)
        self.assertIn("compensated_mtf = intrinsic_mtf", markdown)
        self.assertIn("quality_loss_compensated_mtf_for_acutance", markdown)
        self.assertIn("bundle PR30's entire observable stack", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
