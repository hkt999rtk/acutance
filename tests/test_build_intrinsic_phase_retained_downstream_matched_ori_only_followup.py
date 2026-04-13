from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_downstream_matched_ori_only_followup import (
    CANDIDATE_LABEL,
    ISSUE85_LABEL,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedDownstreamMatchedOriOnlyFollowupTest(unittest.TestCase):
    def test_payload_records_issue93_scope_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 93)
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "readout_reconnect_quality_loss_isolation_downstream_matched_ori_only",
        )
        self.assertEqual(
            payload["implementation_change"]["selected_slice_id"],
            "phase_retained_intrinsic_quality_loss_only_matched_ori_graft_without_readout_correction",
        )
        self.assertIn(
            "downstream Quality Loss branch",
            payload["implementation_change"]["change"],
        )
        self.assertIn("mtf20_no_worse_than_issue85", payload["acceptance"])
        self.assertIn("overall_quality_loss_improved_vs_issue85", payload["acceptance"])
        self.assertIn("candidate_vs_issue89", payload["comparisons"])
        self.assertNotEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            payload["profiles"][ISSUE85_LABEL]["profile_path"],
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_issue85_issue89_and_storage(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Phase-Retained Downstream Matched-Ori-Only Follow-up", markdown)
        self.assertIn("Issue `#85` baseline", markdown)
        self.assertIn("Issue `#89` full graft reference", markdown)
        self.assertIn("All issue-93 gates pass", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
