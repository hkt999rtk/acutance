from __future__ import annotations

import unittest
from pathlib import Path

from algo.build_measured_oecf_followup import (
    MEASURED_OECF_LABEL,
    TOE_PROXY_LABEL,
    build_payload,
)


class BuildMeasuredOecfFollowupTest(unittest.TestCase):
    def test_payload_uses_issue77_paths_and_keeps_storage_separate(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
            acutance_artifact_path=Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"),
        )

        self.assertEqual(payload["issue"], 77)
        self.assertEqual(payload["summary_kind"], "imatest_parity_measured_oecf_followup")
        self.assertIn(
            "algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json",
            payload["storage"]["new_fitted_artifact_paths"],
        )
        self.assertEqual(
            payload["profiles"][MEASURED_OECF_LABEL]["profile_path"],
            "algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json",
        )
        for path in payload["storage"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_measured_oecf_candidate_is_distinct_from_toe_proxy(self) -> None:
        payload = build_payload(
            self.repo_root(),
            psd_artifact_path=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
            acutance_artifact_path=Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"),
        )

        measured = payload["profiles"][MEASURED_OECF_LABEL]
        toe = payload["profiles"][TOE_PROXY_LABEL]
        self.assertNotEqual(measured["profile_path"], toe["profile_path"])
        self.assertIn("matched_ori_oecf_reference", measured["analysis_pipeline"])
        self.assertTrue(measured["analysis_pipeline"]["matched_ori_oecf_reference"])
        self.assertEqual(payload["conclusion"]["status"], "bounded_negative")

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
