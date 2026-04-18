from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue128_ori_015_curve_shape_summary import (
    RESULT_KIND,
    build_payload,
    render_markdown,
)


class BuildIssue128Ori015CurveShapeSummaryTest(unittest.TestCase):
    def test_payload_records_bounded_negative_and_preservation(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            candidate_acutance_path=Path(
                "artifacts/issue128_ori_015_curve_shape_acutance_benchmark.json"
            ),
            candidate_psd_path=Path("artifacts/issue128_ori_015_curve_shape_psd_benchmark.json"),
        )

        self.assertEqual(payload["issue"], 128)
        self.assertEqual(payload["result_kind"], RESULT_KIND)
        self.assertEqual(payload["candidate"]["target_mixups"], ["ori", "0.15"])
        self.assertEqual(payload["candidate"]["deferred_mixups"], ["0.25"])
        self.assertEqual(
            payload["candidate"]["curve_only_acutance_anchor_mixups"],
            ["0.15", "0.8", "ori"],
        )

        delta = payload["comparisons"]["candidate_vs_pr125"]["delta"]
        self.assertGreater(delta["curve_mae_mean"], 0.001)
        self.assertEqual(delta["focus_preset_acutance_mae_mean"], 0.0)
        self.assertEqual(delta["overall_quality_loss_mae_mean"], 0.0)
        self.assertEqual(delta["mtf_abs_signed_rel_mean"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf20"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf30"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf50"], 0.0)
        self.assertEqual(delta["acutance_preset_mae"]["Small Print Acutance"], 0.0)

        curve = payload["curve_shape_result"]
        self.assertGreater(curve["by_mixup_delta"]["0.15"], 0.006)
        self.assertEqual(curve["by_mixup_delta"]["0.25"], 0.0)
        self.assertEqual(curve["by_mixup_delta"]["0.8"], 0.0)
        self.assertEqual(curve["by_mixup_delta"]["ori"], 0.0)

        self.assertFalse(payload["acceptance"]["curve_gate_pass"])
        self.assertFalse(payload["acceptance"]["curve_improved_vs_pr125"])
        self.assertTrue(payload["acceptance"]["reported_mtf_preserved"])
        self.assertTrue(payload["acceptance"]["focus_preset_acutance_preserved"])
        self.assertTrue(payload["acceptance"]["overall_quality_loss_preserved"])
        self.assertTrue(payload["acceptance"]["small_print_acutance_preserved"])
        self.assertTrue(payload["acceptance"]["release_separation_preserved"])

    def test_markdown_mentions_negative_result_and_next_step(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            candidate_acutance_path=Path(
                "artifacts/issue128_ori_015_curve_shape_acutance_benchmark.json"
            ),
            candidate_psd_path=Path("artifacts/issue128_ori_015_curve_shape_psd_benchmark.json"),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 128 Ori/0.15 Curve-Shape Summary", markdown)
        self.assertIn("bounded_negative_not_promotable", markdown)
        self.assertIn("0.15", markdown)
        self.assertIn("worsens", markdown)
        self.assertIn("per-mixup or shape-family variant", markdown)
        self.assertIn("Release Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
