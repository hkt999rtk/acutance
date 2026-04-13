from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue89_next_slice import (
    ISSUE85_LABEL,
    ISSUE89_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue89NextSliceTest(unittest.TestCase):
    def test_payload_selects_quality_loss_only_matched_ori_subfamily(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue87_artifact_path=Path("artifacts/intrinsic_after_issue85_next_slice_benchmark.json"),
            issue81_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"
            ),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue89_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 91)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue89_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("quality_loss_compensated_mtf_for_acutance", selected["minimum_implementation_boundary"][1])
        self.assertIn("Do not apply matched-ori reference correction to `compensated_mtf`", selected["minimum_implementation_boundary"][2])
        self.assertEqual(len(selected["runtime_boundary_evidence"]), 2)
        self.assertTrue(
            payload["residual_tradeoff_evidence"]["issue89_preserves_issue85_main_path"][
                "curve_mae_mean"
            ]
        )
        self.assertTrue(
            payload["residual_tradeoff_evidence"]["issue89_improves_quality_loss_vs_issue85"][
                "overall_quality_loss_mae_mean"
            ]
        )
        self.assertTrue(
            payload["residual_tradeoff_evidence"]["issue89_regresses_readout_vs_issue85"][
                "mtf_abs_signed_rel_mean"
            ]
        )
        self.assertFalse(
            payload["pipeline_delta_summary"]["matched_ori_reference_anchor"][ISSUE85_LABEL]
        )
        self.assertTrue(
            payload["pipeline_delta_summary"]["matched_ori_reference_anchor"][ISSUE89_LABEL]
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_tradeoff_split_and_excluded_routes(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue87_artifact_path=Path("artifacts/intrinsic_after_issue85_next_slice_benchmark.json"),
            issue81_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"
            ),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue89_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 89 Next Slice", markdown)
        self.assertIn("## Residual Tradeoff Evidence", markdown)
        self.assertIn("`matched_ori_reference_anchor`", markdown)
        self.assertIn("quality_loss_compensated_mtf_for_acutance", markdown)
        self.assertIn("restart an unbounded matched-ori family search", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
