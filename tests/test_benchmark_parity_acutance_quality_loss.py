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
from algo.dead_leaves import AcutancePoint, RoiBounds
from algo.parity_benchmark_common import (
    apply_reference_correction_curve,
    derive_reference_acutance_correction_curve,
    derive_reference_correction_curve,
)
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

    def test_reference_correction_curve_supports_strength_curve(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.ones(3, dtype=np.float64),
            np.array([0.05, 0.2, 0.4], dtype=np.float64),
            np.array([2.0, 2.0, 2.0], dtype=np.float64),
            strength_curve_frequencies=[0.0, 0.2, 0.4],
            strength_curve_values=[1.0, 0.5, 1.0],
        )
        np.testing.assert_allclose(corrected, [1.875, 1.5, 2.0])

    def test_reference_correction_curve_supports_delta_power(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.1, 0.2], dtype=np.float64),
            np.ones(2, dtype=np.float64),
            np.array([0.1, 0.2], dtype=np.float64),
            np.array([1.25, 0.75], dtype=np.float64),
            correction_delta_power=2.0,
        )
        np.testing.assert_allclose(corrected, [1.0625, 0.9375])

    def test_reference_acutance_correction_curve_uses_relative_viewing_scale(self) -> None:
        positions, correction = derive_reference_acutance_correction_curve(
            [
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=0.5),
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=20.0, acutance=1.0),
            ],
            [
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=0.25),
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=20.0, acutance=4.0),
            ],
            clip_lo=0.5,
            clip_hi=1.5,
        )
        np.testing.assert_allclose(positions, [0.25, 0.5])
        np.testing.assert_allclose(correction, [1.5, 0.5])

    def test_reference_acutance_correction_curve_can_preserve_raw_ratio(self) -> None:
        positions, correction = derive_reference_acutance_correction_curve(
            [
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=0.5),
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=20.0, acutance=1.0),
            ],
            [
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=0.25),
                AcutancePoint(print_height_cm=40.0, viewing_distance_cm=20.0, acutance=4.0),
            ],
            clip_lo=None,
            clip_hi=None,
        )
        np.testing.assert_allclose(positions, [0.25, 0.5])
        np.testing.assert_allclose(correction, [2.0, 0.25])

    def test_psd_profile_allows_acutance_only_anchor_mode(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_reference_anchor=True,
            matched_ori_anchor_mode="acutance_only",
        )
        self.assertEqual(profile.matched_ori_anchor_mode, "acutance_only")

    def test_psd_profile_allows_acutance_curve_anchor_fields(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_acutance_reference_anchor=True,
            matched_ori_acutance_curve_correction_clip_hi=1.08,
            matched_ori_acutance_preset_correction_clip_hi=1.10,
            matched_ori_acutance_correction_strength=0.75,
            matched_ori_acutance_blend_start_relative_scale=2.5,
            matched_ori_acutance_blend_stop_relative_scale=5.5,
            matched_ori_acutance_strength_curve_relative_scales=(0.0, 3.0, 5.8),
            matched_ori_acutance_strength_curve_values=(1.0, 1.0, 0.4),
            matched_ori_acutance_correction_delta_power=1.4,
            matched_ori_acutance_preset_strength_curve_relative_scales=(0.0, 4.5, 5.8),
            matched_ori_acutance_preset_strength_curve_values=(1.0, 0.85, 0.45),
        )
        self.assertTrue(profile.matched_ori_acutance_reference_anchor)
        self.assertEqual(profile.matched_ori_acutance_curve_correction_clip_hi, 1.08)
        self.assertEqual(profile.matched_ori_acutance_preset_correction_clip_hi, 1.10)
        self.assertEqual(profile.matched_ori_acutance_correction_strength, 0.75)
        self.assertEqual(profile.matched_ori_acutance_blend_start_relative_scale, 2.5)
        self.assertEqual(profile.matched_ori_acutance_blend_stop_relative_scale, 5.5)
        self.assertEqual(profile.matched_ori_acutance_strength_curve_relative_scales, (0.0, 3.0, 5.8))
        self.assertEqual(profile.matched_ori_acutance_strength_curve_values, (1.0, 1.0, 0.4))
        self.assertEqual(profile.matched_ori_acutance_correction_delta_power, 1.4)
        self.assertEqual(
            profile.matched_ori_acutance_preset_strength_curve_relative_scales,
            (0.0, 4.5, 5.8),
        )
        self.assertEqual(
            profile.matched_ori_acutance_preset_strength_curve_values,
            (1.0, 0.85, 0.45),
        )


if __name__ == "__main__":
    unittest.main()
