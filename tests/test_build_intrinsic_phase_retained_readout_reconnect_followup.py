from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_readout_reconnect_followup import (
    CANDIDATE_LABEL,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedReadoutReconnectFollowupTest(unittest.TestCase):
    def test_payload_uses_issue85_candidate_and_keeps_storage_separate(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 85)
        self.assertEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json",
        )
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "readout_reconnect_quality_loss_isolation",
        )
        self.assertIn(
            "issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json",
            payload["storage"]["new_fitted_artifact_paths"][0],
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_scope_and_acceptance(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Phase-Retained Readout Reconnect Follow-up", markdown)
        self.assertIn("readout_reconnect_quality_loss_isolation", markdown)
        self.assertIn("PR `#30`", markdown)
        self.assertIn("issue `#81`", markdown)
        self.assertIn("All issue-85 gates pass", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
