from __future__ import annotations

import unittest

from algo.benchmark_parity_acutance_quality_loss import mean_named_metrics


class BenchmarkParityAcutanceQualityLossTest(unittest.TestCase):
    def test_mean_named_metrics_averages_named_series(self) -> None:
        values = {
            "a": [1.0, 3.0],
            "b": [2.0, 4.0],
        }
        self.assertEqual(mean_named_metrics(values, ("a", "b")), 2.5)


if __name__ == "__main__":
    unittest.main()
