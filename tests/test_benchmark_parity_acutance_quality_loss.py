from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from algo.benchmark_parity_acutance_quality_loss import (
    Profile,
    build_acutance_presets,
    choose_roi,
    mean_named_metrics,
)
from algo.dead_leaves import RoiBounds
from algo.parity_benchmark_common import derive_reference_correction_curve
from algo.parity_benchmark_common import apply_reference_correction_curve
from algo.benchmark_parity_psd_mtf import Profile as PsdProfile


class BenchmarkParityAcutanceQualityLossTest(unittest.TestCase):
    def test_mean_named_metrics_averages_named_series(self) -> None:
        values = {
            "a": [1.0, 3.0],
            "b": [2.0, 4.0],
        }
        self.assertEqual(mean_named_metrics(values, ("a", "b")), 2.5)

    def test_build_acutance_presets_applies_named_override(self) -> None:
        presets = build_acutance_presets(
            {
                '5.5" Phone Display Acutance': {
                    "viewing_distance_cm": 25.55,
                }
            }
        )
        phone = next(preset for preset in presets if preset.name == '5.5" Phone Display Acutance')
        monitor = next(preset for preset in presets if preset.name == "Computer Monitor Acutance")

        self.assertEqual(phone.picture_height_cm, 5.1)
        self.assertEqual(phone.viewing_distance_cm, 25.55)
        self.assertEqual(monitor.viewing_distance_cm, 39.3)

    def test_choose_roi_reference_refined_uses_reference_seed(self) -> None:
        image = np.zeros((20, 20), dtype=np.float32)
        reference = SimpleNamespace(lrtb=RoiBounds(left=4, right=9, top=5, bottom=10))
        profile = Profile(name="p", calibration_file="c", roi_source="reference_refined")
        expected = RoiBounds(left=1, right=2, top=3, bottom=4)
        with patch(
            "algo.benchmark_parity_acutance_quality_loss.refine_roi_to_texture_support",
            return_value=expected,
        ) as refine:
            actual = choose_roi(profile, reference, image)
        self.assertEqual(actual, expected)
        self.assertEqual(refine.call_args.kwargs["seed_roi"], reference.lrtb)

    def test_reference_correction_curve_is_clipped(self) -> None:
        correction = derive_reference_correction_curve(
            np.array([0.1, 0.2], dtype=np.float64),
            np.array([2.0, 0.1], dtype=np.float64),
            np.array([0.1, 0.2], dtype=np.float64),
            np.array([0.5, 0.5], dtype=np.float64),
            clip_lo=0.75,
            clip_hi=1.25,
        )
        np.testing.assert_allclose(correction, [1.25, 0.75])

    def test_reference_correction_curve_can_be_blended_by_frequency(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.ones(3, dtype=np.float64),
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.array([2.0, 2.0, 2.0], dtype=np.float64),
            strength=0.5,
            blend_start_cpp=0.1,
            blend_stop_cpp=0.3,
        )
        np.testing.assert_allclose(corrected, [1.0, 1.25, 1.5])

    def test_reference_correction_curve_supports_piecewise_strength(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.ones(3, dtype=np.float64),
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.array([2.0, 2.0, 2.0], dtype=np.float64),
            strength=1.0,
            strength_low=0.5,
            strength_high=1.0,
            strength_ramp_start_cpp=0.1,
            strength_ramp_stop_cpp=0.3,
        )
        np.testing.assert_allclose(corrected, [1.5, 1.75, 2.0])

    def test_psd_profile_allows_acutance_only_anchor_mode(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_reference_anchor=True,
            matched_ori_anchor_mode="acutance_only",
        )
        self.assertEqual(profile.matched_ori_anchor_mode, "acutance_only")


if __name__ == "__main__":
    unittest.main()
