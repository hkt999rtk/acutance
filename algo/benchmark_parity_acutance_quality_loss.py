from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

import numpy as np

from .dead_leaves import (
    ACUTANCE_HF_NOISE_SHARE_BAND,
    ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS,
    AcutancePreset,
    BayerMode,
    BayerPattern,
    DEFAULT_ACUTANCE_PRESETS,
    IMATEST_REFERENCE_BINS,
    MTF_SHAPE_CORRECTION_SHARE_GATE,
    RoiBounds,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_frequency_scale,
    apply_mtf_compensation,
    apply_mtf_shape_correction,
    compare_acutance_curves,
    compare_acutance_presets,
    estimate_dead_leaves_mtf,
    estimate_texture_support_scale,
    extract_analysis_plane,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
    quality_loss_presets_from_acutance,
    refine_roi_to_texture_support,
)
from .parity_benchmark_common import (
    apply_reference_correction_curve,
    build_ori_reference_map,
    capture_key_from_stem,
    clip_reference_correction_curve,
    derive_reference_acutance_correction_curve,
    derive_reference_correction_curve,
)

FOCUS_ACUTANCE_PRESETS = (
    '5.5" Phone Display Acutance',
    "Computer Monitor Acutance",
    "UHDTV Display Acutance",
    "Small Print Acutance",
    "Large Print Acutance",
)

