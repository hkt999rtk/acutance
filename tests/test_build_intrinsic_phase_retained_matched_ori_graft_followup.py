from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_matched_ori_graft_followup import (
    CANDIDATE_LABEL,
    ISSUE85_LABEL,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedMatchedOriGraftFollowupTest(unittest.TestCase):
    def test_payload_records_issue89_as_mixed_negative(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 89)
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "readout_reconnect_quality_loss_isolation_matched_ori_graft",
        )
        self.assertEqual(
            payload["profiles"][CANDIDATE_LABEL]["curve_mae_mean"],
            payload["profiles"][ISSUE85_LABEL]["curve_mae_mean"],
        )
        self.assertTrue(payload["acceptance"]["overall_quality_loss_improved_vs_issue85"])
        self.assertFalse(payload["acceptance"]["mtf20_closer_to_current_best_pr30"])
        self.assertFalse(
            payload["acceptance"]["mtf_abs_signed_rel_no_worse_distance_to_current_best_pr30"]
        )
        self.assertFalse(payload["acceptance"]["all_issue89_gates_pass"])

    def test_markdown_mentions_quality_loss_gain_and_readout_regression(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Phase-Retained Matched-Ori Graft Follow-up", markdown)
        self.assertIn("overall_quality_loss_mae_mean", markdown)
        self.assertIn("mtf20", markdown)
        self.assertIn("All issue-89 gates pass: `False`", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
