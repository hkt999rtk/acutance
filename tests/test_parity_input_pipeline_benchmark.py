from __future__ import annotations

import unittest

from algo.benchmark_parity_input_pipeline import mean_abs_signed_rel, selection_tuple


class BenchmarkParityInputPipelineTest(unittest.TestCase):
    def test_mean_abs_signed_rel_uses_all_mtf_bands(self) -> None:
        payload = {
            "overall": {
                "bands": {
                    "mtf": {
                        "low": {"signed_rel_mean": -0.10},
                        "mid": {"signed_rel_mean": 0.40},
                        "high": {"signed_rel_mean": -0.70},
                        "top": {"signed_rel_mean": -0.80},
                    }
                }
            }
        }
        self.assertEqual(
            mean_abs_signed_rel(payload),
            (0.10 + 0.40 + 0.70 + 0.80) / 4.0,
        )

    def test_selection_tuple_orders_by_curve_then_mtf_then_quality_loss(self) -> None:
        result = {
            "curve_mae_mean": 0.05,
            "mtf_abs_signed_rel_mean": 0.25,
            "overall_quality_loss_mae_mean": 3.5,
        }
        self.assertEqual(selection_tuple(result), (0.05, 0.25, 3.5))
