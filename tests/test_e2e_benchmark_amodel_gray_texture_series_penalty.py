from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BenchmarkAmodelGrayTextureSeriesPenaltyE2ETest(unittest.TestCase):
    def test_cli_reproduces_checked_in_series_penalty_tradeoff(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        dataset_root = repo_root / "20260318_deadleaf_13b10" / "output3_Amodel"
        if not dataset_root.exists():
            self.skipTest(f"Dataset missing: {dataset_root}")

        checked_in = json.loads(
            (
                repo_root / "artifacts" / "amodel_gray_texture_series_penalty_benchmark.json"
            ).read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "amodel_gray_texture_series_penalty_benchmark.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "algo.benchmark_amodel_gain_hypotheses",
                    "20260318_deadleaf_13b10/output3_Amodel",
                    "release/deadleaf_13b10_release/config/parity_fit_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq110_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq105_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_texture_shape_nofreq_profile.release.json",
                    "release/deadleaf_13b10_release/config/experimental_shape_profile.release.json",
                    "--output",
                    str(output_path),
                ],
                check=True,
                cwd=repo_root,
            )
            regenerated = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(regenerated["baseline"]["summary"], checked_in["baseline"]["summary"])
        self.assertEqual(
            [entry["profile_name"] for entry in regenerated["hypotheses"]],
            [entry["profile_name"] for entry in checked_in["hypotheses"]],
        )

        gray_texture = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_texture_shape_hypothesis"
        )
        freq110 = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_texture_shape_freq110_hypothesis"
        )
        freq105 = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_texture_shape_freq105_hypothesis"
        )
        nofreq = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_texture_shape_nofreq_hypothesis"
        )
        experimental = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_experimental_shape"
        )

        self.assertGreater(
            gray_texture["summary"]["focus_preset_direction_match_count"],
            freq110["summary"]["focus_preset_direction_match_count"],
        )
        self.assertGreater(
            freq110["summary"]["focus_preset_direction_match_count"],
            experimental["summary"]["focus_preset_direction_match_count"],
        )
        self.assertEqual(
            freq105["summary"]["focus_preset_direction_match_count"],
            14,
        )
        self.assertLess(
            freq105["summary"]["focus_preset_series_mae_mean"],
            freq110["summary"]["focus_preset_series_mae_mean"],
        )
        self.assertLess(
            freq105["summary"]["focus_preset_series_mae_mean"],
            gray_texture["summary"]["focus_preset_series_mae_mean"],
        )
        self.assertGreater(
            freq105["summary"]["focus_preset_direction_match_count"],
            nofreq["summary"]["focus_preset_direction_match_count"],
        )
        self.assertLess(
            nofreq["summary"]["focus_preset_series_mae_mean"],
            freq105["summary"]["focus_preset_series_mae_mean"],
        )
        self.assertLess(
            freq105["summary"]["focus_preset_gain_delta_mae_mean"],
            experimental["summary"]["focus_preset_gain_delta_mae_mean"],
        )


if __name__ == "__main__":
    unittest.main()
