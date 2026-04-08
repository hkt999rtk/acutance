from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BenchmarkAmodelGainHypothesesE2ETest(unittest.TestCase):
    def test_cli_reproduces_checked_in_gain_hypothesis_alignment(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        dataset_root = repo_root / "20260318_deadleaf_13b10" / "output3_Amodel"
        if not dataset_root.exists():
            self.skipTest(f"Dataset missing: {dataset_root}")

        checked_in = json.loads(
            (repo_root / "artifacts" / "amodel_gain_hypothesis_benchmark.json").read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "amodel_gain_hypothesis_benchmark.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "algo.benchmark_amodel_gain_hypotheses",
                    "20260318_deadleaf_13b10/output3_Amodel",
                    "release/deadleaf_13b10_release/config/parity_fit_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gain_noise_profile.release.json",
                    "release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json",
                    "release/deadleaf_13b10_release/config/experimental_shape_profile.release.json",
                    "--output",
                    str(output_path),
                ],
                check=True,
                cwd=repo_root,
            )
            regenerated = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(
            regenerated["baseline"]["profile_name"], checked_in["baseline"]["profile_name"]
        )
        self.assertEqual(
            [entry["profile_name"] for entry in regenerated["hypotheses"]],
            [entry["profile_name"] for entry in checked_in["hypotheses"]],
        )

        self.assertEqual(
            regenerated["baseline"]["summary"], checked_in["baseline"]["summary"]
        )

        hypothesis_names = (
            "deadleaf_13b10_release_parity_gain_noise_hypothesis",
            "deadleaf_13b10_release_parity_gain_shape_hypothesis",
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
            self.assertEqual(
                {
                    key: value
                    for key, value in actual["comparison_vs_baseline"].items()
                    if key != "presets"
                },
                {
                    key: value
                    for key, value in expected["comparison_vs_baseline"].items()
                    if key != "presets"
                },
            )
            for preset_name in (
                "Computer Monitor Acutance",
                "UHDTV Display Acutance",
                "Large Print Acutance",
            ):
                self.assertEqual(
                    actual["comparison_vs_baseline"]["presets"][preset_name],
                    expected["comparison_vs_baseline"]["presets"][preset_name],
                )

        baseline = regenerated["baseline"]
        parity_shape = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_parity_gain_shape_hypothesis"
        )
        experimental = next(
            entry
            for entry in regenerated["hypotheses"]
            if entry["profile_name"] == "deadleaf_13b10_release_experimental_shape"
        )

        self.assertGreater(
            parity_shape["comparison_vs_baseline"]["focus_preset_gain_delta_mae_improvement"], 0.0
        )
        self.assertEqual(
            parity_shape["comparison_vs_baseline"]["focus_preset_direction_match_delta"], 0
        )
        self.assertGreater(
            experimental["comparison_vs_baseline"]["focus_preset_direction_match_delta"], 0
        )

        large_print = parity_shape["comparison_vs_baseline"]["presets"]["Large Print Acutance"]
        self.assertLess(
            large_print["hypothesis_predicted_mean_gain_delta"],
            large_print["baseline_predicted_mean_gain_delta"],
        )
        self.assertLess(large_print["reported_mean_gain_delta"], 0.0)
        self.assertGreater(large_print["hypothesis_predicted_mean_gain_delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
