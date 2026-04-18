from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue130_next_slice_discovery import (
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIssue130NextSliceDiscoveryTest(unittest.TestCase):
    def test_payload_selects_small_print_preset_only_boundary(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            issue128_summary_path=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
        )

        self.assertEqual(payload["issue"], 130)
        self.assertEqual(payload["current_best"]["issue"], 124)
        self.assertEqual(payload["current_best"]["pr"], 125)
        self.assertEqual(payload["selected_next_slice"]["slice_id"], SELECTED_SLICE_ID)
        self.assertEqual(
            payload["selected_next_slice"]["slice_type"],
            "Small Print Acutance preset-only boundary",
        )
        self.assertTrue(payload["selected_next_slice"]["selected"])

        curve = payload["curve_path_status"]
        self.assertEqual(curve["status"], "not_selected_for_direct_implementation")
        self.assertTrue(curve["do_not_continue_broadening_issue124_anchor_mask"])
        self.assertIn("`0.15` improves", curve["future_curve_prerequisite"])

        issue128 = payload["evidence_base"]["issue128_negative_result"]
        self.assertEqual(issue128["result_kind"], "bounded_negative_not_promotable")
        self.assertGreater(issue128["curve_mae_delta_vs_pr125"], 0.001)
        self.assertGreater(issue128["mixup_015_delta_vs_pr125"], 0.006)
        self.assertTrue(issue128["protected_metrics_preserved"]["reported_mtf"])
        self.assertTrue(issue128["protected_metrics_preserved"]["overall_quality_loss"])

        small = payload["small_print_boundary"]
        self.assertEqual(small["target_preset"], "Small Print Acutance")
        self.assertEqual(small["worst_non_phone_preset"], "Small Print Acutance")
        self.assertGreater(small["delta_to_gate"], 0.001)
        self.assertLess(small["delta_to_gate"], 0.002)

        gates = payload["readme_gate_status"]["gates"]
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertTrue(gates["focus_preset_acutance_mae_mean"]["pass"])
        self.assertTrue(gates["overall_quality_loss_mae_mean"]["pass"])
        self.assertFalse(gates["non_phone_acutance_preset_mae_max"]["pass"])

        acceptance = payload["acceptance"]
        self.assertTrue(acceptance["identifies_next_bounded_slice"])
        self.assertTrue(acceptance["next_handoff_is_not_umbrella"])
        self.assertTrue(acceptance["selected_slice_from_checked_in_artifacts"])
        self.assertTrue(acceptance["current_best_remains_pr125"])
        self.assertTrue(acceptance["curve_continuation_requires_015_preflight"])
        self.assertTrue(acceptance["small_print_handoff_is_preset_only"])

    def test_selected_slice_preserves_non_target_boundaries(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            issue128_summary_path=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
        )

        boundary = payload["selected_next_slice"]["minimum_implementation_boundary"]
        boundary_text = "\n".join(boundary)
        self.assertIn("Small Print Acutance", boundary_text)
        self.assertIn("Do not change `curve_only_acutance_anchor_mixups`", boundary_text)
        self.assertIn("Do not change reported-MTF", boundary_text)
        self.assertIn("Do not change Quality Loss", boundary_text)

        preservation = payload["selected_next_slice"]["expected_preservation"]
        self.assertEqual(preservation["curve_mae_mean"], "preserve_pr125")
        self.assertEqual(preservation["reported_mtf_parity"], "preserve_pr125")
        self.assertEqual(preservation["overall_quality_loss_mae_mean"], "preserve_pr125")
        self.assertEqual(preservation["quality_loss_coefficients"], "preserve")
        self.assertEqual(preservation["release_separation"], "preserve")

    def test_markdown_records_decision_and_handoff(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            issue128_summary_path=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 130 Next-Slice Discovery", markdown)
        self.assertIn("Current best remains issue `#124` / PR `#125`", markdown)
        self.assertIn("do not continue broadening the issue #124 curve-only anchor mask", markdown)
        self.assertIn("per-mixup or shape-family preflight proving `0.15` improves", markdown)
        self.assertIn("Small Print Acutance preset-only", markdown)
        self.assertIn("Release Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
