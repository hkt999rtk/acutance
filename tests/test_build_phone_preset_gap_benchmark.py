from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_phone_preset_gap_benchmark import build_phone_preset_gap_benchmark


class BuildPhonePresetGapBenchmarkTest(unittest.TestCase):
    def test_issue61_proxy_example_keeps_trend_guard_and_exposes_tradeoff(self) -> None:
        payload = build_phone_preset_gap_benchmark(
            repo_root=self.repo_root(),
            psd_artifact_path=Path("artifacts/issue61_isp_family_psd_benchmark.json"),
            acutance_artifact_path=Path("artifacts/issue61_isp_family_acutance_benchmark.json"),
            baseline_profile_path=Path(
                "algo/"
                "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
                "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
                "psd_roi_reference_only_profile.json"
            ),
            candidate_profile_path=Path(
                "algo/"
                "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
                "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
                "psd_roi_reference_only_hf_noise_share_shape_profile.json"
            ),
            trend_profile_path=Path(
                "release/deadleaf_13b10_release/config/parity_fit_profile.release.json"
            ),
        )

        self.assertEqual(payload["issue"], 70)
        self.assertEqual(
            payload["trend_guard"]["trend_correctness"]["match_count"],
            3,
        )
        self.assertEqual(
            payload["trend_guard"]["trend_correctness"]["group_count"],
            20,
        )
        self.assertAlmostEqual(
            payload["trend_guard"]["gain_trend_series_shape_error"],
            0.018628257751567734,
        )
        self.assertTrue(payload["acceptance"]["phone_acutance_improved"])
        self.assertTrue(payload["acceptance"]["phone_quality_loss_improved"])
        self.assertFalse(payload["acceptance"]["curve_mae_mean_improved"])
        self.assertTrue(payload["acceptance"]["mtf_thresholds_non_worse"])
        self.assertFalse(payload["acceptance"]["all_primary_gates_pass"])

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
