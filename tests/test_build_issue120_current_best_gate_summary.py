from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_issue120_current_best_gate_summary import (
    CURRENT_BEST_LABEL,
    NEXT_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIssue120CurrentBestGateSummaryTest(unittest.TestCase):
    def test_payload_records_current_best_and_readme_gate_misses(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue118_summary_path=Path(
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 120)
        self.assertEqual(payload["summary_kind"], "issue120_current_best_readme_gate_summary")
        self.assertEqual(payload["current_best"]["label"], CURRENT_BEST_LABEL)
        self.assertEqual(payload["current_best"]["pr"], 119)
        self.assertEqual(payload["current_best"]["issue"], 118)
        self.assertEqual(payload["current_best"]["merge_commit"], "52bbca7")

        delta = payload["comparisons"]["current_best_vs_pr30"]["delta"]
        self.assertLess(delta["overall_quality_loss_mae_mean"], -0.017)
        self.assertLess(delta["curve_mae_mean"], -0.0039)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf20"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf30"], 0.0)
        self.assertEqual(delta["mtf_threshold_mae"]["mtf50"], 0.0)

        gates = payload["readme_gate_summary"]["gates"]
        self.assertFalse(payload["readme_gate_summary"]["all_readme_gates_pass"])
        self.assertFalse(gates["curve_mae_mean"]["pass"])
        self.assertTrue(gates["focus_preset_acutance_mae_mean"]["pass"])
        self.assertTrue(gates["overall_quality_loss_mae_mean"]["pass"])
        self.assertFalse(gates["non_phone_acutance_preset_mae_max"]["pass"])
        self.assertEqual(
            gates["non_phone_acutance_preset_mae_max"]["worst_preset"],
            "Small Print Acutance",
        )
        self.assertTrue(gates['5.5" Phone Display Acutance']["pass"])

        self.assertEqual(payload["next_handoff"]["mode"], "developer_discovery")
        self.assertEqual(payload["next_handoff"]["selected_slice_id"], NEXT_SLICE_ID)
        self.assertFalse(payload["release_separation"]["candidate_is_release_config"])
        for path in payload["current_best"]["source_artifacts"]:
            self.assertFalse(path.startswith("release/deadleaf_13b10_release/config"))

    def test_markdown_mentions_gates_next_handoff_and_release_separation(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue118_summary_path=Path(
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Issue 120 Current Best README Gate Summary", markdown)
        self.assertIn("issue `#118` / PR `#119`", markdown)
        self.assertIn("README Gate Status", markdown)
        self.assertIn("Small Print Acutance", markdown)
        self.assertIn("developer_discovery", markdown)
        self.assertIn(NEXT_SLICE_ID, markdown)
        self.assertIn("not a release-facing config promotion", markdown)

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
