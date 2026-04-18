from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue124_curve_only_high_mixup_ori_summary import (
    RESULT_KIND,
    build_payload,
    render_markdown,
)


class BuildIssue124CurveOnlyHighMixupOriSummaryTest(unittest.TestCase):
    def test_payload_records_positive_partial_and_preservation(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue120_summary_path=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
            issue122_summary_path=Path(
                "artifacts/intrinsic_after_issue120_next_slice_benchmark.json"
            ),
            candidate_acutance_path=Path(
                "artifacts/issue124_curve_only_high_mixup_ori_acutance_benchmark.json"
            ),
            candidate_psd_path=Path(
                "artifacts/issue124_curve_only_high_mixup_ori_psd_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 124)
        self.assertEqual(payload["result_kind"], RESULT_KIND)
        self.assertEqual(
            payload["candidate"]["curve_only_acutance_anchor_mixups"],
            ["0.8", "ori"],
        )

        delta = payload["comparisons"]["candidate_vs_pr119"]["delta"]
        self.assertLess(delta["curve_mae_mean"], -0.008)
        self.assertEqual(delta["mtf_abs_signed_rel_mean"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf20"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf30"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf50"], 0.0)
        self.assertEqual(delta["overall_quality_loss_mae_mean"], 0.0)
        self.assertEqual(delta["acutance_preset_mae"]["Small Print Acutance"], 0.0)

        gates = payload["readme_gate_summary"]["gates"]
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertTrue(gates["focus_preset_acutance_mae_mean"]["pass"])
        self.assertTrue(gates["overall_quality_loss_mae_mean"]["pass"])
        self.assertFalse(gates["non_phone_acutance_preset_mae_max"]["pass"])

        curve_tail = payload["curve_tail_result"]
        self.assertLess(curve_tail["by_mixup_delta"]["0.8"], -0.025)
        self.assertLess(curve_tail["by_mixup_delta"]["ori"], -0.033)
        self.assertEqual(curve_tail["by_mixup_delta"]["0.15"], 0.0)
        self.assertEqual(curve_tail["by_mixup_delta"]["0.25"], 0.0)
        self.assertTrue(curve_tail["weighted_curve_mae_matches_candidate"])

        self.assertTrue(payload["acceptance"]["curve_mae_reduced_vs_pr119"])
        self.assertTrue(payload["acceptance"]["reported_mtf_preserved"])
        self.assertTrue(payload["acceptance"]["overall_quality_loss_preserved"])
        self.assertFalse(payload["acceptance"]["all_readme_gates_pass"])

        self.assertFalse(payload["release_separation"]["candidate_is_release_config"])
        for path in payload["candidate"]["source_artifacts"]:
            self.assertFalse(path.startswith("release/deadleaf_13b10_release"))

    def test_markdown_mentions_partial_result_and_remaining_misses(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue120_summary_path=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
            issue122_summary_path=Path(
                "artifacts/intrinsic_after_issue120_next_slice_benchmark.json"
            ),
            candidate_acutance_path=Path(
                "artifacts/issue124_curve_only_high_mixup_ori_acutance_benchmark.json"
            ),
            candidate_psd_path=Path(
                "artifacts/issue124_curve_only_high_mixup_ori_psd_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 124 Curve-Only High-Mixup/Ori Summary", markdown)
        self.assertIn("positive_partial_not_promotable", markdown)
        self.assertIn("curve_mae_mean", markdown)
        self.assertIn("0.8", markdown)
        self.assertIn("ori", markdown)
        self.assertIn("Small Print Acutance", markdown)
        self.assertIn("Release Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
