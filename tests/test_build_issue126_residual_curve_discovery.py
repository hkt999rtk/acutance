from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue126_residual_curve_discovery import (
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIssue126ResidualCurveDiscoveryTest(unittest.TestCase):
    def test_payload_selects_minimum_residual_curve_slice(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
        )

        self.assertEqual(payload["issue"], 126)
        self.assertEqual(payload["current_best"]["issue"], 124)
        self.assertEqual(payload["current_best"]["pr"], 125)
        self.assertEqual(payload["selected_next_slice"]["slice_id"], SELECTED_SLICE_ID)
        self.assertEqual(payload["selected_next_slice"]["target_mixups"], ["ori", "0.15"])
        self.assertEqual(payload["selected_next_slice"]["explicitly_deferred_mixups"], ["0.25"])

        residual = payload["residual_curve_evidence"]
        self.assertGreater(residual["delta_to_curve_gate"], 0.004)
        self.assertEqual(
            residual["ranked_positive_excess_mixups"],
            ["ori", "0.15", "0.25"],
        )
        self.assertGreater(residual["ori_only_if_reduced_to_gate_curve_mae"], 0.020)
        self.assertGreater(residual["ori_and_025_if_reduced_to_gate_curve_mae"], 0.020)
        self.assertLessEqual(residual["ori_and_015_if_reduced_to_gate_curve_mae"], 0.020)
        self.assertGreater(residual["by_mixup"]["ori"]["positive_excess_share"], 0.45)
        self.assertGreater(residual["by_mixup"]["0.15"]["positive_excess_share"], 0.30)
        self.assertGreater(residual["by_mixup"]["0.25"]["positive_excess_share"], 0.15)

        gates = payload["readme_gate_status"]["gates"]
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertTrue(gates["focus_preset_acutance_mae_mean"]["pass"])
        self.assertTrue(gates["overall_quality_loss_mae_mean"]["pass"])
        self.assertFalse(gates["non_phone_acutance_preset_mae_max"]["pass"])

        self.assertFalse(payload["stop_curve_work_option"]["selected"])
        self.assertTrue(payload["acceptance"]["identifies_next_bounded_slice"])
        self.assertTrue(payload["acceptance"]["next_handoff_is_not_umbrella"])
        self.assertTrue(payload["acceptance"]["release_separation_preserved"])

    def test_markdown_records_handoff_and_release_separation(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 126 Residual Curve Discovery", markdown)
        self.assertIn("issue124_residual_curve_ori_015_curve_only_shape_boundary", markdown)
        self.assertIn("Target mixups: `ori, 0.15`", markdown)
        self.assertIn("Deferred residual mixups: `0.25`", markdown)
        self.assertIn("Small Print Acutance preset work", markdown)
        self.assertIn("Release Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
