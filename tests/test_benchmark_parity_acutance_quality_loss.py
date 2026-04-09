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


if __name__ == "__main__":
    unittest.main()
