import unittest
from pathlib import Path

from algo.dead_leaves import parse_imatest_random_csv


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_RESULTS = ROOT / "20260318_deadleaf_13b10" / "OV13B10_AI_NR_OV13B10_ori" / "Results"


class GoldenSampleObservableTest(unittest.TestCase):
    def test_parser_exposes_observable_fields_from_golden_csvs(self) -> None:
        expected = {
            "OV13b10_AG15.5_ET2800_deadleaf_12M_60_R_Random.csv": {
                "image_shape": (4032, 3024),
                "crop": (1669, 1653),
                "lrtb": (1194, 2862, 647, 2299),
            },
            "OV13b10_AG1_ET40000_deadleaf_12M_1_R_Random.csv": {
                "image_shape": (4032, 3024),
                "crop": (1673, 1656),
                "lrtb": (1194, 2866, 646, 2301),
            },
            "OV13b10_AG4_ET11000_deadleaf_12M_20_R_Random.csv": {
                "image_shape": (4032, 3024),
                "crop": (1673, 1656),
                "lrtb": (1194, 2866, 646, 2301),
            },
            "OV13b10_AG8_ET5500_deadleaf_12M_40_R_Random.csv": {
                "image_shape": (4032, 3024),
                "crop": (1673, 1656),
                "lrtb": (1194, 2866, 646, 2301),
            },
        }

        for name, observable in expected.items():
            parsed = parse_imatest_random_csv(GOLDEN_RESULTS / name)
            self.assertEqual(parsed.image_shape, observable["image_shape"])
            self.assertEqual(parsed.crop, observable["crop"])
            self.assertEqual(
                (parsed.lrtb.left, parsed.lrtb.right, parsed.lrtb.top, parsed.lrtb.bottom),
                observable["lrtb"],
            )
            self.assertEqual(parsed.report_gamma, 0.5)
            self.assertEqual(parsed.color_channel, "R")
            self.assertEqual(parsed.max_detected_frequency_cpp, 0.498)
            self.assertTrue(parsed.use_unnormalized_mtf_for_acutance)
            self.assertEqual(len(parsed.frequencies_cpp), 64)
            self.assertEqual(len(parsed.acutance_table), 100)


if __name__ == "__main__":
    unittest.main()
