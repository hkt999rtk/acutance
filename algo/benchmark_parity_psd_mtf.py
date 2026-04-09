from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

import numpy as np

from .dead_leaves import (
    BayerMode,
    BayerPattern,
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_frequency_scale,
    apply_mtf_compensation,
    compare_acutance_curves,
    compare_acutance_presets,
    compute_mtf_metrics,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    estimate_texture_support_scale,
    extract_analysis_plane,
    interpolate_threshold,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
    refine_roi_to_texture_support,
)
from .parity_benchmark_common import (
    apply_reference_correction_curve,
    build_ori_reference_map,
    capture_key_from_stem,
    derive_reference_correction_curve,
)

BANDS = (
    ("low", 0.01, 0.08),
    ("mid", 0.08, 0.2),
    ("high", 0.2, 0.35),
    ("top", 0.35, 0.5),
)


@dataclass(frozen=True)
class Profile:
    name: str
    calibration_file: str
    gamma: float = 1.0
    linearization_mode: str = "power"
    linearization_toe: float = 0.0
    bayer_pattern: str = BayerPattern.RGGB.value
    bayer_mode: str = BayerMode.DEMOSAIC_RED.value
    roi_source: str = "fixed"
    roi_width: int = 1655
    roi_height: int = 1673
    roi_refine_percentile: float = 45.0
    roi_refine_sigma: float = 5.0
    roi_refine_min_border_margin: int = 8
    roi_refine_search_radius: int = 12
    roi_refine_step: int = 2
    roi_refine_area_tolerance: float = 0.98
    matched_ori_reference_anchor: bool = False
    matched_ori_anchor_mode: str = "all"
    matched_ori_correction_clip_lo: float = 0.5
    matched_ori_correction_clip_hi: float = 2.0
    matched_ori_correction_strength: float = 1.0
    matched_ori_blend_start_cpp: float = 0.0
    matched_ori_blend_stop_cpp: float = 0.0
    matched_ori_strength_low: float | None = None
    matched_ori_strength_high: float | None = None
    matched_ori_strength_ramp_start_cpp: float = 0.0
    matched_ori_strength_ramp_stop_cpp: float = 0.0
    matched_ori_strength_curve_frequencies: tuple[float, ...] | None = None
    matched_ori_strength_curve_values: tuple[float, ...] | None = None
    matched_ori_acutance_reference_anchor: bool = False
    matched_ori_acutance_correction_clip_lo: float = 0.9
    matched_ori_acutance_correction_clip_hi: float = 1.1
    matched_ori_acutance_curve_correction_clip_lo: float | None = None
    matched_ori_acutance_curve_correction_clip_hi: float | None = None
    matched_ori_acutance_curve_correction_clip_lo_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_curve_correction_clip_lo_values: tuple[float, ...] | None = None
    matched_ori_acutance_curve_correction_clip_hi_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_curve_correction_clip_hi_values: tuple[float, ...] | None = None
    matched_ori_acutance_preset_correction_clip_lo: float | None = None
    matched_ori_acutance_preset_correction_clip_hi: float | None = None
    matched_ori_acutance_preset_correction_clip_lo_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_preset_correction_clip_lo_values: tuple[float, ...] | None = None
    matched_ori_acutance_preset_correction_clip_hi_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_preset_correction_clip_hi_values: tuple[float, ...] | None = None
    matched_ori_acutance_correction_strength: float = 1.0
    matched_ori_acutance_blend_start_relative_scale: float = 0.0
    matched_ori_acutance_blend_stop_relative_scale: float = 0.0
    matched_ori_acutance_strength_curve_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_strength_curve_values: tuple[float, ...] | None = None
    matched_ori_acutance_correction_delta_power: float = 1.0
    matched_ori_acutance_curve_correction_delta_power: float | None = None
    matched_ori_acutance_preset_correction_delta_power: float | None = None
    matched_ori_acutance_preset_correction_delta_power_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_preset_correction_delta_power_values: tuple[float, ...] | None = None
    matched_ori_acutance_preset_strength_curve_relative_scales: tuple[float, ...] | None = None
    matched_ori_acutance_preset_strength_curve_values: tuple[float, ...] | None = None
    frequency_scale: float = 1.0
    normalization_band_lo: float = 0.01
    normalization_band_hi: float = 0.03
    normalization_mode: str = "max"
    acutance_band_lo: float = 0.017
    acutance_band_hi: float = 0.035
    acutance_band_mode: str = "mean"
    signal_psd_correction_gain: float = 0.0
    signal_psd_correction_start_cpp: float = 0.08
    signal_psd_correction_peak_cpp: float = 0.15
    signal_psd_correction_stop_cpp: float = 0.22
    noise_psd_model: str = "empirical"
    noise_psd_log_polynomial_degree: int = 2
    noise_psd_scale: float = 1.0
    noise_psd_scale_for_acutance: float | None = None
    acutance_noise_scale_mode: str = "fixed"
    acutance_noise_share_band_lo: float = 0.36
    acutance_noise_share_band_hi: float = 0.5
    acutance_noise_share_scale_coefficients: tuple[float, float, float] = (
        521.08180962,
        -26.62905791,
        1.59615575,
    )
    high_frequency_guard_start_cpp: float | None = None
    high_frequency_guard_stop_cpp: float = 0.5
    texture_support_scale: bool = False
    mtf_compensation_mode: str = "none"
    sensor_fill_factor: float = 1.0
    compensation_denominator_clip: float = 0.25
    compensation_max_gain: float = 3.0


