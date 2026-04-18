from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue120_next_slice import (
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue120NextSliceTest(unittest.TestCase):
    def test_payload_recommends_split_and_selects_curve_tail_slice(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue120_summary_path=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
            issue118_summary_path=Path(
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"
            ),
            issue118_acutance_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"
            ),
            issue118_psd_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"
            ),
            record_summary_path=Path(
                "artifacts/"
                "imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_"
                "sextic_acutance_record_summary.json"
            ),
        )

        self.assertEqual(payload["issue"], 122)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue120_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        self.assertEqual(
            payload["split_recommendation"]["recommendation"],
            "split_remaining_misses",
        )
        self.assertEqual(payload["split_recommendation"]["first_slice"], SELECTED_SLICE_ID)

        gates = payload["readme_gate_status"]["gates"]
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertGreater(gates["curve_mae_mean"]["delta_to_gate"], 0.012)
        self.assertFalse(gates["non_phone_acutance_preset_mae_max"]["pass"])
        self.assertEqual(
            gates["non_phone_acutance_preset_mae_max"]["worst_preset"],
            "Small Print Acutance",
        )
        self.assertLess(
            payload["residual_small_print_evidence"]["delta_to_gate"],
            0.002,
        )
        self.assertLess(
            payload["residual_small_print_evidence"]["delta_vs_pr30"],
            -0.014,
        )

        curve = payload["residual_curve_evidence"]
        self.assertGreater(curve["high_mixup_weighted_error_share"], 0.51)
        self.assertAlmostEqual(curve["high_mixup_record_fraction"], 0.3)
        self.assertGreater(curve["by_mixup"]["ori"]["delta_vs_comparison"], 0.03)
        self.assertGreater(curve["by_mixup"]["0.8"]["delta_vs_comparison"], 0.004)
        self.assertTrue(curve["low_mid_already_below_gate"]["0.4"])
        self.assertTrue(curve["low_mid_already_below_gate"]["0.65"])

        self.assertTrue(
            payload["quality_loss_boundary_invariance"][
                "all_curve_and_acutance_metrics_invariant"
            ]
        )
        selected = next(row for row in payload["candidate_slices"] if row["selected"])
        self.assertEqual(selected["expected_preservation"]["reported_mtf_parity"], "preserve")
        self.assertEqual(
            selected["expected_preservation"]["overall_quality_loss_mae_mean"],
            "preserve",
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(path.startswith("release/deadleaf_13b10_release"))

    def test_markdown_mentions_split_high_mixup_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue120_summary_path=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
            issue118_summary_path=Path(
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"
            ),
            issue118_acutance_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"
            ),
            issue118_psd_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"
            ),
            record_summary_path=Path(
                "artifacts/"
                "imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_"
                "sextic_acutance_record_summary.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 120 Next Slice", markdown)
        self.assertIn("split_remaining_misses", markdown)
        self.assertIn(SELECTED_SLICE_ID, markdown)
        self.assertIn("High-mixup", markdown)
        self.assertIn("Small Print Acutance", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
