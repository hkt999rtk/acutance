from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue136_curve_preflight_discovery import (
    RESULT_KIND,
    build_payload,
    render_markdown,
)


class BuildIssue136CurvePreflightDiscoveryTest(unittest.TestCase):
    def test_payload_records_no_source_backed_preflight_result(self) -> None:
        payload = self.payload()

        self.assertEqual(payload["issue"], 136)
        self.assertEqual(payload["result_kind"], RESULT_KIND)
        self.assertEqual(payload["current_best"]["issue"], 132)
        self.assertEqual(payload["current_best"]["pr"], 135)
        self.assertEqual(
            payload["current_best"]["profile_path"],
            "algo/issue132_small_print_acutance_parity_input_profile.json",
        )

        gates = payload["readme_gate_status"]["gates"]
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertTrue(gates["focus_preset_acutance_mae_mean"]["pass"])
        self.assertTrue(gates["overall_quality_loss_mae_mean"]["pass"])
        self.assertTrue(gates["non_phone_acutance_preset_mae_max"]["pass"])
        self.assertEqual(payload["readme_gate_status"]["failed_gates"], ["curve_mae_mean"])

        decision = payload["preflight_decision"]
        self.assertEqual(
            decision["status"],
            "no_source_backed_current_topology_015_preflight_found",
        )
        self.assertIsNone(decision["selected_follow_up"])
        self.assertTrue(decision["do_not_open_full_curve_candidate"])
        self.assertIn("source-backed", decision["reason"])

        acceptance = payload["acceptance"]
        self.assertTrue(acceptance["records_post_pr135_readme_gates"])
        self.assertTrue(acceptance["records_pr129_015_negative"])
        self.assertTrue(acceptance["requires_015_preflight"])
        self.assertTrue(acceptance["no_full_curve_candidate_selected"])
        self.assertTrue(acceptance["no_source_backed_current_topology_preflight_found"])
        self.assertTrue(acceptance["result_is_developer_discovery_not_pm_question"])
        self.assertTrue(acceptance["release_separation_preserved"])

    def test_payload_records_pr129_negative_and_rejects_apparent_improvements(self) -> None:
        payload = self.payload()

        issue128 = payload["evidence_base"]["issue128_direct_015_negative"]
        self.assertAlmostEqual(issue128["baseline_015_curve_mae"], 0.029378599163150443)
        self.assertAlmostEqual(issue128["candidate_015_curve_mae"], 0.03545614453309601)
        self.assertGreater(issue128["delta_vs_pr125"], 0.006)
        self.assertTrue(issue128["moves_015_in_wrong_direction"])

        examples = payload["evidence_base"]["apparent_015_improvement_examples"]
        self.assertEqual(len(examples), 2)
        self.assertTrue(all(row["mixup_015_delta_vs_issue132"] < 0.0 for row in examples))
        self.assertTrue(
            all(
                not row["accepted_as_source_backed_current_topology_preflight"]
                for row in examples
            )
        )
        self.assertEqual(
            examples[0]["classification"],
            "fitted_release_workaround_not_source_backed_current_topology",
        )
        self.assertEqual(
            examples[1]["classification"],
            "historical_non_current_topology_with_protected_gate_regression",
        )

    def test_payload_preserves_issue126_curve_requirement(self) -> None:
        payload = self.payload()

        requirement = payload["evidence_base"]["issue126_curve_requirement"]
        self.assertEqual(
            requirement["selected_minimum_gate_clear_mixups"],
            ["ori", "0.15"],
        )
        self.assertLessEqual(requirement["ori_and_015_if_reduced_to_gate_curve_mae"], 0.020)
        self.assertGreater(requirement["ori_and_025_if_reduced_to_gate_curve_mae"], 0.020)

    def test_markdown_records_decision_and_release_separation(self) -> None:
        markdown = render_markdown(self.payload())

        self.assertIn("# Issue 136 Curve Preflight Discovery", markdown)
        self.assertIn("no_source_backed_current_topology_015_preflight_found", markdown)
        self.assertIn("PR #129 direct `0.15` anchor-mask broadening", markdown)
        self.assertIn("fitted_release_workaround_not_source_backed_current_topology", markdown)
        self.assertIn("Required evidence before curve work resumes", markdown)
        self.assertIn("Release Separation", markdown)

    def payload(self) -> dict:
        return build_payload(
            self.repo_root(),
            issue126_discovery_path=Path("artifacts/issue126_residual_curve_discovery.json"),
            issue128_summary_path=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
            issue130_discovery_path=Path("artifacts/issue130_next_slice_discovery.json"),
            issue132_summary_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_summary.json"
            ),
            issue132_acutance_path=Path(
                "artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"
            ),
            parity_acutance_path=Path("artifacts/parity_acutance_quality_loss_benchmark.json"),
            issue63_acutance_path=Path(
                "artifacts/issue63_empirical_linearization_acutance_benchmark.json"
            ),
        )

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