FOCUS_QUALITY_PRESETS = (
    '5.5" Phone Display Quality Loss',
    "Computer Monitor Quality Loss",
    "UHDTV Display Quality Loss",
    "Small Print Quality Loss",
    "Large Print Quality Loss",
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
    acutance_noise_share_band_lo: float = ACUTANCE_HF_NOISE_SHARE_BAND[0]
    acutance_noise_share_band_hi: float = ACUTANCE_HF_NOISE_SHARE_BAND[1]
    acutance_noise_share_scale_coefficients: tuple[float, float, float] = (
        ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS
    )
    high_frequency_guard_start_cpp: float | None = None
    high_frequency_guard_stop_cpp: float = 0.5
    mtf_shape_correction_mode: str = "none"
    mtf_shape_correction_gain: float = 0.035
    mtf_shape_correction_share_gate_lo: float = MTF_SHAPE_CORRECTION_SHARE_GATE[0]
    mtf_shape_correction_share_gate_hi: float = MTF_SHAPE_CORRECTION_SHARE_GATE[1]
    mtf_shape_correction_mid_start_cpp: float = 0.095
    mtf_shape_correction_mid_peak_cpp: float = 0.145
    mtf_shape_correction_mid_stop_cpp: float = 0.19
    mtf_shape_correction_high_start_cpp: float = 0.36
    mtf_shape_correction_high_peak_cpp: float = 0.40
    mtf_shape_correction_high_stop_cpp: float = 0.49
    mtf_shape_correction_high_weight: float = 0.25
    quality_loss_om_ceiling: float = 0.8851
    quality_loss_coefficients: tuple[float, float, float] = (64.99250542, 9.37974246, 0.72233291)
    quality_loss_preset_overrides: dict[str, dict[str, object]] | None = None
    acutance_preset_overrides: dict[str, dict[str, float | str | None]] | None = None
    texture_support_scale: bool = False
    mtf_compensation_mode: str = "none"
    sensor_fill_factor: float = 1.0
    compensation_denominator_clip: float = 0.25
    compensation_max_gain: float = 3.0


def load_profile(path: Path) -> Profile:
    return Profile(**json.loads(path.read_text(encoding="utf-8")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate acutance and quality loss profiles.")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("profiles", nargs="+", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--include-quality-loss-records",
        action="store_true",
        help="Include per-sample Acutance and Quality Loss records in the output payload.",
    )
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


def detect_texture_roi(image: np.ndarray) -> RoiBounds:
    from .dead_leaves import detect_texture_roi as _detect_texture_roi

    return _detect_texture_roi(image)


def classify_csv(csv_path: Path, dataset_root: Path) -> str:
    relative = csv_path.relative_to(dataset_root)
    parts = relative.parts
    if "OV13B10_AI_NR_OV13B10_ori" in parts:
        return "ori"
    parent = csv_path.parent.parent.name
    match = re.search(r"_ppqpkl_([0-9.]+)$", parent)
    return match.group(1) if match else "unknown"


def mean_named_metrics(values: dict[str, list[float]], names: tuple[str, ...]) -> float:
    return float(np.mean([np.mean(values[name]) for name in names]))


def build_acutance_presets(
    overrides: dict[str, dict[str, float | str | None]] | None = None,
) -> tuple[AcutancePreset, ...]:
    presets: list[AcutancePreset] = []
    override_map = overrides or {}
    for preset in DEFAULT_ACUTANCE_PRESETS:
        override = override_map.get(preset.name, {})
        display_mtf_c50_cpd = override.get("display_mtf_c50_cpd", preset.display_mtf_c50_cpd)
        presets.append(
            AcutancePreset(
                name=preset.name,
                picture_height_cm=float(override.get("picture_height_cm", preset.picture_height_cm)),
                viewing_distance_cm=float(
                    override.get("viewing_distance_cm", preset.viewing_distance_cm)
                ),
                display_mtf_c50_cpd=(
                    None if display_mtf_c50_cpd is None else float(display_mtf_c50_cpd)
                ),
                display_mtf_model=str(override.get("display_mtf_model", preset.display_mtf_model)),
            )
        )
    return tuple(presets)


def summarize_profile(
    *,
    dataset_root: Path,
    profile_path: Path,
    profile: Profile,
    width: int,
    height: int,
    include_quality_loss_records: bool = False,
) -> dict[str, object]:
    calibration = load_ideal_psd_calibration(profile.calibration_file)
    ori_reference_map = (
        build_ori_reference_map(dataset_root) if profile.matched_ori_reference_anchor else {}
    )
    correction_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    acutance_correction_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    presets = build_acutance_presets(profile.acutance_preset_overrides)
    csv_paths = sorted(dataset_root.glob("**/Results/*_R_Random.csv"))
    curve_mae: list[float] = []
    acutance_preset_errors: dict[str, list[float]] = {}
    quality_loss_errors: dict[str, list[float]] = {}
    by_mixup_curve_mae: dict[str, list[float]] = {}
    by_mixup_quality_loss_mae: dict[str, list[float]] = {}
    quality_loss_records: list[dict[str, object]] = []

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
                            ori_compensated_mtf_for_acutance,
                            clip_lo=profile.matched_ori_correction_clip_lo,
                            clip_hi=profile.matched_ori_correction_clip_hi,
                        ),
                    )
                correction_frequencies, correction_curve = correction_cache[capture_key]
                compensated_mtf_for_acutance = apply_reference_correction_curve(
                    scaled_frequencies,
                    compensated_mtf_for_acutance,
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
        corrected_mtf_for_acutance, _ = apply_mtf_shape_correction(
            compensated_mtf_for_acutance,
            scaled_frequencies,
            mode=profile.mtf_shape_correction_mode,
            high_frequency_noise_share=estimate.acutance_high_frequency_noise_share,
            gain=profile.mtf_shape_correction_gain,
            share_gate_lo=profile.mtf_shape_correction_share_gate_lo,
            share_gate_hi=profile.mtf_shape_correction_share_gate_hi,
            mid_start_cpp=profile.mtf_shape_correction_mid_start_cpp,
            mid_peak_cpp=profile.mtf_shape_correction_mid_peak_cpp,
            mid_stop_cpp=profile.mtf_shape_correction_mid_stop_cpp,
            high_start_cpp=profile.mtf_shape_correction_high_start_cpp,
            high_peak_cpp=profile.mtf_shape_correction_high_peak_cpp,
            high_stop_cpp=profile.mtf_shape_correction_high_stop_cpp,
            high_weight=profile.mtf_shape_correction_high_weight,
        )
        curve = acutance_curve_from_mtf(
            scaled_frequencies,
            corrected_mtf_for_acutance,
            picture_height_cm=40.0,
            viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
            pixels_along_picture_height=estimate.roi.height,
        )
        acutance = acutance_presets_from_mtf(
            scaled_frequencies,
            corrected_mtf_for_acutance,
            pixels_along_picture_height=estimate.roi.height,
            presets=presets,
        )
        if profile.matched_ori_acutance_reference_anchor:
            capture_key = capture_key_from_stem(raw_path.stem)
            if capture_key in ori_reference_map:
                if capture_key not in acutance_correction_cache:
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
                    ori_compensated_mtf_for_acutance, _ = apply_mtf_compensation(
                        ori_estimate.mtf_for_acutance,
                        ori_scaled_frequencies,
                        mode=profile.mtf_compensation_mode,
                        sensor_fill_factor=profile.sensor_fill_factor,
                        denominator_clip=profile.compensation_denominator_clip,
                        max_gain=profile.compensation_max_gain,
                    )
                    ori_corrected_mtf_for_acutance, _ = apply_mtf_shape_correction(
                        ori_compensated_mtf_for_acutance,
                        ori_scaled_frequencies,
                        mode=profile.mtf_shape_correction_mode,
                        high_frequency_noise_share=ori_estimate.acutance_high_frequency_noise_share,
                        gain=profile.mtf_shape_correction_gain,
                        share_gate_lo=profile.mtf_shape_correction_share_gate_lo,
                        share_gate_hi=profile.mtf_shape_correction_share_gate_hi,
                        mid_start_cpp=profile.mtf_shape_correction_mid_start_cpp,
                        mid_peak_cpp=profile.mtf_shape_correction_mid_peak_cpp,
                        mid_stop_cpp=profile.mtf_shape_correction_mid_stop_cpp,
                        high_start_cpp=profile.mtf_shape_correction_high_start_cpp,
                        high_peak_cpp=profile.mtf_shape_correction_high_peak_cpp,
                        high_stop_cpp=profile.mtf_shape_correction_high_stop_cpp,
                        high_weight=profile.mtf_shape_correction_high_weight,
                    )
                    ori_curve = acutance_curve_from_mtf(
                        ori_scaled_frequencies,
                        ori_corrected_mtf_for_acutance,
                        picture_height_cm=40.0,
                        viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
                        pixels_along_picture_height=ori_estimate.roi.height,
                    )
                    acutance_correction_cache[capture_key] = (
                        derive_reference_acutance_correction_curve(
                            ori_reference.acutance_table,
                            ori_curve,
                            clip_lo=None,
                            clip_hi=None,
                        )
                    )
                correction_positions, correction_curve = acutance_correction_cache[capture_key]
                curve_positions = np.asarray(
                    [
                        point.viewing_distance_cm / max(point.print_height_cm, 1e-12)
                        for point in curve
                    ],
                    dtype=np.float64,
                )
                curve_correction_curve = clip_reference_correction_curve(
                    curve_positions,
                    correction_curve,
                    clip_lo=(
                        profile.matched_ori_acutance_curve_correction_clip_lo
                        if profile.matched_ori_acutance_curve_correction_clip_lo is not None
                        else profile.matched_ori_acutance_correction_clip_lo
                    ),
                    clip_hi=(
                        profile.matched_ori_acutance_curve_correction_clip_hi
                        if profile.matched_ori_acutance_curve_correction_clip_hi is not None
                        else profile.matched_ori_acutance_correction_clip_hi
                    ),
                    clip_lo_positions=(
                        profile.matched_ori_acutance_curve_correction_clip_lo_relative_scales
                    ),
                    clip_lo_values=profile.matched_ori_acutance_curve_correction_clip_lo_values,
                    clip_hi_positions=profile.matched_ori_acutance_curve_correction_clip_hi_relative_scales,
                    clip_hi_values=profile.matched_ori_acutance_curve_correction_clip_hi_values,
                )
                corrected_curve_values = apply_reference_correction_curve(
                    curve_positions,
                    np.asarray([point.acutance for point in curve], dtype=np.float64),
                    correction_positions,
                    curve_correction_curve,
                    strength=profile.matched_ori_acutance_correction_strength,
                    blend_start_cpp=profile.matched_ori_acutance_blend_start_relative_scale,
                    blend_stop_cpp=profile.matched_ori_acutance_blend_stop_relative_scale,
                    strength_curve_frequencies=profile.matched_ori_acutance_strength_curve_relative_scales,
                    strength_curve_values=profile.matched_ori_acutance_strength_curve_values,
                    correction_delta_power=(
                        profile.matched_ori_acutance_curve_correction_delta_power
                        if profile.matched_ori_acutance_curve_correction_delta_power is not None
                        else profile.matched_ori_acutance_correction_delta_power
                    ),
                )
                curve = [
                    point.__class__(
                        print_height_cm=point.print_height_cm,
                        viewing_distance_cm=point.viewing_distance_cm,
                        acutance=float(value),
                    )
                    for point, value in zip(curve, corrected_curve_values)
                ]
                preset_positions = np.asarray(
                    [preset.viewing_distance_cm / preset.picture_height_cm for preset in presets],
                    dtype=np.float64,
                )
                corrected_preset_values = apply_reference_correction_curve(
                    preset_positions,
                    np.asarray([acutance[preset.name] for preset in presets], dtype=np.float64),
                    correction_positions,
                    clip_reference_correction_curve(
                        correction_positions,
                        correction_curve,
                        clip_lo=(
                            profile.matched_ori_acutance_preset_correction_clip_lo
                            if profile.matched_ori_acutance_preset_correction_clip_lo is not None
                            else profile.matched_ori_acutance_correction_clip_lo
                        ),
                        clip_hi=(
                            profile.matched_ori_acutance_preset_correction_clip_hi
                            if profile.matched_ori_acutance_preset_correction_clip_hi is not None
                            else profile.matched_ori_acutance_correction_clip_hi
                        ),
                        clip_lo_positions=(
                            profile.matched_ori_acutance_preset_correction_clip_lo_relative_scales
                        ),
                        clip_lo_values=(
                            profile.matched_ori_acutance_preset_correction_clip_lo_values
                        ),
                        clip_hi_positions=(
                            profile.matched_ori_acutance_preset_correction_clip_hi_relative_scales
                        ),
                        clip_hi_values=profile.matched_ori_acutance_preset_correction_clip_hi_values,
                    ),
                    strength=profile.matched_ori_acutance_correction_strength,
                    blend_start_cpp=profile.matched_ori_acutance_blend_start_relative_scale,
                    blend_stop_cpp=profile.matched_ori_acutance_blend_stop_relative_scale,
                    strength_curve_frequencies=(
                        profile.matched_ori_acutance_preset_strength_curve_relative_scales
                        or profile.matched_ori_acutance_strength_curve_relative_scales
                    ),
                    strength_curve_values=(
                        profile.matched_ori_acutance_preset_strength_curve_values
                        or profile.matched_ori_acutance_strength_curve_values
                    ),
                    correction_delta_power=(
                        profile.matched_ori_acutance_preset_correction_delta_power
                        if profile.matched_ori_acutance_preset_correction_delta_power is not None
                        else profile.matched_ori_acutance_correction_delta_power
                    ),
                    correction_delta_power_positions=(
                        profile.matched_ori_acutance_preset_correction_delta_power_relative_scales
                    ),
                    correction_delta_power_values=(
                        profile.matched_ori_acutance_preset_correction_delta_power_values
                    ),
                )
                acutance = {
                    preset.name: float(value)
                    for preset, value in zip(presets, corrected_preset_values)
                }
        curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
        if curve_cmp.get("count", 0):
            curve_mae.append(float(curve_cmp["mae"]))
            by_mixup_curve_mae.setdefault(classify_csv(csv_path, dataset_root), []).append(
                float(curve_cmp["mae"])
            )
        acutance_cmp = compare_acutance_presets(acutance, reference.reported_acutance)
        for name, values in acutance_cmp.items():
            acutance_preset_errors.setdefault(name, []).append(float(values["abs_error"]))

        quality_loss = quality_loss_presets_from_acutance(
            acutance,
            om_ceiling=profile.quality_loss_om_ceiling,
            coefficients=tuple(profile.quality_loss_coefficients),
            preset_overrides=profile.quality_loss_preset_overrides,
        )
        quality_abs_errors = {}
        for name, value in quality_loss.items():
            abs_error = abs(float(value) - float(reference.reported_quality_loss[name]))
            quality_loss_errors.setdefault(name, []).append(abs_error)
            quality_abs_errors[name] = abs_error
            if include_quality_loss_records:
                quality_loss_records.append(
                    {
                        "capture_key": capture_key_from_stem(raw_path.stem),
                        "csv_path": str(csv_path),
                        "mixup": classify_csv(csv_path, dataset_root),
                        "preset_name": name,
                        "reported_quality_loss": float(reference.reported_quality_loss[name]),
                        "predicted_quality_loss": float(value),
                        "predicted_acutance": float(
                            acutance[name.replace("Quality Loss", "Acutance")]
                        ),
                    }
                )
        by_mixup_quality_loss_mae.setdefault(classify_csv(csv_path, dataset_root), []).append(
            float(np.mean(list(quality_abs_errors.values())))
        )

    result = {
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
            "quality_loss_om_ceiling": profile.quality_loss_om_ceiling,
            "quality_loss_coefficients": profile.quality_loss_coefficients,
            "quality_loss_preset_overrides": profile.quality_loss_preset_overrides,
            "frequency_scale": profile.frequency_scale,
            "texture_support_scale": profile.texture_support_scale,
            "calibration_file": profile.calibration_file,
            "acutance_noise_scale_mode": profile.acutance_noise_scale_mode,
            "high_frequency_guard_start_cpp": profile.high_frequency_guard_start_cpp,
            "mtf_shape_correction_mode": profile.mtf_shape_correction_mode,
            "mtf_compensation_mode": profile.mtf_compensation_mode,
            "sensor_fill_factor": profile.sensor_fill_factor,
            "acutance_preset_overrides": profile.acutance_preset_overrides,
        },
        "overall": {
            "curve_mae_mean": float(np.mean(curve_mae)),
            "acutance_preset_mae": {
                key: float(np.mean(values))
                for key, values in sorted(acutance_preset_errors.items())
            },
            "acutance_focus_preset_mae_mean": mean_named_metrics(
                acutance_preset_errors, FOCUS_ACUTANCE_PRESETS
            ),
            "quality_loss_preset_mae": {
                key: float(np.mean(values))
                for key, values in sorted(quality_loss_errors.items())
            },
            "overall_quality_loss_mae_mean": float(
                np.mean([np.mean(values) for values in quality_loss_errors.values()])
            ),
            "quality_loss_focus_preset_mae_mean": mean_named_metrics(
                quality_loss_errors, FOCUS_QUALITY_PRESETS
            ),
        },
        "by_mixup_curve_mae_mean": {
            key: float(np.mean(values))
            for key, values in sorted(by_mixup_curve_mae.items())
        },
        "by_mixup_quality_loss_mae_mean": {
            key: float(np.mean(values))
            for key, values in sorted(by_mixup_quality_loss_mae.items())
        },
    }
    if include_quality_loss_records:
        result["quality_loss_records"] = quality_loss_records
    return result


def main() -> int:
    args = build_parser().parse_args()
    profiles = [load_profile(path) for path in args.profiles]
    results = [
        summarize_profile(
            dataset_root=args.dataset_root,
            profile_path=path,
            profile=profile,
            width=args.width,
            height=args.height,
            include_quality_loss_records=args.include_quality_loss_records,
        )
        for path, profile in zip(args.profiles, profiles)
    ]
    baseline = results[0]["overall"]
    for result in results[1:]:
        overall = result["overall"]
        result["delta_vs_first_profile"] = {
            "curve_mae_mean": float(overall["curve_mae_mean"] - baseline["curve_mae_mean"]),
            "overall_quality_loss_mae_mean": float(
                overall["overall_quality_loss_mae_mean"] - baseline["overall_quality_loss_mae_mean"]
            ),
            "acutance_focus_preset_mae_mean": float(
                overall["acutance_focus_preset_mae_mean"] - baseline["acutance_focus_preset_mae_mean"]
            ),
            "quality_loss_focus_preset_mae_mean": float(
                overall["quality_loss_focus_preset_mae_mean"]
                - baseline["quality_loss_focus_preset_mae_mean"]
            ),
        }
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
