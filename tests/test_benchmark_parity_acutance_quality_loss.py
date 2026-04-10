from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from algo.benchmark_parity_acutance_quality_loss import (
    Profile,
    build_acutance_presets,
    build_parser,
    choose_roi,
    mean_named_metrics,
)
from algo.dead_leaves import AcutancePoint, RoiBounds
from algo.parity_benchmark_common import (
    align_patch_phase_correlation,
    apply_quantile_transfer_curve,
    apply_reference_correction_curve,
    clip_reference_correction_curve,
    derive_quantile_transfer_curve,
    derive_reference_acutance_correction_curve,
    derive_reference_correction_curve,
    derive_intrinsic_transfer_curve,
)
from algo.benchmark_parity_psd_mtf import Profile as PsdProfile


class BenchmarkParityAcutanceQualityLossTest(unittest.TestCase):
    def test_build_parser_supports_acutance_and_quality_record_flags(self) -> None:
        args = build_parser().parse_args(
            [
                "dataset",
                "profile.json",
                "--include-acutance-records",
                "--include-quality-loss-records",
            ]
        )
        self.assertTrue(args.include_acutance_records)
        self.assertTrue(args.include_quality_loss_records)

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

    def test_quantile_transfer_curve_is_monotonic_and_anchored(self) -> None:
        source_values, target_values = derive_quantile_transfer_curve(
            np.array([[0.0, 0.2], [0.4, 1.0]], dtype=np.float32),
            np.array([[0.0, 0.1], [0.3, 1.0]], dtype=np.float32),
            quantiles=(0.0, 0.25, 0.5, 0.75, 1.0),
        )
        self.assertEqual(source_values[0], 0.0)
        self.assertEqual(target_values[0], 0.0)
        self.assertEqual(source_values[-1], 1.0)
        self.assertEqual(target_values[-1], 1.0)
        self.assertTrue(np.all(np.diff(source_values) > 0.0))
        self.assertTrue(np.all(np.diff(target_values) >= 0.0))

    def test_quantile_transfer_curve_blends_by_strength(self) -> None:
        corrected = apply_quantile_transfer_curve(
            np.array([0.0, 0.25, 0.5, 1.0], dtype=np.float32),
            np.array([0.0, 0.5, 1.0], dtype=np.float64),
            np.array([0.0, 0.25, 1.0], dtype=np.float64),
            strength=0.5,
        )
        np.testing.assert_allclose(corrected, [0.0, 0.1875, 0.375, 1.0])

    def test_reference_correction_curve_supports_delta_power(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.1, 0.2], dtype=np.float64),
            np.ones(2, dtype=np.float64),
            np.array([0.1, 0.2], dtype=np.float64),
            np.array([1.25, 0.75], dtype=np.float64),
            correction_delta_power=2.0,
        )
        np.testing.assert_allclose(corrected, [1.0625, 0.9375])

    def test_reference_correction_curve_supports_delta_power_curve(self) -> None:
        corrected = apply_reference_correction_curve(
            np.array([0.1, 0.2], dtype=np.float64),
            np.ones(2, dtype=np.float64),
            np.array([0.1, 0.2], dtype=np.float64),
            np.array([1.25, 1.25], dtype=np.float64),
            correction_delta_power_positions=[0.0, 0.15, 0.25],
            correction_delta_power_values=[1.0, 1.0, 2.0],
        )
        np.testing.assert_allclose(corrected, [1.25, 1.125])

    def test_clip_reference_correction_curve_supports_variable_hi_curve(self) -> None:
        clipped = clip_reference_correction_curve(
            np.array([0.0, 0.5, 1.0], dtype=np.float64),
            np.array([1.08, 1.08, 1.08], dtype=np.float64),
            clip_lo=0.9,
            clip_hi=1.1,
            clip_hi_positions=[0.0, 0.5, 1.0],
            clip_hi_values=[1.02, 1.04, 1.06],
        )
        np.testing.assert_allclose(clipped, [1.02, 1.04, 1.06])

    def test_clip_reference_correction_curve_supports_variable_lo_curve(self) -> None:
        clipped = clip_reference_correction_curve(
            np.array([0.0, 0.5, 1.0], dtype=np.float64),
            np.array([0.92, 0.95, 1.08], dtype=np.float64),
            clip_lo=0.9,
            clip_hi=1.2,
            clip_lo_positions=[0.0, 0.5, 1.0],
            clip_lo_values=[0.96, 0.98, 1.00],
        )
        np.testing.assert_allclose(clipped, [0.96, 0.98, 1.08])

    def test_preset_reference_correction_uses_correction_positions_for_clip_shape(self) -> None:
        correction_positions = np.array([1.0, 2.0, 4.0, 6.0], dtype=np.float64)
        correction_curve = np.array([1.08, 1.10, 1.14, 1.20], dtype=np.float64)
        preset_positions = np.array([1.5, 5.8], dtype=np.float64)
        clipped_curve = clip_reference_correction_curve(
            correction_positions,
            correction_curve,
            clip_lo=0.9,
            clip_hi=1.2,
            clip_hi_positions=[0.0, 4.5, 5.8, 6.2],
            clip_hi_values=[1.10, 1.10, 1.12, 1.12],
        )
        corrected = apply_reference_correction_curve(
            preset_positions,
            np.ones(2, dtype=np.float64),
            correction_positions,
            clipped_curve,
        )
        np.testing.assert_allclose(clipped_curve, [1.08, 1.10, 1.10, 1.12])
        np.testing.assert_allclose(corrected, [1.09, 1.118])

    def test_preset_reference_correction_uses_correction_positions_for_lo_clip_shape(self) -> None:
        correction_positions = np.array([1.0, 2.0, 5.8, 6.0], dtype=np.float64)
        correction_curve = np.array([0.92, 0.94, 0.97, 1.01], dtype=np.float64)
        clipped_curve = clip_reference_correction_curve(
            correction_positions,
            correction_curve,
            clip_lo=0.9,
            clip_hi=1.1,
            clip_lo_positions=[0.0, 4.5, 5.8, 6.2],
            clip_lo_values=[0.90, 0.90, 0.98, 0.98],
        )
        np.testing.assert_allclose(clipped_curve, [0.92, 0.94, 0.98, 1.01])

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

    def test_phase_correlation_alignment_recovers_simple_translation(self) -> None:
        rng = np.random.default_rng(123)
        reference = rng.normal(size=(96, 96)).astype(np.float32)
        transform = np.array([[1.0, 0.0, 5.0], [0.0, 1.0, -3.0]], dtype=np.float32)
        observed = cv2.warpAffine(
            reference,
            transform,
            (reference.shape[1], reference.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )
        aligned, shift, response = align_patch_phase_correlation(reference, observed)
        self.assertGreater(response, 0.5)
        self.assertAlmostEqual(shift[0], 5.0, delta=0.5)
        self.assertAlmostEqual(shift[1], -3.0, delta=0.5)
        self.assertLess(float(np.mean(np.abs(aligned - reference))), 0.2)

    def test_intrinsic_transfer_curve_is_near_identity_for_registered_translation(self) -> None:
        rng = np.random.default_rng(123)
        reference = rng.normal(size=(96, 96)).astype(np.float32)
        transform = np.array([[1.0, 0.0, 4.0], [0.0, 1.0, 2.0]], dtype=np.float32)
        observed = cv2.warpAffine(
            reference,
            transform,
            (reference.shape[1], reference.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )
        transfer = derive_intrinsic_transfer_curve(
            reference,
            observed,
            bin_centers=np.linspace(0.01, 0.49, 32, dtype=np.float64),
            normalization_band=(0.01, 0.03),
            normalization_mode="mean",
            clip_lo=0.5,
            clip_hi=1.5,
            registration_mode="phase_correlation",
        )
        self.assertLess(float(np.mean(np.abs(transfer - 1.0))), 0.12)

    def test_intrinsic_transfer_curve_captures_high_frequency_rolloff(self) -> None:
        rng = np.random.default_rng(123)
        reference = rng.normal(size=(96, 96)).astype(np.float32)
        observed = cv2.GaussianBlur(reference, (0, 0), 1.4)
        transfer = derive_intrinsic_transfer_curve(
            reference,
            observed,
            bin_centers=np.linspace(0.01, 0.49, 32, dtype=np.float64),
            normalization_band=(0.01, 0.03),
            normalization_mode="mean",
            clip_lo=0.5,
            clip_hi=1.5,
            registration_mode="phase_correlation",
        )
        self.assertGreater(float(np.mean(transfer[:4])), float(np.mean(transfer[-4:])))
        self.assertLess(float(np.mean(transfer[-4:])), 0.85)

    def test_psd_profile_allows_acutance_only_anchor_mode(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_reference_anchor=True,
            matched_ori_anchor_mode="acutance_only",
        )
        self.assertEqual(profile.matched_ori_anchor_mode, "acutance_only")

    def test_psd_profile_allows_matched_ori_oecf_fields(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_oecf_reference=True,
            matched_ori_oecf_strength=0.4,
            matched_ori_oecf_quantiles=(0.0, 0.2, 0.5, 0.8, 1.0),
        )
        self.assertTrue(profile.matched_ori_oecf_reference)
        self.assertEqual(profile.matched_ori_oecf_strength, 0.4)
        self.assertEqual(profile.matched_ori_oecf_quantiles, (0.0, 0.2, 0.5, 0.8, 1.0))

    def test_psd_profile_allows_acutance_curve_anchor_fields(self) -> None:
        profile = PsdProfile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            matched_ori_acutance_reference_anchor=True,
            matched_ori_acutance_curve_correction_clip_hi=1.08,
            matched_ori_acutance_curve_correction_clip_lo_relative_scales=(0.0, 1.0, 2.0),
            matched_ori_acutance_curve_correction_clip_lo_values=(0.98, 0.99, 1.00),
            matched_ori_acutance_curve_correction_clip_hi_relative_scales=(0.0, 1.0, 2.0),
            matched_ori_acutance_curve_correction_clip_hi_values=(1.02, 1.04, 1.06),
            matched_ori_acutance_preset_correction_clip_hi=1.10,
            matched_ori_acutance_preset_correction_clip_lo_relative_scales=(0.0, 4.5, 5.8),
            matched_ori_acutance_preset_correction_clip_lo_values=(0.90, 0.95, 1.00),
            matched_ori_acutance_preset_correction_clip_hi_relative_scales=(0.0, 4.5, 5.8),
            matched_ori_acutance_preset_correction_clip_hi_values=(1.08, 1.10, 1.14),
            matched_ori_acutance_correction_strength=0.75,
            matched_ori_acutance_blend_start_relative_scale=2.5,
            matched_ori_acutance_blend_stop_relative_scale=5.5,
            matched_ori_acutance_strength_curve_relative_scales=(0.0, 3.0, 5.8),
            matched_ori_acutance_strength_curve_values=(1.0, 1.0, 0.4),
            matched_ori_acutance_correction_delta_power=1.4,
            matched_ori_acutance_curve_correction_delta_power=1.1,
            matched_ori_acutance_preset_correction_delta_power=1.2,
            matched_ori_acutance_preset_correction_delta_power_relative_scales=(0.0, 4.5, 5.8),
            matched_ori_acutance_preset_correction_delta_power_values=(1.0, 1.05, 1.15),
            matched_ori_acutance_preset_strength_curve_relative_scales=(0.0, 4.5, 5.8),
            matched_ori_acutance_preset_strength_curve_values=(1.0, 0.85, 0.45),
        )
        self.assertTrue(profile.matched_ori_acutance_reference_anchor)
        self.assertEqual(profile.matched_ori_acutance_curve_correction_clip_hi, 1.08)
        self.assertEqual(
            profile.matched_ori_acutance_curve_correction_clip_lo_relative_scales,
            (0.0, 1.0, 2.0),
        )
        self.assertEqual(
            profile.matched_ori_acutance_curve_correction_clip_lo_values,
            (0.98, 0.99, 1.00),
        )
        self.assertEqual(
            profile.matched_ori_acutance_curve_correction_clip_hi_relative_scales,
            (0.0, 1.0, 2.0),
        )
        self.assertEqual(
            profile.matched_ori_acutance_curve_correction_clip_hi_values,
            (1.02, 1.04, 1.06),
        )
        self.assertEqual(profile.matched_ori_acutance_preset_correction_clip_hi, 1.10)
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_clip_lo_relative_scales,
            (0.0, 4.5, 5.8),
        )
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_clip_lo_values,
            (0.90, 0.95, 1.00),
        )
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_clip_hi_relative_scales,
            (0.0, 4.5, 5.8),
        )
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_clip_hi_values,
            (1.08, 1.10, 1.14),
        )
        self.assertEqual(profile.matched_ori_acutance_correction_strength, 0.75)
        self.assertEqual(profile.matched_ori_acutance_blend_start_relative_scale, 2.5)
        self.assertEqual(profile.matched_ori_acutance_blend_stop_relative_scale, 5.5)
        self.assertEqual(profile.matched_ori_acutance_strength_curve_relative_scales, (0.0, 3.0, 5.8))
        self.assertEqual(profile.matched_ori_acutance_strength_curve_values, (1.0, 1.0, 0.4))
        self.assertEqual(profile.matched_ori_acutance_correction_delta_power, 1.4)
        self.assertEqual(profile.matched_ori_acutance_curve_correction_delta_power, 1.1)
        self.assertEqual(profile.matched_ori_acutance_preset_correction_delta_power, 1.2)
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_delta_power_relative_scales,
            (0.0, 4.5, 5.8),
        )
        self.assertEqual(
            profile.matched_ori_acutance_preset_correction_delta_power_values,
            (1.0, 1.05, 1.15),
        )
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
