from __future__ import annotations

import unittest

from algo.benchmark_amodel_gain_hypotheses import summarize_against_baseline


class BenchmarkAmodelGainHypothesesTest(unittest.TestCase):
    def test_summarize_against_baseline_reports_improvements_and_direction_delta(self) -> None:
        baseline = {
            "summary": {
                "focus_preset_gain_delta_mae_mean": 0.020,
                "focus_preset_series_mae_mean": 0.030,
                "focus_preset_direction_match_count": 3,
                "focus_preset_direction_group_count": 20,
            },
            "presets": {
                "Preset A": {
                    "reported_mean_gain_delta": -0.005,
                    "predicted_mean_gain_delta": 0.010,
                    "gain_delta_mae_mean": 0.015,
                    "series_mae_mean": 0.025,
                    "direction_match_count": 0,
                    "direction_group_count": 4,
                }
            },
        }
        hypothesis = {
            "summary": {
                "focus_preset_gain_delta_mae_mean": 0.012,
                "focus_preset_series_mae_mean": 0.028,
                "focus_preset_direction_match_count": 7,
                "focus_preset_direction_group_count": 20,
            },
            "presets": {
                "Preset A": {
                    "reported_mean_gain_delta": -0.005,
                    "predicted_mean_gain_delta": -0.001,
                    "gain_delta_mae_mean": 0.006,
                    "series_mae_mean": 0.020,
                    "direction_match_count": 3,
                    "direction_group_count": 4,
                }
            },
        }

        summary = summarize_against_baseline(baseline, hypothesis)

        self.assertAlmostEqual(summary["focus_preset_gain_delta_mae_delta"], -0.008)
        self.assertAlmostEqual(summary["focus_preset_gain_delta_mae_improvement"], 0.008)
        self.assertAlmostEqual(summary["focus_preset_series_mae_delta"], -0.002)
        self.assertAlmostEqual(summary["focus_preset_series_mae_improvement"], 0.002)
        self.assertEqual(summary["focus_preset_direction_match_delta"], 4)
        self.assertEqual(summary["focus_preset_direction_group_count"], 20)
        preset = summary["presets"]["Preset A"]
        self.assertAlmostEqual(preset["predicted_mean_gain_delta_delta"], -0.011)
        self.assertAlmostEqual(preset["gain_delta_mae_improvement"], 0.009)
        self.assertAlmostEqual(preset["series_mae_improvement"], 0.005)
        self.assertEqual(preset["direction_match_delta"], 3)


if __name__ == "__main__":
    unittest.main()
