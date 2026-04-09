from __future__ import annotations

import unittest

import numpy as np

from algo.dead_leaves import (
    RawLinearization,
    apply_mtf_compensation,
    estimate_mtf_compensation_curve,
    linearize_raw,
)


class DeadLeavesMtfCompensationTest(unittest.TestCase):
    def test_toe_power_linearization_lifts_dark_values_before_gamma(self) -> None:
        raw = np.array([0.0, 100.0, 1000.0], dtype=np.float32)
        base = linearize_raw(
            raw,
            config=RawLinearization(black_level=0.0, white_level=1000.0, gamma=0.5),
        )
        toe = linearize_raw(
            raw,
            config=RawLinearization(
                black_level=0.0,
                white_level=1000.0,
                gamma=0.5,
                mode="toe_power",
                toe=0.12,
            ),
        )
        self.assertGreater(toe[1], base[1])
        self.assertAlmostEqual(toe[-1], 1.0)

    def test_sensor_aperture_compensation_leaves_dc_unchanged(self) -> None:
        frequencies = np.array([0.0, 0.1, 0.25, 0.5], dtype=np.float64)
        compensation = estimate_mtf_compensation_curve(
            frequencies,
            mode="sensor_aperture_sinc",
            sensor_fill_factor=1.5,
        )
        self.assertAlmostEqual(compensation[0], 1.0)
        self.assertGreater(compensation[-1], compensation[1])

    def test_sensor_aperture_compensation_respects_gain_clip(self) -> None:
        frequencies = np.array([0.45, 0.5], dtype=np.float64)
        compensation = estimate_mtf_compensation_curve(
            frequencies,
            mode="sensor_aperture_sinc",
            sensor_fill_factor=1.5,
            denominator_clip=0.05,
            max_gain=2.0,
        )
        np.testing.assert_allclose(compensation, [2.0, 2.0])

    def test_apply_mtf_compensation_multiplies_curve(self) -> None:
        frequencies = np.array([0.0, 0.25, 0.5], dtype=np.float64)
        mtf = np.array([1.0, 0.8, 0.4], dtype=np.float64)
        corrected, compensation = apply_mtf_compensation(
            mtf,
            frequencies,
            mode="sensor_aperture_sinc",
            sensor_fill_factor=1.5,
            max_gain=3.0,
        )
        np.testing.assert_allclose(corrected, mtf * compensation)
        self.assertGreater(corrected[-1], mtf[-1])


if __name__ == "__main__":
    unittest.main()
