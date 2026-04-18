from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue102_next_slice import (
    CURRENT_BEST_LABEL,
    ISSUE102_LABEL,
    PR30_OBSERVED_BRANCH_BUNDLE_KEYS,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue102NextSliceTest(unittest.TestCase):
    def test_payload_selects_observed_branch_pr30_bundle(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue99_artifact_path=Path("artifacts/intrinsic_after_issue97_next_slice_benchmark.json"),
            issue102_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 105)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue102_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("anchored calibration", selected["selected_summary"])
        self.assertIn("mtf_compensation_mode=sensor_aperture_sinc", selected["selected_summary"])
        self.assertIn("sensor_fill_factor=1.5", selected["selected_summary"])
        self.assertIn("texture_support_scale", selected["selected_summary"])
        self.assertIn("high_frequency_guard_start_cpp", selected["selected_summary"])
        self.assertIn("readout-only sensor-aperture compensation", selected["minimum_implementation_boundary"][0])
        self.assertTrue(
            payload["residual_gap_evidence"]["issue93_issue97_issue102_quality_loss_record_is_invariant"][
                "issue93_equals_issue102"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue102_readout_improves_but_does_not_close_pr30_gap"][
                "mtf20_beats_current_best_pr30"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue102_readout_improves_but_does_not_close_pr30_gap"][
                "mtf30_still_worse_than_current_best_pr30"
            ]
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["calibration_file"][ISSUE102_LABEL],
            "algo/deadleaf_13b10_psd_calibration.json",
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["calibration_file"][CURRENT_BEST_LABEL],
            "algo/deadleaf_13b10_psd_calibration_anchored.json",
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["texture_support_scale"][ISSUE102_LABEL], False
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["texture_support_scale"][CURRENT_BEST_LABEL], True
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["mtf_compensation_mode"][ISSUE102_LABEL], "none"
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["mtf_compensation_mode"][CURRENT_BEST_LABEL],
            "sensor_aperture_sinc",
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["sensor_fill_factor"][ISSUE102_LABEL], 1.0
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["sensor_fill_factor"][CURRENT_BEST_LABEL], 1.5
        )
        self.assertEqual(
            payload["selected_pr30_observed_branch_bundle_keys"],
            list(PR30_OBSERVED_BRANCH_BUNDLE_KEYS),
        )
        selected_boundary = "\n".join(selected["minimum_implementation_boundary"])
        for key in PR30_OBSERVED_BRANCH_BUNDLE_KEYS:
            self.assertIn(key, selected_boundary)
        self.assertTrue(
            payload["residual_gap_evidence"][
                "downstream_quality_loss_live_compensation_pair_differs_from_pr30"
            ]["mtf_compensation_mode_differs"]
        )
        self.assertTrue(
            payload["residual_gap_evidence"][
                "downstream_quality_loss_live_compensation_pair_differs_from_pr30"
            ]["sensor_fill_factor_differs"]
        )
        self.assertEqual(
            payload["comparison_records"][ISSUE102_LABEL]["analysis_pipeline"][
                "readout_mtf_compensation_mode"
            ],
            "sensor_aperture_sinc",
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_pr30_bundle_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue99_artifact_path=Path("artifacts/intrinsic_after_issue97_next_slice_benchmark.json"),
            issue102_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 102 Next Slice", markdown)
        self.assertIn("## Pipeline Delta Summary", markdown)
        self.assertIn("anchored calibration", markdown)
        self.assertIn("mtf_compensation_mode", markdown)
        self.assertIn("sensor_fill_factor", markdown)
        self.assertIn("texture_support_scale", markdown)
        self.assertIn("high_frequency_guard_start_cpp", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
