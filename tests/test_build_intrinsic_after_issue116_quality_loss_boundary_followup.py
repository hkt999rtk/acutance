from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue116_quality_loss_boundary_followup import (
    CANDIDATE_LABEL,
    COMPUTER_MONITOR_QUALITY_LOSS,
    LARGE_PRINT_QUALITY_LOSS,
    SELECTED_SLICE_ID,
    SMALL_PRINT_QUALITY_LOSS,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue116QualityLossBoundaryFollowupTest(unittest.TestCase):
    def test_payload_records_large_print_only_boundary(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue116_summary_path=Path(
                "artifacts/intrinsic_after_issue114_quality_loss_boundary_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"
            ),
            psd_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 118)
        self.assertEqual(
            payload["summary_kind"],
            "intrinsic_after_issue116_quality_loss_boundary_followup",
        )
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        self.assertTrue(payload["acceptance"]["large_print_quality_loss_improved_vs_issue116"])
        self.assertTrue(payload["acceptance"]["overall_quality_loss_improved_vs_issue116"])
        self.assertTrue(payload["acceptance"]["computer_monitor_quality_loss_preserved_vs_issue116"])
        self.assertTrue(payload["acceptance"]["small_print_quality_loss_preserved_vs_issue116"])
        self.assertTrue(payload["acceptance"]["reported_mtf_equal_to_issue116"])
        self.assertTrue(payload["acceptance"]["only_large_print_quality_loss_input_added"])
        self.assertTrue(payload["acceptance"]["quality_loss_coefficients_preserved"])
        self.assertTrue(payload["acceptance"]["all_issue118_gates_pass"])

        delta = payload["comparisons"]["candidate_vs_issue116"]["delta"]
        self.assertLess(delta["quality_loss_preset_mae"][LARGE_PRINT_QUALITY_LOSS], -0.10)
        self.assertLess(delta["overall_quality_loss_mae_mean"], -0.02)
        self.assertEqual(
            delta["quality_loss_preset_mae"][COMPUTER_MONITOR_QUALITY_LOSS],
            0.0,
        )
        self.assertEqual(
            delta["quality_loss_preset_mae"][SMALL_PRINT_QUALITY_LOSS],
            0.0,
        )
        for preset, value in delta["quality_loss_preset_mae"].items():
            if preset not in {
                LARGE_PRINT_QUALITY_LOSS,
                SMALL_PRINT_QUALITY_LOSS,
                COMPUTER_MONITOR_QUALITY_LOSS,
            }:
                self.assertEqual(value, 0.0)

        candidate = payload["profiles"][CANDIDATE_LABEL]
        expected_input = (
            "algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
            "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json"
        )
        self.assertEqual(
            candidate["analysis_pipeline"]["quality_loss_preset_input_profile_overrides"],
            {
                COMPUTER_MONITOR_QUALITY_LOSS: expected_input,
                SMALL_PRINT_QUALITY_LOSS: expected_input,
                LARGE_PRINT_QUALITY_LOSS: expected_input,
            },
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )
            self.assertFalse(path.startswith("release/deadleaf_13b10_release/config"))

    def test_markdown_mentions_scope_result_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue116_summary_path=Path(
                "artifacts/intrinsic_after_issue114_quality_loss_boundary_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"
            ),
            psd_artifact_path=Path(
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 116 Quality Loss Boundary", markdown)
        self.assertIn("Issue `#118`", markdown)
        self.assertIn("Large Print Quality Loss", markdown)
        self.assertIn("Small Print", markdown)
        self.assertIn("Computer Monitor", markdown)
        self.assertIn("reported-MTF", markdown)
        self.assertIn("Quality Loss coefficients", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
