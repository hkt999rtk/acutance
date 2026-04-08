from __future__ import annotations

import unittest

import numpy as np

from algo.benchmark_parity_psd_mtf import band_error_summary, resample_curve


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


if __name__ == "__main__":
    unittest.main()
