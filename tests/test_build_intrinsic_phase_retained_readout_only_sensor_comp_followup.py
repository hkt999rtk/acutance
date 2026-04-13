from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_readout_only_sensor_comp_followup import (
    CANDIDATE_LABEL,
    ISSUE93_LABEL,
    ISSUE97_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedReadoutOnlySensorCompFollowupTest(unittest.TestCase):
    def test_payload_records_issue102_scope_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 102)
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only",
        )
        self.assertEqual(
            payload["implementation_change"]["selected_slice_id"],
            SELECTED_SLICE_ID,
        )
        self.assertIn("sensor_aperture_sinc", payload["implementation_change"]["change"])
        self.assertIn("mtf30_improved_vs_issue97", payload["acceptance"])
        self.assertIn("mtf50_improved_vs_issue97", payload["acceptance"])
        self.assertEqual(
            payload["profiles"][CANDIDATE_LABEL]["analysis_pipeline"]["readout_mtf_compensation_mode"],
            "sensor_aperture_sinc",
        )
        self.assertEqual(
            payload["profiles"][CANDIDATE_LABEL]["analysis_pipeline"]["readout_sensor_fill_factor"],
            1.5,
        )
        self.assertNotEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            payload["profiles"][ISSUE97_LABEL]["profile_path"],
        )
        self.assertNotEqual(
            payload["profiles"][ISSUE97_LABEL]["profile_path"],
            payload["profiles"][ISSUE93_LABEL]["profile_path"],
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_issue97_pr30_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn(
            "# Intrinsic Phase-Retained Readout-Only Sensor Compensation Follow-up",
            markdown,
        )
        self.assertIn("Issue `#93` baseline", markdown)
        self.assertIn("Issue `#97` baseline", markdown)
        self.assertIn("Current PR `#30` branch", markdown)
        self.assertIn("All issue-102 gates pass", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
