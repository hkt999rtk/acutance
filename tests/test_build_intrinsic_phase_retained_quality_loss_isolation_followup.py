from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_intrinsic_phase_retained_quality_loss_isolation_followup import (
    CANDIDATE_LABEL,
    build_payload,
    render_markdown,
)


class BuildIntrinsicPhaseRetainedQualityLossIsolationFollowupTest(unittest.TestCase):
    def test_payload_uses_issue81_candidate_and_keeps_storage_separate(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 81)
        self.assertEqual(
            payload["profiles"][CANDIDATE_LABEL]["profile_path"],
            "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json",
        )
        self.assertEqual(
            payload["implementation_change"]["scope_name"],
            "quality_loss_isolation",
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
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"
            ),
            acutance_artifact_path=Path(
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic Phase-Retained Quality-Loss Isolation Follow-up", markdown)
        self.assertIn("quality_loss_isolation", markdown)
        self.assertIn("PR `#30`", markdown)
        self.assertIn("PR `#34`", markdown)
        self.assertIn("PR `#47`", markdown)
        self.assertIn("Storage Separation", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
