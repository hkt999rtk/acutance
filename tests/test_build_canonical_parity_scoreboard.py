from __future__ import annotations

import unittest

from algo.build_canonical_parity_scoreboard import build_scoreboard, render_markdown


class BuildCanonicalParityScoreboardTest(unittest.TestCase):
    def test_scoreboard_contains_expected_rows_and_statuses(self) -> None:
        scoreboard = build_scoreboard(repo_root=self.repo_root())
        by_id = {row["family_id"]: row for row in scoreboard["rows"]}

        self.assertIn("release_parity_fit", by_id)
        self.assertIn("release_parity_gray_texture_shape", by_id)
        self.assertIn("direct_issue29_anchored_hf_psd", by_id)
        self.assertIn("direct_issue67_readout_policy", by_id)

        self.assertEqual(by_id["release_parity_fit"]["status"], "parity-valid")
        self.assertEqual(
            by_id["direct_issue67_readout_policy"]["status"],
            "archived / exhausted",
        )
        self.assertAlmostEqual(
            by_id["direct_issue29_anchored_hf_psd"]["overall_quality_loss_mae_mean"],
            1.2214989544377113,
        )
        self.assertEqual(
            by_id["direct_issue56_empirical_frequency_scale"]["sources"]["primary_path"],
            (
                "algo/"
                "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
                "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
                "psd_roi_reference_only_freqscale_1095_profile.json"
            ),
        )

    def test_trend_ranking_prefers_direction_match_then_series_error(self) -> None:
        scoreboard = build_scoreboard(repo_root=self.repo_root())
        rank_by_id = {row["family_id"]: row["rank"] for row in scoreboard["rows"]}

        self.assertLess(
            rank_by_id["release_parity_gray_texture_shape"],
            rank_by_id["release_experimental_shape"],
        )
        self.assertLess(
            rank_by_id["release_experimental_shape"],
            rank_by_id["release_parity_fit"],
        )
        self.assertLess(
            rank_by_id["release_parity_gray_texture_shape_freq105"],
            rank_by_id["release_parity_fit"],
        )

    def test_markdown_mentions_required_sections(self) -> None:
        scoreboard = build_scoreboard(repo_root=self.repo_root())
        markdown = render_markdown(scoreboard)

        self.assertIn("# Canonical Parity Scoreboard", markdown)
        self.assertIn("| Rank | Family | Type | Status | Trend match |", markdown)
        self.assertIn("release/parity_gray_texture_shape", markdown)
        self.assertIn("direct/issue29_anchored_hf_psd", markdown)
        self.assertIn("archived / exhausted", markdown)
        self.assertNotIn("/tmp/", markdown)

    def test_scoreboard_sources_do_not_leak_temp_paths(self) -> None:
        scoreboard = build_scoreboard(repo_root=self.repo_root())
        for row in scoreboard["rows"]:
            self.assertNotIn("/tmp/", row["sources"]["primary_path"])

    @staticmethod
    def repo_root():
        from pathlib import Path

        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
