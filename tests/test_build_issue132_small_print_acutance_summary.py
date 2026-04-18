from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue132_small_print_acutance_summary import build_payload, render_markdown


class BuildIssue132SmallPrintAcutanceSummaryTest(unittest.TestCase):
    def test_payload_records_targeted_small_print_boundary(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue130_discovery_path=Path("artifacts/issue130_next_slice_discovery.json"),
            candidate_profile_path=Path(
                "algo/issue132_small_print_acutance_parity_input_profile.json"
            ),
            baseline_profile_path=Path(
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json"
            ),
            candidate_acutance_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"
            ),
            candidate_psd_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_psd_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 132)
        self.assertEqual(payload["result_kind"], "positive_targeted_not_full_canonical")
        self.assertEqual(
            payload["candidate"]["profile_path"],
            "algo/issue132_small_print_acutance_parity_input_profile.json",
        )

        small = payload["small_print_result"]
        self.assertEqual(small["target_preset"], "Small Print Acutance")
        self.assertAlmostEqual(small["baseline_value"], 0.031726251556383624)
        self.assertAlmostEqual(small["candidate_value"], 0.028952087494203603)
        self.assertLess(small["delta_vs_pr125"], -0.0027)
        self.assertLessEqual(small["candidate_value"], 0.030)
        self.assertEqual(
            small["override_source_profile"],
            "algo/deadleaf_13b10_parity_psd_mtf_profile.json",
        )

        acceptance = payload["acceptance"]
        self.assertTrue(acceptance["small_print_gate_pass"])
        self.assertTrue(acceptance["focus_preset_acutance_gate_pass"])
        self.assertTrue(acceptance["curve_mae_preserved_vs_pr125"])
        self.assertTrue(acceptance["reported_mtf_preserved_vs_pr125"])
        self.assertTrue(acceptance["overall_quality_loss_gate_pass"])
        self.assertTrue(acceptance["overall_quality_loss_preserved_vs_pr125"])
        self.assertTrue(acceptance["quality_loss_inputs_preserved"])
        self.assertTrue(acceptance["only_small_print_acutance_input_added"])
        self.assertTrue(acceptance["release_separation_preserved"])
        self.assertFalse(acceptance["full_readme_gate_pass"])
        self.assertEqual(payload["readme_gate_summary"]["failed_gates"], ["curve_mae_mean"])

        scope = payload["profile_scope_delta"]
        self.assertEqual(scope["changed_keys"], ["acutance_preset_input_profile_overrides"])
        self.assertEqual(
            scope["acutance_preset_input_profile_overrides"],
            {"Small Print Acutance": "algo/deadleaf_13b10_parity_psd_mtf_profile.json"},
        )
        self.assertTrue(scope["quality_loss_preset_input_profile_overrides_preserved"])
        self.assertTrue(scope["reported_mtf_readout_fields_preserved"])

    def test_payload_preserves_non_target_metrics(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue130_discovery_path=Path("artifacts/issue130_next_slice_discovery.json"),
            candidate_profile_path=Path(
                "algo/issue132_small_print_acutance_parity_input_profile.json"
            ),
            baseline_profile_path=Path(
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json"
            ),
            candidate_acutance_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"
            ),
            candidate_psd_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_psd_benchmark.json"
            ),
        )

        delta = payload["comparisons"]["candidate_vs_pr125"]["delta"]
        self.assertEqual(delta["curve_mae_mean"], 0.0)
        self.assertEqual(delta["overall_quality_loss_mae_mean"], 0.0)
        self.assertEqual(delta["mtf_abs_signed_rel_mean"], 0.0)
        self.assertTrue(all(value == 0.0 for value in delta["mtf_threshold_mae"].values()))
        self.assertEqual(delta["quality_loss_preset_mae"]["Small Print Quality Loss"], 0.0)
        self.assertLess(delta["focus_preset_acutance_mae_mean"], 0.0)

    def test_markdown_records_result_and_remaining_gate(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue124_summary_path=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
            issue130_discovery_path=Path("artifacts/issue130_next_slice_discovery.json"),
            candidate_profile_path=Path(
                "algo/issue132_small_print_acutance_parity_input_profile.json"
            ),
            baseline_profile_path=Path(
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json"
            ),
            candidate_acutance_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"
            ),
            candidate_psd_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_psd_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 132 Small Print Acutance Boundary Summary", markdown)
        self.assertIn("Small Print Acutance", markdown)
        self.assertIn("algo/deadleaf_13b10_parity_psd_mtf_profile.json", markdown)
        self.assertIn("only `curve_mae_mean <= 0.020`", markdown)
        self.assertIn("Release Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
