from __future__ import annotations

import unittest

from algo.benchmark_amodel_gain_trend import classify_direction, parse_gain_value


class BenchmarkAmodelGainTrendTest(unittest.TestCase):
    def test_parse_gain_value_reads_decimal_gain_from_filename(self) -> None:
        gain = parse_gain_value(
            "OV13b10_AG15.5_ET2800_deadleaf_12M_60_denoised_A_model_mixup04_R_Random.csv"  # type: ignore[arg-type]
        )
        self.assertEqual(gain, 15.5)

    def test_classify_direction_uses_flat_epsilon_band(self) -> None:
        self.assertEqual(classify_direction(0.003, flat_epsilon=0.002), "up")
        self.assertEqual(classify_direction(-0.003, flat_epsilon=0.002), "down")
        self.assertEqual(classify_direction(0.001, flat_epsilon=0.002), "flat")


if __name__ == "__main__":
    unittest.main()
