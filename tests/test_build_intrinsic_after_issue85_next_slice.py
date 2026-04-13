from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue85_next_slice import (
    ISSUE81_LABEL,
    ISSUE85_LABEL,
    ISSUE47_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue85NextSliceTest(unittest.TestCase):
    def test_payload_selects_matched_ori_graft_slice(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue83_artifact_path=Path("artifacts/intrinsic_after_issue81_next_slice_benchmark.json"),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue47_psd_artifact_path=Path(
                "artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json"
            ),
            issue47_acutance_artifact_path=Path(
                "artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json"
            ),
            issue81_psd_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"
            ),
            issue81_acutance_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"
            ),
            issue85_psd_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"
            ),
            issue85_acutance_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"
            ),
            current_best_psd_artifact_path=Path(
                "artifacts/issue77_measured_oecf_psd_benchmark.json"
            ),
            current_best_acutance_artifact_path=Path(
                "artifacts/issue77_measured_oecf_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 87)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue85_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("matched-ori reference correction", selected["minimum_implementation_boundary"][1])
        self.assertEqual(len(selected["runtime_boundary_evidence"]), 2)
        self.assertTrue(
            payload["residual_alignment_evidence"]["issue85_quality_loss_matches_issue81"][
                "quality_loss_preset_mae"
            ]
        )
        self.assertTrue(
            payload["residual_alignment_evidence"]["issue85_readout_matches_issue47"][
                "mtf_threshold_mae"
            ]
        )
        self.assertFalse(payload["pipeline_gap_summary"]["matched_ori_reference_anchor"][ISSUE85_LABEL])
        self.assertTrue(payload["pipeline_gap_summary"]["matched_ori_reference_anchor"]["current_best_pr30_branch"])
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_residual_alignment_and_pipeline_gap(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue83_artifact_path=Path("artifacts/intrinsic_after_issue81_next_slice_benchmark.json"),
            issue85_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"
            ),
            issue47_psd_artifact_path=Path(
                "artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json"
            ),
            issue47_acutance_artifact_path=Path(
                "artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json"
            ),
            issue81_psd_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"
            ),
            issue81_acutance_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"
            ),
            issue85_psd_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"
            ),
            issue85_acutance_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"
            ),
            current_best_psd_artifact_path=Path(
                "artifacts/issue77_measured_oecf_psd_benchmark.json"
            ),
            current_best_acutance_artifact_path=Path(
                "artifacts/issue77_measured_oecf_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 85 Next Slice", markdown)
        self.assertIn("## Residual Alignment Evidence", markdown)
        self.assertIn("matched_ori_reference_anchor", markdown)
        self.assertIn("## Runtime Boundary Evidence", markdown)
        self.assertIn("reopen measured OECF", markdown)
        self.assertIn("Storage Separation", markdown)
        self.assertIn("overall Quality Loss MAE", markdown)
        self.assertIn("mtf20", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
