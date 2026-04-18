from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_pr30_observed_bundle_followup import (
    CANDIDATE_LABEL,
    CURRENT_BEST_LABEL,
    ISSUE102_LABEL,
    PR30_OBSERVED_BRANCH_BUNDLE,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedPr30ObservedBundleFollowupTest(unittest.TestCase):
    def test_payload_records_issue108_scope_bundle_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
            ),
            issue102_summary_path=Path(
                "artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"
            ),
            issue105_summary_path=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        )

        self.assertEqual(payload["issue"], 108)
        self.assertEqual(
            payload["summary_kind"],
            "intrinsic_phase_retained_pr30_observed_bundle_followup",
        )
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only",
        )
        self.assertEqual(
            payload["implementation_change"]["selected_slice_id"],
            SELECTED_SLICE_ID,
        )
        self.assertEqual(
            payload["implementation_change"]["selected_pr30_observed_branch_bundle"],
            PR30_OBSERVED_BRANCH_BUNDLE,
        )
        self.assertTrue(
            all(payload["implementation_change"]["candidate_bundle_matches"].values())
        )
        self.assertIn("all_issue108_gates_pass", payload["acceptance"])
        self.assertIn("candidate_vs_issue102", payload["comparisons"])
        self.assertIn("candidate_vs_current_best_pr30", payload["comparisons"])
        candidate_pipeline = payload["profiles"][CANDIDATE_LABEL]["analysis_pipeline"]
        for key, expected in PR30_OBSERVED_BRANCH_BUNDLE.items():
            self.assertEqual(candidate_pipeline[key], expected)
        self.assertEqual(
            candidate_pipeline["intrinsic_full_reference_scope"],
            "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only",
        )
        self.assertNotEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            payload["profiles"][ISSUE102_LABEL]["profile_path"],
        )
        self.assertNotEqual(
            payload["profiles"][ISSUE102_LABEL]["profile_path"],
            payload["profiles"][CURRENT_BEST_LABEL]["profile_path"],
        )
        selected_source = payload["implementation_change"]["selected_slice_source"]
        self.assertEqual(selected_source["issue"], 105)
        self.assertEqual(selected_source["selected_slice_id"], SELECTED_SLICE_ID)
        self.assertEqual(
            selected_source["selected_pr30_observed_branch_bundle_keys"],
            list(PR30_OBSERVED_BRANCH_BUNDLE),
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )
            self.assertFalse(path.startswith("release/deadleaf_13b10_release/config"))

    def test_markdown_mentions_issue102_pr30_bundle_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
            ),
            issue102_summary_path=Path(
                "artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"
            ),
            issue105_summary_path=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        )
        markdown = render_markdown(payload)

        self.assertIn(
            "# Intrinsic Phase-Retained PR30 Observed-Branch Bundle Follow-up",
            markdown,
        )
        self.assertIn("Issue `#108`", markdown)
        self.assertIn("issue-102 intrinsic topology", markdown)
        self.assertIn("PR `#30` observed-branch bundle", markdown)
        self.assertIn("calibration_file", markdown)
        self.assertIn("mtf_compensation_mode", markdown)
        self.assertIn("sensor_fill_factor", markdown)
        self.assertIn("texture_support_scale", markdown)
        self.assertIn("high_frequency_guard_start_cpp", markdown)
        self.assertIn("All issue-108 gates pass", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
