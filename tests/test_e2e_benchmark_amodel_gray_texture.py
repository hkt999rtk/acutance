from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BenchmarkAmodelGrayTextureE2ETest(unittest.TestCase):
    def test_cli_reproduces_checked_in_gray_texture_factor_alignment(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        dataset_root = repo_root / "20260318_deadleaf_13b10" / "output3_Amodel"
        if not dataset_root.exists():
            self.skipTest(f"Dataset missing: {dataset_root}")

        checked_in = json.loads(
            (repo_root / "artifacts" / "amodel_gray_texture_benchmark.json").read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "amodel_gray_texture_benchmark.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "algo.benchmark_amodel_gain_hypotheses",
                    "20260318_deadleaf_13b10/output3_Amodel",
                    "release/deadleaf_13b10_release/config/parity_fit_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_shape_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_texture_shape_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json",
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

        hypothesis_names = (
            "deadleaf_13b10_release_parity_gain_shape_hypothesis",
            "deadleaf_13b10_release_parity_gray_shape_hypothesis",
            "deadleaf_13b10_release_parity_texture_shape_hypothesis",
            "deadleaf_13b10_release_parity_gray_texture_shape_hypothesis",
            "deadleaf_13b10_release_experimental_shape",
        )
        for hypothesis_name in hypothesis_names:
            expected = next(
                entry for entry in checked_in["hypotheses"] if entry["profile_name"] == hypothesis_name
            )
            actual = next(
                entry for entry in regenerated["hypotheses"] if entry["profile_name"] == hypothesis_name
            )
            self.assertEqual(actual["summary"], expected["summary"])

        parity_shape = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gain_shape_hypothesis"
        )
        gray_only = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_shape_hypothesis"
        )
        texture_only = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_texture_shape_hypothesis"
        )
        gray_texture = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gray_texture_shape_hypothesis"
        )
        experimental = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_experimental_shape"
        )

        self.assertEqual(
            gray_only["comparison_vs_baseline"]["focus_preset_direction_match_delta"], 0
        )
        self.assertEqual(
            texture_only["comparison_vs_baseline"]["focus_preset_direction_match_delta"], 0
        )
        self.assertGreater(
            gray_texture["comparison_vs_baseline"]["focus_preset_direction_match_delta"],
            experimental["comparison_vs_baseline"]["focus_preset_direction_match_delta"],
        )
        self.assertGreater(
            gray_texture["comparison_vs_baseline"]["focus_preset_gain_delta_mae_improvement"],
            experimental["comparison_vs_baseline"]["focus_preset_gain_delta_mae_improvement"],
        )
        self.assertGreater(
            gray_texture["comparison_vs_baseline"]["focus_preset_series_mae_delta"], 0.0
        )

        monitor = gray_texture["comparison_vs_baseline"]["presets"]["Computer Monitor Acutance"]
        uhdtv = gray_texture["comparison_vs_baseline"]["presets"]["UHDTV Display Acutance"]
        large_print = gray_texture["comparison_vs_baseline"]["presets"]["Large Print Acutance"]

        self.assertLess(
            monitor["hypothesis_predicted_mean_gain_delta"],
            monitor["baseline_predicted_mean_gain_delta"],
        )
        self.assertLess(
            uhdtv["hypothesis_predicted_mean_gain_delta"],
            uhdtv["baseline_predicted_mean_gain_delta"],
        )
        self.assertLess(large_print["hypothesis_predicted_mean_gain_delta"], 0.0)
        self.assertEqual(uhdtv["direction_match_delta"], 2)
        self.assertEqual(large_print["direction_match_delta"], 3)


if __name__ == "__main__":
    unittest.main()
