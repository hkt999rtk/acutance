from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_reported_mtf_disconnect_followup import (
    CANDIDATE_LABEL,
    ISSUE93_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedReportedMtfDisconnectFollowupTest(unittest.TestCase):
    def test_payload_records_issue97_scope_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 97)
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only",
        )
        self.assertEqual(
            payload["implementation_change"]["selected_slice_id"],
            SELECTED_SLICE_ID,
        )
        self.assertIn("reported-MTF", payload["implementation_change"]["change"])
        self.assertIn("mtf20_improved_vs_issue93", payload["acceptance"])
        self.assertIn("mtf_abs_signed_rel_improved_vs_issue93", payload["acceptance"])
        self.assertNotEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            payload["profiles"][ISSUE93_LABEL]["profile_path"],
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_issue93_pr30_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Phase-Retained Reported-MTF Disconnect Follow-up", markdown)
        self.assertIn("Issue `#93` baseline", markdown)
        self.assertIn("Current PR `#30` branch", markdown)
        self.assertIn("All issue-97 gates pass", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
