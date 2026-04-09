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
) -> dict[str, object]:
    calibration = load_ideal_psd_calibration(profile.calibration_file)
    presets = build_acutance_presets(profile.acutance_preset_overrides)
    csv_paths = sorted(dataset_root.glob("**/Results/*_R_Random.csv"))
    curve_mae: list[float] = []
    acutance_preset_errors: dict[str, list[float]] = {}
    quality_loss_errors: dict[str, list[float]] = {}
    by_mixup_curve_mae: dict[str, list[float]] = {}
    by_mixup_quality_loss_mae: dict[str, list[float]] = {}

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
        curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
        if curve_cmp.get("count", 0):
            curve_mae.append(float(curve_cmp["mae"]))
            by_mixup_curve_mae.setdefault(classify_csv(csv_path, dataset_root), []).append(
                float(curve_cmp["mae"])
            )
        acutance = acutance_presets_from_mtf(
            scaled_frequencies,
            corrected_mtf_for_acutance,
            pixels_along_picture_height=estimate.roi.height,
            presets=presets,
        )
        acutance_cmp = compare_acutance_presets(acutance, reference.reported_acutance)
        for name, values in acutance_cmp.items():
            acutance_preset_errors.setdefault(name, []).append(float(values["abs_error"]))

        quality_loss = quality_loss_presets_from_acutance(
            acutance,
            om_ceiling=profile.quality_loss_om_ceiling,
            coefficients=tuple(profile.quality_loss_coefficients),
        )
        quality_abs_errors = {}
        for name, value in quality_loss.items():
            abs_error = abs(float(value) - float(reference.reported_quality_loss[name]))
            quality_loss_errors.setdefault(name, []).append(abs_error)
            quality_abs_errors[name] = abs_error
        by_mixup_quality_loss_mae.setdefault(classify_csv(csv_path, dataset_root), []).append(
            float(np.mean(list(quality_abs_errors.values())))
        )

    return {
        "profile_path": str(profile_path),
        "analysis_pipeline": {
            "gamma": profile.gamma,
            "linearization_mode": profile.linearization_mode,
            "linearization_toe": profile.linearization_toe,
            "bayer_pattern": profile.bayer_pattern,
            "bayer_mode": profile.bayer_mode,
            "roi_source": profile.roi_source,
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
