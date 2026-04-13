from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from algo.build_intrinsic_after_issue97_next_slice import (
    CURRENT_BEST_LABEL,
    ISSUE97_LABEL,
    SELECTED_SLICE_ID,
    build_payload,
    render_markdown,
)


class BuildIntrinsicAfterIssue97NextSliceTest(unittest.TestCase):
    def test_payload_selects_readout_only_sensor_aperture_compensation(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue95_artifact_path=Path("artifacts/intrinsic_after_issue93_next_slice_benchmark.json"),
            issue93_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"
            ),
            issue97_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"
            ),
            current_best_psd_artifact_path=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
            issue93_psd_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"
            ),
            issue97_psd_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"
            ),
        )

        self.assertEqual(payload["issue"], 99)
        self.assertEqual(payload["summary_kind"], "intrinsic_after_issue97_next_slice")
        self.assertEqual(payload["selected_slice_id"], SELECTED_SLICE_ID)
        selected = next(
            row for row in payload["candidate_slices"] if row["slice_id"] == SELECTED_SLICE_ID
        )
        self.assertIn("sensor_aperture_sinc", selected["selected_summary"])
        self.assertIn("compensated_mtf_for_acutance", selected["minimum_implementation_boundary"][2])
        self.assertTrue(
            payload["residual_gap_evidence"]["issue97_preserves_issue93_core_record"][
                "overall_quality_loss_mae_mean"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue97_threshold_tradeoff_vs_issue93"][
                "mtf_abs_signed_rel_regressed"
            ]
        )
        self.assertTrue(
            payload["residual_gap_evidence"]["issue97_band_signed_rel_direction"]["high"][
                "issue97_flips_negative_vs_issue93"
            ]
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["mtf_compensation_mode"][ISSUE97_LABEL], "none"
        )
        self.assertEqual(
            payload["pipeline_delta_summary"]["mtf_compensation_mode"][CURRENT_BEST_LABEL],
            "sensor_aperture_sinc",
        )
        self.assertEqual(
            payload["comparison_records"]["issue93_downstream_matched_ori_only_candidate"][
                "mtf_abs_signed_rel_mean"
            ],
            0.13993778559089318,
        )
        for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
            self.assertFalse(path.startswith("20260318_deadleaf_13b10"))
            self.assertFalse(
                path.startswith("release/deadleaf_13b10_release/data/20260318_deadleaf_13b10")
            )

    def test_markdown_mentions_band_sign_flip_and_compensation_slice(self) -> None:
        payload = build_payload(
            self.repo_root(),
            issue95_artifact_path=Path("artifacts/intrinsic_after_issue93_next_slice_benchmark.json"),
            issue93_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"
            ),
            issue97_artifact_path=Path(
                "artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"
            ),
            current_best_psd_artifact_path=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
            issue93_psd_artifact_path=Path(
                "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"
            ),
            issue97_psd_artifact_path=Path(
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"
            ),
        )
        markdown = render_markdown(payload)

        self.assertIn("# Intrinsic After Issue 97 Next Slice", markdown)
        self.assertIn("## Band Direction Evidence", markdown)
        self.assertIn("sensor-aperture compensation", markdown)
        self.assertIn("issue97_flips_negative_vs_issue93", markdown)
        self.assertIn("high_frequency_guard_start_cpp", markdown)
        self.assertIn("Storage Separation", markdown)

    def test_build_payload_fails_when_issue97_embedded_issue93_copy_diverges(self) -> None:
        repo_root = self.repo_root()
        source_artifact = repo_root / "artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"
        diverged = json.loads(source_artifact.read_text(encoding="utf-8"))
        diverged["profiles"]["issue93_downstream_matched_ori_only_candidate"][
            "mtf_abs_signed_rel_mean"
        ] = 9.999

        with tempfile.TemporaryDirectory() as tmpdir:
            diverged_path = Path(tmpdir) / "issue93_diverged.json"
            diverged_path.write_text(
                json.dumps(diverged, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError, "embedded issue93_downstream_matched_ori_only_candidate record diverges"
            ):
                build_payload(
                    repo_root,
                    issue95_artifact_path=Path(
                        "artifacts/intrinsic_after_issue93_next_slice_benchmark.json"
                    ),
                    issue93_artifact_path=diverged_path,
                    issue97_artifact_path=Path(
                        "artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"
                    ),
                    current_best_psd_artifact_path=Path(
                        "artifacts/issue77_measured_oecf_psd_benchmark.json"
                    ),
                    issue93_psd_artifact_path=Path(
                        "artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"
                    ),
                    issue97_psd_artifact_path=Path(
                        "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"
                    ),
                )

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
