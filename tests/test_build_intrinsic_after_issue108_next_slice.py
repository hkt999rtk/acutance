from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue108_next_slice import (
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue108NextSliceTest(unittest.TestCase):
    def test_payload_selects_computer_monitor_quality_loss_boundary(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue108_summary_path=Path(
                "artifacts/intrinsic_phase_retained_pr30_observed_bundle_benchmark.json"
            ),
            issue108_acutance_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
            ),
            issue105_summary_path=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        )

        self.assertEqual(payload["issue"], 111)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue108_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertEqual(selected["decision"], "advance")
        self.assertIn("Computer Monitor", selected["selected_summary"])

        residual = payload["residual_quality_loss_boundaries"]
        top_preset = residual["top_positive_preset"]
        self.assertEqual(top_preset["preset"], "Computer Monitor Quality Loss")
        self.assertGreater(top_preset["delta"], 0.66)
        self.assertGreater(top_preset["mean_contribution"], 0.13)
        self.assertGreater(residual["top_positive_preset_net_gap_share"], 0.70)

        self.assertTrue(
            all(payload["boundary_evidence"]["reported_mtf_parity_with_pr30"].values())
        )
        self.assertTrue(
            payload["boundary_evidence"]["quality_loss_coefficients_and_ceilings_match_pr30"]
        )
        self.assertTrue(
            all(
                payload["boundary_evidence"][
                    "issue102_intrinsic_gains_preserved_vs_pr30"
                ].values()
            )
        )

        excluded = {
            row["slice_id"]: row for row in payload["candidate_slices"] if row["decision"] == "exclude"
        }
        self.assertIn("retune_quality_loss_coefficients_or_om_ceiling", excluded)
        self.assertIn("retune_reported_mtf_readout_again", excluded)
        self.assertIn("phone_preset_only_search", excluded)
        self.assertIn("uhdtv_quality_loss_preset_family", excluded)

        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )
            self.assertFalse(path.startswith("release/deadleaf_13b10_release/config"))

    def test_markdown_mentions_evidence_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue108_summary_path=Path(
                "artifacts/intrinsic_phase_retained_pr30_observed_bundle_benchmark.json"
            ),
            issue108_acutance_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
            ),
            issue105_summary_path=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 108 Next Slice", markdown)
        self.assertIn("Issue `#111`", markdown)
        self.assertIn("Computer Monitor Quality Loss", markdown)
        self.assertIn("reported-MTF", markdown)
        self.assertIn("Quality Loss coefficients", markdown)
        self.assertIn("UHDTV Quality Loss", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
