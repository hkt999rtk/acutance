from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from algo.benchmark_parity_psd_mtf import (
    Profile,
    band_error_summary,
    choose_roi,
    profile_payload,
    resample_curve,
)
from algo.dead_leaves import AcutancePoint, RoiBounds
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

    def test_profile_allows_readout_policy_fields(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            readout_smoothing_window=7,
            readout_interpolation="linear",
        )
        self.assertEqual(profile.readout_smoothing_window, 7)
        self.assertEqual(profile.readout_interpolation, "linear")

    def test_choose_roi_reference_refined_uses_reference_seed(self) -> None:
        image = np.zeros((20, 20), dtype=np.float32)
        reference = SimpleNamespace(lrtb=RoiBounds(left=4, right=9, top=5, bottom=10))
        profile = Profile(name="p", calibration_file="c", roi_source="reference_refined")
        expected = RoiBounds(left=1, right=2, top=3, bottom=4)
        with patch("algo.benchmark_parity_psd_mtf.refine_roi_to_texture_support", return_value=expected) as refine:
            actual = choose_roi(profile, reference, image)
        self.assertEqual(actual, expected)
        self.assertEqual(refine.call_args.kwargs["seed_roi"], reference.lrtb)

    def test_profile_payload_uses_observable_table_frequency_bins(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=reference.frequencies_cpp,
                mtf=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                frequency_bin_source="observable_table",
                readout_smoothing_window=7,
                readout_interpolation="linear",
            )

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch("algo.benchmark_parity_psd_mtf.parse_imatest_random_csv", return_value=reference),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate) as estimate_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ),
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch("algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf", return_value=reference.acutance_table),
                patch("algo.benchmark_parity_psd_mtf.compare_acutance_curves", return_value={"count": 1, "mae": 0.0}),
                patch("algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf", return_value=reference.reported_acutance),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            self.assertEqual(estimate_mtf.call_count, 1)
            np.testing.assert_allclose(
                estimate_mtf.call_args.kwargs["bin_centers"],
                reference.frequencies_cpp,
            )
            self.assertEqual(
                estimate_mtf.call_args.kwargs["num_bins"],
                len(reference.frequencies_cpp),
            )
            self.assertEqual(estimate_mtf.call_args.kwargs["readout_smoothing_window"], 7)
            self.assertEqual(estimate_mtf.call_args.kwargs["readout_interpolation"], "linear")

    def test_capture_key_from_stem_strips_denoise_suffix(self) -> None:
        self.assertEqual(
            capture_key_from_stem("OV13b10_AG8_ET5500_deadleaf_12M_40_denoised_A_model_mixup04"),
            "OV13b10_AG8_ET5500_deadleaf_12M_40",
        )

    def test_profile_payload_recomputes_oecf_curve_for_variants_sharing_capture_key(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            for suffix in ("variantA", "variantB"):
                stem = f"{capture_key}_{suffix}"
                (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
                (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 0.9, 0.8, 0.7], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                matched_ori_oecf_reference=True,
            )

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch("algo.benchmark_parity_psd_mtf.parse_imatest_random_csv", return_value=reference),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_quantile_transfer_curve",
                    side_effect=[
                        (np.array([0.0, 1.0]), np.array([0.0, 0.8])),
                        (np.array([0.0, 1.0]), np.array([0.0, 0.6])),
                    ],
                ) as derive_curve,
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_quantile_transfer_curve",
                    side_effect=lambda image, *_args, **_kwargs: image,
                ),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ),
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch("algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf", return_value=reference.acutance_table),
                patch("algo.benchmark_parity_psd_mtf.compare_acutance_curves", return_value={"count": 1, "mae": 0.0}),
                patch("algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf", return_value=reference.reported_acutance),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            self.assertEqual(derive_curve.call_count, 2)

    def test_profile_allows_intrinsic_full_reference_mode(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            intrinsic_full_reference_mode="paired_ori_transfer",
        )
        self.assertEqual(profile.intrinsic_full_reference_mode, "paired_ori_transfer")

    def test_profile_allows_intrinsic_phase_retention_transfer_mode(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            intrinsic_full_reference_mode="paired_ori_transfer",
            intrinsic_full_reference_transfer_mode="radial_real_mean",
        )
        self.assertEqual(profile.intrinsic_full_reference_transfer_mode, "radial_real_mean")

    def test_profile_allows_hf_noise_share_shape_correction_fields(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            acutance_noise_scale_mode="high_frequency_noise_share_quadratic",
            mtf_shape_correction_mode="hf_noise_share_gated_bump",
        )
        self.assertEqual(profile.acutance_noise_scale_mode, "high_frequency_noise_share_quadratic")
        self.assertEqual(profile.mtf_shape_correction_mode, "hf_noise_share_gated_bump")

    def test_profile_allows_observable_table_frequency_bins(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            frequency_bin_source="observable_table",
        )
        self.assertEqual(profile.frequency_bin_source, "observable_table")

    def test_profile_allows_chart_fill_factor_for_compensation_family(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            mtf_compensation_mode="chart_sensor_aperture_sinc",
            chart_fill_factor=0.5,
        )
        self.assertEqual(profile.mtf_compensation_mode, "chart_sensor_aperture_sinc")
        self.assertEqual(profile.chart_fill_factor, 0.5)

    def test_profile_allows_empirical_linearization_percentiles(self) -> None:
        profile = Profile(
            name="test",
            calibration_file="algo/deadleaf_13b10_psd_calibration.json",
            black_percentile=0.0,
            white_percentile=99.5,
        )
        self.assertEqual(profile.black_percentile, 0.0)
        self.assertEqual(profile.white_percentile, 99.5)

    def test_intrinsic_scope_can_limit_full_reference_to_acutance_side_only(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            ori_reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=reference.acutance_table,
                reported_acutance=reference.reported_acutance,
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                intrinsic_full_reference_mode="paired_ori_transfer",
                intrinsic_full_reference_scope="acutance_only",
            )

            def parse_csv(path: Path):
                return ori_reference if path.name == "ori.csv" else reference

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.parse_imatest_random_csv",
                    side_effect=parse_csv,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_intrinsic_transfer_curve",
                    return_value=np.array([2.0, 2.0, 2.0, 2.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ) as compute_metrics,
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf",
                    return_value=reference.acutance_table,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_curves",
                    return_value={"count": 1, "mae": 0.0},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf",
                    return_value=reference.reported_acutance,
                ) as acutance_from_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            np.testing.assert_allclose(compute_metrics.call_args.args[1], [1.0, 1.0, 1.0, 1.0])
            np.testing.assert_allclose(acutance_from_mtf.call_args.args[1], [2.0, 2.0, 2.0, 2.0])

    def test_intrinsic_scope_can_isolate_quality_loss_without_changing_psd_semantics(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            ori_reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=reference.acutance_table,
                reported_acutance=reference.reported_acutance,
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                intrinsic_full_reference_mode="paired_ori_transfer",
                intrinsic_full_reference_scope="quality_loss_isolation",
            )

            def parse_csv(path: Path):
                return ori_reference if path.name == "ori.csv" else reference

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.parse_imatest_random_csv",
                    side_effect=parse_csv,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_intrinsic_transfer_curve",
                    return_value=np.array([2.0, 2.0, 2.0, 2.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ) as compute_metrics,
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf",
                    return_value=reference.acutance_table,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_curves",
                    return_value={"count": 1, "mae": 0.0},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf",
                    return_value=reference.reported_acutance,
                ) as acutance_from_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            np.testing.assert_allclose(compute_metrics.call_args.args[1], [1.0, 1.0, 1.0, 1.0])
            np.testing.assert_allclose(acutance_from_mtf.call_args.args[1], [2.0, 2.0, 2.0, 2.0])

    def test_intrinsic_scope_can_reconnect_readout_while_leaving_acutance_intrinsic(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            ori_reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=reference.acutance_table,
                reported_acutance=reference.reported_acutance,
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                intrinsic_full_reference_mode="paired_ori_transfer",
                intrinsic_full_reference_scope="readout_reconnect_quality_loss_isolation",
            )

            def parse_csv(path: Path):
                return ori_reference if path.name == "ori.csv" else reference

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.parse_imatest_random_csv",
                    side_effect=parse_csv,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_intrinsic_transfer_curve",
                    return_value=np.array([2.0, 2.0, 2.0, 2.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ) as compute_metrics,
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf",
                    return_value=reference.acutance_table,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_curves",
                    return_value={"count": 1, "mae": 0.0},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf",
                    return_value=reference.reported_acutance,
                ) as acutance_from_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            np.testing.assert_allclose(compute_metrics.call_args.args[1], [2.0, 2.0, 2.0, 2.0])
            np.testing.assert_allclose(acutance_from_mtf.call_args.args[1], [2.0, 2.0, 2.0, 2.0])

    def test_intrinsic_scope_can_graft_matched_ori_to_readout_only(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            ori_reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=reference.acutance_table,
                reported_acutance=reference.reported_acutance,
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                intrinsic_full_reference_mode="paired_ori_transfer",
                intrinsic_full_reference_scope=(
                    "readout_reconnect_quality_loss_isolation_matched_ori_graft"
                ),
                matched_ori_reference_anchor=True,
                matched_ori_anchor_mode="acutance_only",
            )

            def parse_csv(path: Path):
                return ori_reference if path.name == "ori.csv" else reference

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.parse_imatest_random_csv",
                    side_effect=parse_csv,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_intrinsic_transfer_curve",
                    return_value=np.array([2.0, 2.0, 2.0, 2.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_reference_correction_curve",
                    return_value=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_reference_correction_curve",
                    side_effect=lambda _freqs, values, *_args, **_kwargs: (
                        np.asarray(values, dtype=np.float64) + 1.0
                    ),
                ) as apply_correction_curve,
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ) as compute_metrics,
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf",
                    return_value=reference.acutance_table,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_curves",
                    return_value={"count": 1, "mae": 0.0},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf",
                    return_value=reference.reported_acutance,
                ) as acutance_from_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            self.assertEqual(apply_correction_curve.call_count, 1)
            np.testing.assert_allclose(compute_metrics.call_args.args[1], [3.0, 3.0, 3.0, 3.0])
            np.testing.assert_allclose(acutance_from_mtf.call_args.args[1], [2.0, 2.0, 2.0, 2.0])

    def test_intrinsic_scope_can_keep_downstream_matched_ori_off_readout_path(self) -> None:
        capture_key = "OV13b10_AG8_ET5500_deadleaf_12M_40"
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir)
            variant_root = dataset_root / "OV13B10_AI_NR_OV13B10_ppqpkl_0.10"
            results_dir = variant_root / "Results"
            results_dir.mkdir(parents=True)
            stem = f"{capture_key}_variantA"
            (results_dir / f"{stem}_R_Random.csv").write_text("", encoding="utf-8")
            (variant_root / f"{stem}.raw").write_bytes(b"")

            reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=[
                    AcutancePoint(print_height_cm=40.0, viewing_distance_cm=10.0, acutance=1.0)
                ],
                reported_acutance={'5.5" Phone Display Acutance': 1.0},
            )
            ori_reference = SimpleNamespace(
                lrtb=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                acutance_table=reference.acutance_table,
                reported_acutance=reference.reported_acutance,
            )
            estimate = SimpleNamespace(
                roi=RoiBounds(left=0, right=1, top=0, bottom=1),
                frequencies_cpp=np.array([0.02, 0.1, 0.25, 0.4], dtype=np.float64),
                mtf=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                mtf_for_acutance=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
            )
            profile = Profile(
                name="test",
                calibration_file="calibration.json",
                roi_source="reference",
                intrinsic_full_reference_mode="paired_ori_transfer",
                intrinsic_full_reference_scope=(
                    "readout_reconnect_quality_loss_isolation_downstream_matched_ori_only"
                ),
                matched_ori_reference_anchor=True,
                matched_ori_anchor_mode="all",
            )

            def parse_csv(path: Path):
                return ori_reference if path.name == "ori.csv" else reference

            with (
                patch("algo.benchmark_parity_psd_mtf.load_ideal_psd_calibration", return_value=None),
                patch(
                    "algo.benchmark_parity_psd_mtf.build_ori_reference_map",
                    return_value={capture_key: (dataset_root / "ori.csv", dataset_root / "ori.raw")},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.parse_imatest_random_csv",
                    side_effect=parse_csv,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.load_raw_u16",
                    side_effect=lambda path, width, height: np.zeros((height, width), dtype=np.uint16),
                ),
                patch("algo.benchmark_parity_psd_mtf.extract_analysis_plane", side_effect=lambda raw, **_: raw),
                patch("algo.benchmark_parity_psd_mtf.normalize_for_analysis", side_effect=lambda plane, **_: plane),
                patch("algo.benchmark_parity_psd_mtf.estimate_dead_leaves_mtf", return_value=estimate),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_mtf_compensation",
                    side_effect=lambda mtf, freqs, **_: (
                        np.asarray(mtf, dtype=np.float64),
                        np.asarray(freqs, dtype=np.float64),
                    ),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_intrinsic_transfer_curve",
                    return_value=np.array([2.0, 2.0, 2.0, 2.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.derive_reference_correction_curve",
                    return_value=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64),
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.apply_reference_correction_curve",
                    side_effect=lambda _freqs, values, *_args, **_kwargs: (
                        np.asarray(values, dtype=np.float64) + 1.0
                    ),
                ) as apply_correction_curve,
                patch(
                    "algo.benchmark_parity_psd_mtf.compute_mtf_metrics",
                    return_value=SimpleNamespace(mtf50=0.1, mtf30=0.1, mtf20=0.1),
                ) as compute_metrics,
                patch("algo.benchmark_parity_psd_mtf.interpolate_threshold", return_value=0.1),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_curve_from_mtf",
                    return_value=reference.acutance_table,
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_curves",
                    return_value={"count": 1, "mae": 0.0},
                ),
                patch(
                    "algo.benchmark_parity_psd_mtf.acutance_presets_from_mtf",
                    return_value=reference.reported_acutance,
                ) as acutance_from_mtf,
                patch(
                    "algo.benchmark_parity_psd_mtf.compare_acutance_presets",
                    return_value={'5.5" Phone Display Acutance': {"abs_error": 0.0}},
                ),
            ):
                profile_payload(
                    dataset_root=dataset_root,
                    profile_path=dataset_root / "profile.json",
                    profile=profile,
                    width=2,
                    height=2,
                )

            self.assertEqual(apply_correction_curve.call_count, 0)
            np.testing.assert_allclose(compute_metrics.call_args.args[1], [2.0, 2.0, 2.0, 2.0])
            np.testing.assert_allclose(acutance_from_mtf.call_args.args[1], [2.0, 2.0, 2.0, 2.0])


if __name__ == "__main__":
    unittest.main()
