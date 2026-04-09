from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from algo.benchmark_parity_psd_mtf import Profile, band_error_summary, choose_roi, resample_curve
from algo.dead_leaves import RoiBounds
from algo.parity_benchmark_common import capture_key_from_stem


class BenchmarkParityPsdMtfTest(unittest.TestCase):
    def test_resample_curve_interpolates_in_order(self) -> None:
        source_f = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        source_v = np.array([1.0, 3.0, 5.0], dtype=np.float64)
        ref_f = np.array([0.5, 1.5], dtype=np.float64)
        np.testing.assert_allclose(resample_curve(source_f, source_v, ref_f), [2.0, 4.0])

    def test_band_error_summary_reports_signed_relative_error(self) -> None:
        frequencies = np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64)
        estimate = np.array([0.9, 0.8, 0.7, 0.6], dtype=np.float64)
        reference = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)
        summary = band_error_summary(frequencies, estimate, reference)
        self.assertAlmostEqual(summary["low"]["signed_rel_mean"], -0.1)
        self.assertAlmostEqual(summary["mid"]["signed_rel_mean"], -0.2)
        self.assertAlmostEqual(summary["high"]["signed_rel_mean"], -0.3)
        self.assertAlmostEqual(summary["top"]["signed_rel_mean"], -0.4)

    def test_choose_roi_reference_refined_uses_reference_seed(self) -> None:
        image = np.zeros((20, 20), dtype=np.float32)
        reference = SimpleNamespace(lrtb=RoiBounds(left=4, right=9, top=5, bottom=10))
        profile = Profile(name="p", calibration_file="c", roi_source="reference_refined")
        expected = RoiBounds(left=1, right=2, top=3, bottom=4)
        with patch("algo.benchmark_parity_psd_mtf.refine_roi_to_texture_support", return_value=expected) as refine:
            actual = choose_roi(profile, reference, image)
        self.assertEqual(actual, expected)
        self.assertEqual(refine.call_args.kwargs["seed_roi"], reference.lrtb)

    def test_capture_key_from_stem_strips_denoise_suffix(self) -> None:
        self.assertEqual(
            capture_key_from_stem("OV13b10_AG8_ET5500_deadleaf_12M_40_denoised_A_model_mixup04"),
            "OV13b10_AG8_ET5500_deadleaf_12M_40",
        )


if __name__ == "__main__":
    unittest.main()