def load_profile(path: Path) -> Profile:
    return Profile(**json.loads(path.read_text(encoding="utf-8")))


def classify_csv(csv_path: Path, dataset_root: Path) -> str:
    relative = csv_path.relative_to(dataset_root)
    parts = relative.parts
    if "OV13B10_AI_NR_OV13B10_ori" in parts:
        return "ori"
    parent = csv_path.parent.parent.name
    match = re.search(r"_ppqpkl_([0-9.]+)$", parent)
    return match.group(1) if match else "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark parity PSD/MTF profiles.")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("profiles", nargs="+", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--output", type=Path)
    return parser


def choose_roi(profile: Profile, reference, image: np.ndarray) -> RoiBounds:
    if profile.roi_source == "reference":
        return reference.lrtb.clamp(image.shape[1], image.shape[0])
    if profile.roi_source == "reference_refined":
        seed = reference.lrtb.clamp(image.shape[1], image.shape[0])
        return refine_roi_to_texture_support(
            image,
            seed_roi=seed,
            target_width=profile.roi_width,
            target_height=profile.roi_height,
            percentile=profile.roi_refine_percentile,
            sigma=profile.roi_refine_sigma,
            min_border_margin=profile.roi_refine_min_border_margin,
            search_radius=profile.roi_refine_search_radius,
            step=profile.roi_refine_step,
            area_tolerance=profile.roi_refine_area_tolerance,
        )
    detected = detect_texture_roi(image)
    seed = RoiBounds.centered(
        center_x=(detected.left + detected.right) // 2,
        center_y=(detected.top + detected.bottom) // 2,
        width=profile.roi_width,
        height=profile.roi_height,
        image_width=image.shape[1],
        image_height=image.shape[0],
    )
    if profile.roi_source == "fixed_refined":
        return refine_roi_to_texture_support(
            image,
            seed_roi=seed,
            target_width=profile.roi_width,
            target_height=profile.roi_height,
            percentile=profile.roi_refine_percentile,
            sigma=profile.roi_refine_sigma,
            min_border_margin=profile.roi_refine_min_border_margin,
            search_radius=profile.roi_refine_search_radius,
            step=profile.roi_refine_step,
            area_tolerance=profile.roi_refine_area_tolerance,
        )
    return seed


def resample_curve(
    source_frequencies: np.ndarray,
    source_values: np.ndarray,
    reference_frequencies: np.ndarray,
) -> np.ndarray:
    source_f = np.asarray(source_frequencies, dtype=np.float64)
    source_v = np.asarray(source_values, dtype=np.float64)
    reference_f = np.asarray(reference_frequencies, dtype=np.float64)
    return np.interp(
        reference_f,
        source_f,
        source_v,
        left=float(source_v[0]),
        right=float(source_v[-1]),
    )


def mean_abs_signed_rel(summary: dict[str, dict[str, float]]) -> float:
    return float(np.mean([abs(summary[name]["signed_rel_mean"]) for name, _, _ in BANDS]))


def band_error_summary(
    frequencies: np.ndarray,
    estimate: np.ndarray,
    reference: np.ndarray,
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for label, lo, hi in BANDS:
        band = (frequencies >= lo) & (frequencies < hi)
        if not np.any(band):
            continue
        est = np.asarray(estimate[band], dtype=np.float64)
        ref = np.asarray(reference[band], dtype=np.float64)
        abs_err = np.abs(est - ref)
        rel_err = abs_err / np.maximum(np.abs(ref), 1e-12)
        signed_rel = (est - ref) / np.maximum(np.abs(ref), 1e-12)
        summary[label] = {
            "mae_mean": float(np.mean(abs_err)),
            "mre_mean": float(np.mean(rel_err)),
            "signed_rel_mean": float(np.mean(signed_rel)),
        }
    return summary


def profile_payload(
    *,
    dataset_root: Path,
    profile_path: Path,
    profile: Profile,
    width: int,
    height: int,
) -> dict[str, object]:
    calibration = load_ideal_psd_calibration(profile.calibration_file)
    ori_reference_map = (
        build_ori_reference_map(dataset_root) if profile.matched_ori_reference_anchor else {}
    )
    correction_cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    csv_paths = sorted(dataset_root.glob("**/Results/*_R_Random.csv"))
    curve_mae: list[float] = []
    preset_errors: dict[str, list[float]] = {}
    mtf50_errors: list[float] = []
    mtf30_errors: list[float] = []
    mtf20_errors: list[float] = []
    band_rows: list[dict[str, dict[str, float]]] = []
    by_mixup: dict[str, list[float]] = {}

    for csv_path in csv_paths:
        raw_path = csv_path.parent.parent / csv_path.name.replace("_R_Random.csv", ".raw")
        if not raw_path.exists():
            continue

        reference = parse_imatest_random_csv(csv_path)
        raw = load_raw_u16(raw_path, width, height)
        plane = extract_analysis_plane(
            raw,
            bayer_pattern=BayerPattern(profile.bayer_pattern),
            mode=BayerMode(profile.bayer_mode),
        )
        image = normalize_for_analysis(
            plane,
            gamma=profile.gamma,
            mode=profile.linearization_mode,
            toe=profile.linearization_toe,
        )
        roi = choose_roi(profile, reference, image)
        estimate = estimate_dead_leaves_mtf(
            image,
            num_bins=len(IMATEST_REFERENCE_BINS),
            ideal_psd_mode="calibrated_log",
            ideal_psd_calibration=calibration,
            bin_centers=IMATEST_REFERENCE_BINS,
            roi_override=roi,
            normalization_band=(profile.normalization_band_lo, profile.normalization_band_hi),
            normalization_mode=profile.normalization_mode,
            acutance_reference_band=(profile.acutance_band_lo, profile.acutance_band_hi),
            acutance_reference_mode=profile.acutance_band_mode,
            signal_psd_correction_gain=profile.signal_psd_correction_gain,
            signal_psd_correction_start_cpp=profile.signal_psd_correction_start_cpp,
            signal_psd_correction_peak_cpp=profile.signal_psd_correction_peak_cpp,
            signal_psd_correction_stop_cpp=profile.signal_psd_correction_stop_cpp,
            noise_psd_model=profile.noise_psd_model,
            noise_psd_log_polynomial_degree=profile.noise_psd_log_polynomial_degree,
            noise_psd_scale=profile.noise_psd_scale,
            noise_psd_scale_for_acutance=profile.noise_psd_scale_for_acutance,
            acutance_noise_scale_model=profile.acutance_noise_scale_mode,
            acutance_noise_share_band=(
                profile.acutance_noise_share_band_lo,
                profile.acutance_noise_share_band_hi,
            ),
            acutance_noise_share_scale_coefficients=tuple(
                profile.acutance_noise_share_scale_coefficients
            ),
            high_frequency_guard_start_cpp=profile.high_frequency_guard_start_cpp,
            high_frequency_guard_stop_cpp=profile.high_frequency_guard_stop_cpp,
        )
        effective_frequency_scale = profile.frequency_scale
        if profile.texture_support_scale:
            crop = image[
                estimate.roi.top : estimate.roi.bottom + 1,
                estimate.roi.left : estimate.roi.right + 1,
            ]
            effective_frequency_scale *= estimate_texture_support_scale(
                crop,
                percentile=45.0,
            ).frequency_scale
        scaled_frequencies = apply_frequency_scale(
            estimate.frequencies_cpp,
            scale=effective_frequency_scale,
        )
        compensated_mtf, _ = apply_mtf_compensation(
            estimate.mtf,
            scaled_frequencies,
            mode=profile.mtf_compensation_mode,
            sensor_fill_factor=profile.sensor_fill_factor,
            denominator_clip=profile.compensation_denominator_clip,
            max_gain=profile.compensation_max_gain,
        )
        compensated_mtf_for_acutance, _ = apply_mtf_compensation(
            estimate.mtf_for_acutance,
            scaled_frequencies,
            mode=profile.mtf_compensation_mode,
            sensor_fill_factor=profile.sensor_fill_factor,
            denominator_clip=profile.compensation_denominator_clip,
            max_gain=profile.compensation_max_gain,
        )
        if profile.matched_ori_reference_anchor:
            capture_key = capture_key_from_stem(raw_path.stem)
            if capture_key in ori_reference_map:
                if capture_key not in correction_cache:
                    ori_csv_path, ori_raw_path = ori_reference_map[capture_key]
                    ori_reference = parse_imatest_random_csv(ori_csv_path)
                    ori_raw = load_raw_u16(ori_raw_path, width, height)
                    ori_plane = extract_analysis_plane(
                        ori_raw,
                        bayer_pattern=BayerPattern(profile.bayer_pattern),
                        mode=BayerMode(profile.bayer_mode),
                    )
                    ori_image = normalize_for_analysis(
                        ori_plane,
                        gamma=profile.gamma,
                        mode=profile.linearization_mode,
                        toe=profile.linearization_toe,
                    )
                    ori_roi = choose_roi(profile, ori_reference, ori_image)
                    ori_estimate = estimate_dead_leaves_mtf(
                        ori_image,
                        num_bins=len(IMATEST_REFERENCE_BINS),
                        ideal_psd_mode="calibrated_log",
                        ideal_psd_calibration=calibration,
                        bin_centers=IMATEST_REFERENCE_BINS,
                        roi_override=ori_roi,
                        normalization_band=(profile.normalization_band_lo, profile.normalization_band_hi),
                        normalization_mode=profile.normalization_mode,
                        acutance_reference_band=(profile.acutance_band_lo, profile.acutance_band_hi),
                        acutance_reference_mode=profile.acutance_band_mode,
                        signal_psd_correction_gain=profile.signal_psd_correction_gain,
                        signal_psd_correction_start_cpp=profile.signal_psd_correction_start_cpp,
                        signal_psd_correction_peak_cpp=profile.signal_psd_correction_peak_cpp,
                        signal_psd_correction_stop_cpp=profile.signal_psd_correction_stop_cpp,
                        noise_psd_model=profile.noise_psd_model,
                        noise_psd_log_polynomial_degree=profile.noise_psd_log_polynomial_degree,
                        noise_psd_scale=profile.noise_psd_scale,
                        noise_psd_scale_for_acutance=profile.noise_psd_scale_for_acutance,
                        acutance_noise_scale_model=profile.acutance_noise_scale_mode,
                        acutance_noise_share_band=(
                            profile.acutance_noise_share_band_lo,
                            profile.acutance_noise_share_band_hi,
                        ),
                        acutance_noise_share_scale_coefficients=tuple(
                            profile.acutance_noise_share_scale_coefficients
                        ),
                        high_frequency_guard_start_cpp=profile.high_frequency_guard_start_cpp,
                        high_frequency_guard_stop_cpp=profile.high_frequency_guard_stop_cpp,
                    )
                    ori_frequency_scale = profile.frequency_scale
                    if profile.texture_support_scale:
                        ori_crop = ori_image[
                            ori_estimate.roi.top : ori_estimate.roi.bottom + 1,
                            ori_estimate.roi.left : ori_estimate.roi.right + 1,
                        ]
                        ori_frequency_scale *= estimate_texture_support_scale(
                            ori_crop,
                            percentile=45.0,
                        ).frequency_scale
                    ori_scaled_frequencies = apply_frequency_scale(
                        ori_estimate.frequencies_cpp,
                        scale=ori_frequency_scale,
                    )
                    ori_compensated_mtf, _ = apply_mtf_compensation(
                        ori_estimate.mtf,
                        ori_scaled_frequencies,
                        mode=profile.mtf_compensation_mode,
                        sensor_fill_factor=profile.sensor_fill_factor,
                        denominator_clip=profile.compensation_denominator_clip,
                        max_gain=profile.compensation_max_gain,
                    )
                    ori_compensated_mtf_for_acutance, _ = apply_mtf_compensation(
                        ori_estimate.mtf_for_acutance,
                        ori_scaled_frequencies,
                        mode=profile.mtf_compensation_mode,
                        sensor_fill_factor=profile.sensor_fill_factor,
                        denominator_clip=profile.compensation_denominator_clip,
                        max_gain=profile.compensation_max_gain,
                    )
                    correction_cache[capture_key] = (
                        ori_reference.frequencies_cpp.copy(),
                        derive_reference_correction_curve(
                            ori_reference.frequencies_cpp,
                            ori_reference.mtf,
                            ori_scaled_frequencies,
                            ori_compensated_mtf,
                            clip_lo=profile.matched_ori_correction_clip_lo,
                            clip_hi=profile.matched_ori_correction_clip_hi,
                        ),
                        derive_reference_correction_curve(
                            ori_reference.frequencies_cpp,
                            ori_reference.mtf,
                            ori_scaled_frequencies,
                            ori_compensated_mtf_for_acutance,
                            clip_lo=profile.matched_ori_correction_clip_lo,
                            clip_hi=profile.matched_ori_correction_clip_hi,
                        ),
                    )
                correction_frequencies, correction_curve, acutance_correction_curve = correction_cache[
                    capture_key
                ]
                if profile.matched_ori_anchor_mode != "acutance_only":
                    compensated_mtf = apply_reference_correction_curve(
                        scaled_frequencies,
                        compensated_mtf,
                        correction_frequencies,
                        correction_curve,
                    strength=profile.matched_ori_correction_strength,
                    blend_start_cpp=profile.matched_ori_blend_start_cpp,
                    blend_stop_cpp=profile.matched_ori_blend_stop_cpp,
                    strength_low=profile.matched_ori_strength_low,
                    strength_high=profile.matched_ori_strength_high,
                    strength_ramp_start_cpp=profile.matched_ori_strength_ramp_start_cpp,
                    strength_ramp_stop_cpp=profile.matched_ori_strength_ramp_stop_cpp,
                    strength_curve_frequencies=profile.matched_ori_strength_curve_frequencies,
                    strength_curve_values=profile.matched_ori_strength_curve_values,
                )
                compensated_mtf_for_acutance = apply_reference_correction_curve(
                    scaled_frequencies,
                    compensated_mtf_for_acutance,
                    correction_frequencies,
                    acutance_correction_curve,
                    strength=profile.matched_ori_correction_strength,
                    blend_start_cpp=profile.matched_ori_blend_start_cpp,
                    blend_stop_cpp=profile.matched_ori_blend_stop_cpp,
                    strength_low=profile.matched_ori_strength_low,
                    strength_high=profile.matched_ori_strength_high,
                    strength_ramp_start_cpp=profile.matched_ori_strength_ramp_start_cpp,
                    strength_ramp_stop_cpp=profile.matched_ori_strength_ramp_stop_cpp,
                    strength_curve_frequencies=profile.matched_ori_strength_curve_frequencies,
                    strength_curve_values=profile.matched_ori_strength_curve_values,
                )
        metrics = compute_mtf_metrics(scaled_frequencies, compensated_mtf)
        mtf50_errors.append(
            abs(metrics.mtf50 - interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.5))
        )
        mtf30_errors.append(
            abs(metrics.mtf30 - interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.3))
        )
        mtf20_errors.append(
            abs(metrics.mtf20 - interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.2))
        )

        curve = acutance_curve_from_mtf(
            scaled_frequencies,
            compensated_mtf_for_acutance,
            picture_height_cm=40.0,
            viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
            pixels_along_picture_height=estimate.roi.height,
        )
        curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
        if curve_cmp.get("count", 0):
            curve_mae.append(float(curve_cmp["mae"]))
            key = classify_csv(csv_path, dataset_root)
            by_mixup.setdefault(key, []).append(float(curve_cmp["mae"]))

        presets = acutance_presets_from_mtf(
            scaled_frequencies,
            compensated_mtf_for_acutance,
            pixels_along_picture_height=estimate.roi.height,
        )
        preset_cmp = compare_acutance_presets(presets, reference.reported_acutance)
        for key, values in preset_cmp.items():
            preset_errors.setdefault(key, []).append(float(values["abs_error"]))

        estimate_on_reference = resample_curve(
            scaled_frequencies,
            compensated_mtf,
            reference.frequencies_cpp,
        )
        band_rows.append(
            band_error_summary(reference.frequencies_cpp, estimate_on_reference, reference.mtf)
        )

    mtf_summary = {
        label: {
            "mae_mean": float(np.mean([row[label]["mae_mean"] for row in band_rows])),
            "mre_mean": float(np.mean([row[label]["mre_mean"] for row in band_rows])),
            "signed_rel_mean": float(np.mean([row[label]["signed_rel_mean"] for row in band_rows])),
        }
        for label, _, _ in BANDS
    }
    return {
        "profile_path": str(profile_path),
        "analysis_pipeline": {
            "gamma": profile.gamma,
            "linearization_mode": profile.linearization_mode,
            "linearization_toe": profile.linearization_toe,
            "bayer_pattern": profile.bayer_pattern,
            "bayer_mode": profile.bayer_mode,
            "roi_source": profile.roi_source,
            "matched_ori_reference_anchor": profile.matched_ori_reference_anchor,
            "matched_ori_anchor_mode": profile.matched_ori_anchor_mode,
            "matched_ori_correction_clip_lo": profile.matched_ori_correction_clip_lo,
            "matched_ori_correction_clip_hi": profile.matched_ori_correction_clip_hi,
            "matched_ori_correction_strength": profile.matched_ori_correction_strength,
            "matched_ori_blend_start_cpp": profile.matched_ori_blend_start_cpp,
            "matched_ori_blend_stop_cpp": profile.matched_ori_blend_stop_cpp,
            "matched_ori_strength_low": profile.matched_ori_strength_low,
            "matched_ori_strength_high": profile.matched_ori_strength_high,
            "matched_ori_strength_ramp_start_cpp": profile.matched_ori_strength_ramp_start_cpp,
            "matched_ori_strength_ramp_stop_cpp": profile.matched_ori_strength_ramp_stop_cpp,
            "matched_ori_strength_curve_frequencies": profile.matched_ori_strength_curve_frequencies,
            "matched_ori_strength_curve_values": profile.matched_ori_strength_curve_values,
            "matched_ori_acutance_reference_anchor": profile.matched_ori_acutance_reference_anchor,
            "matched_ori_acutance_correction_clip_lo": profile.matched_ori_acutance_correction_clip_lo,
            "matched_ori_acutance_correction_clip_hi": profile.matched_ori_acutance_correction_clip_hi,
            "matched_ori_acutance_curve_correction_clip_lo": profile.matched_ori_acutance_curve_correction_clip_lo,
            "matched_ori_acutance_curve_correction_clip_hi": profile.matched_ori_acutance_curve_correction_clip_hi,
            "matched_ori_acutance_curve_correction_clip_lo_relative_scales": profile.matched_ori_acutance_curve_correction_clip_lo_relative_scales,
            "matched_ori_acutance_curve_correction_clip_lo_values": profile.matched_ori_acutance_curve_correction_clip_lo_values,
            "matched_ori_acutance_curve_correction_clip_hi_relative_scales": profile.matched_ori_acutance_curve_correction_clip_hi_relative_scales,
            "matched_ori_acutance_curve_correction_clip_hi_values": profile.matched_ori_acutance_curve_correction_clip_hi_values,
            "matched_ori_acutance_preset_correction_clip_lo": profile.matched_ori_acutance_preset_correction_clip_lo,
            "matched_ori_acutance_preset_correction_clip_hi": profile.matched_ori_acutance_preset_correction_clip_hi,
            "matched_ori_acutance_preset_correction_clip_lo_relative_scales": profile.matched_ori_acutance_preset_correction_clip_lo_relative_scales,
            "matched_ori_acutance_preset_correction_clip_lo_values": profile.matched_ori_acutance_preset_correction_clip_lo_values,
            "matched_ori_acutance_preset_correction_clip_hi_relative_scales": profile.matched_ori_acutance_preset_correction_clip_hi_relative_scales,
            "matched_ori_acutance_preset_correction_clip_hi_values": profile.matched_ori_acutance_preset_correction_clip_hi_values,
            "matched_ori_acutance_correction_strength": profile.matched_ori_acutance_correction_strength,
            "matched_ori_acutance_blend_start_relative_scale": profile.matched_ori_acutance_blend_start_relative_scale,
            "matched_ori_acutance_blend_stop_relative_scale": profile.matched_ori_acutance_blend_stop_relative_scale,
            "matched_ori_acutance_strength_curve_relative_scales": profile.matched_ori_acutance_strength_curve_relative_scales,
            "matched_ori_acutance_strength_curve_values": profile.matched_ori_acutance_strength_curve_values,
            "matched_ori_acutance_correction_delta_power": profile.matched_ori_acutance_correction_delta_power,
            "matched_ori_acutance_curve_correction_delta_power": profile.matched_ori_acutance_curve_correction_delta_power,
            "matched_ori_acutance_preset_correction_delta_power": profile.matched_ori_acutance_preset_correction_delta_power,
            "matched_ori_acutance_preset_correction_delta_power_relative_scales": profile.matched_ori_acutance_preset_correction_delta_power_relative_scales,
            "matched_ori_acutance_preset_correction_delta_power_values": profile.matched_ori_acutance_preset_correction_delta_power_values,
            "matched_ori_acutance_preset_strength_curve_relative_scales": profile.matched_ori_acutance_preset_strength_curve_relative_scales,
            "matched_ori_acutance_preset_strength_curve_values": profile.matched_ori_acutance_preset_strength_curve_values,
            "frequency_scale": profile.frequency_scale,
            "texture_support_scale": profile.texture_support_scale,
            "signal_psd_correction_gain": profile.signal_psd_correction_gain,
            "calibration_file": profile.calibration_file,
            "mtf_compensation_mode": profile.mtf_compensation_mode,
            "sensor_fill_factor": profile.sensor_fill_factor,
        },
        "overall": {
            "curve_mae_mean": float(np.mean(curve_mae)),
            "preset_mae": {
                key: float(np.mean(values))
                for key, values in sorted(preset_errors.items())
            },
            "mtf_threshold_mae": {
                "mtf50": float(np.mean(mtf50_errors)),
                "mtf30": float(np.mean(mtf30_errors)),
                "mtf20": float(np.mean(mtf20_errors)),
            },
            "mtf_bands": mtf_summary,
            "mtf_abs_signed_rel_mean": mean_abs_signed_rel(mtf_summary),
        },
        "by_mixup_curve_mae_mean": {
            key: float(np.mean(values))
            for key, values in sorted(by_mixup.items())
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    results = []
    for profile_path in args.profiles:
        profile = load_profile(profile_path)
        results.append(
            profile_payload(
                dataset_root=args.dataset_root,
                profile_path=profile_path,
                profile=profile,
                width=args.width,
                height=args.height,
            )
        )
    payload = {
        "dataset_root": str(args.dataset_root),
        "profiles": results,
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
