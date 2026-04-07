from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    ACUTANCE_HF_NOISE_SHARE_BAND,
    ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS,
    MTF_SHAPE_CORRECTION_SHARE_GATE,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_mtf_shape_correction,
    quality_loss_presets_from_acutance,
    BayerMode,
    BayerPattern,
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    apply_frequency_scale,
    compute_mtf_metrics,
    estimate_texture_support_scale,
    load_ideal_psd_calibration,
    acutance_from_mtf,
    compare_acutance_curves,
    compare_acutance_presets,
    compare_to_imatest,
    detect_texture_roi,
    extract_analysis_plane,
    estimate_dead_leaves_mtf,
    refine_roi_to_texture_support,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dead-leaves / acutance prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze one raw file")
    analyze.add_argument("raw_path", type=Path)
    analyze.add_argument("--width", type=int, required=True)
    analyze.add_argument("--height", type=int, required=True)
    analyze.add_argument("--gamma", type=float, default=1.0)
    analyze.add_argument("--black-level", type=float)
    analyze.add_argument("--white-level", type=float)
    analyze.add_argument("--black-percentile", type=float, default=0.1)
    analyze.add_argument("--white-percentile", type=float, default=99.9)
    analyze.add_argument("--roi-width", type=int)
    analyze.add_argument("--roi-height", type=int)
    analyze.add_argument("--reference-bins", action="store_true")
    analyze.add_argument("--refine-roi-center", action="store_true")
    analyze.add_argument("--roi-search-radius", type=int, default=12)
    analyze.add_argument("--roi-search-step", type=int, default=2)
    analyze.add_argument("--texture-support-scale", action="store_true")
    analyze.add_argument("--texture-support-percentile", type=float, default=45.0)
    analyze.add_argument("--texture-support-margin", type=int, default=8)
    analyze.add_argument(
        "--bayer-pattern",
        choices=[pattern.value for pattern in BayerPattern],
        default=BayerPattern.RGGB.value,
    )
    analyze.add_argument(
        "--bayer-mode",
        choices=[mode.value for mode in BayerMode],
        default=BayerMode.GRAY.value,
    )
    analyze.add_argument("--bins", type=int, default=64)
    analyze.add_argument(
        "--ideal-psd-mode",
        choices=["quadratic_log", "power_law", "calibrated_log"],
        default="quadratic_log",
    )
    analyze.add_argument("--frequency-scale", type=float, default=1.0)
    analyze.add_argument("--normalization-band-lo", type=float, default=0.01)
    analyze.add_argument("--normalization-band-hi", type=float, default=0.03)
    analyze.add_argument(
        "--normalization-mode",
        choices=["max", "mean", "p90"],
        default="max",
    )
    analyze.add_argument("--acutance-band-lo", type=float, default=0.017)
    analyze.add_argument("--acutance-band-hi", type=float, default=0.035)
    analyze.add_argument(
        "--acutance-band-mode",
        choices=["max", "mean", "p90"],
        default="mean",
    )
    analyze.add_argument("--readout-smoothing-window", type=int, default=1)
    analyze.add_argument(
        "--readout-interpolation",
        choices=["linear", "log_frequency"],
        default="linear",
    )
    analyze.add_argument("--calibration-file", type=Path)
    analyze.add_argument("--signal-psd-correction-gain", type=float, default=0.0)
    analyze.add_argument("--signal-psd-correction-start-cpp", type=float, default=0.08)
    analyze.add_argument("--signal-psd-correction-peak-cpp", type=float, default=0.15)
    analyze.add_argument("--signal-psd-correction-stop-cpp", type=float, default=0.22)
    analyze.add_argument(
        "--noise-psd-model",
        choices=["empirical", "colored_log_polynomial"],
        default="empirical",
    )
    analyze.add_argument("--noise-psd-log-polynomial-degree", type=int, default=2)
    analyze.add_argument("--noise-psd-scale", type=float, default=1.0)
    analyze.add_argument("--noise-psd-scale-for-acutance", type=float)
    analyze.add_argument(
        "--acutance-noise-scale-mode",
        choices=["fixed", "high_frequency_noise_share_quadratic"],
        default="fixed",
    )
    analyze.add_argument(
        "--acutance-noise-share-band-lo",
        type=float,
        default=ACUTANCE_HF_NOISE_SHARE_BAND[0],
    )
    analyze.add_argument(
        "--acutance-noise-share-band-hi",
        type=float,
        default=ACUTANCE_HF_NOISE_SHARE_BAND[1],
    )
    analyze.add_argument(
        "--acutance-noise-share-scale-coefficients",
        type=float,
        nargs=3,
        default=list(ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS),
    )
    analyze.add_argument("--high-frequency-guard-start-cpp", type=float)
    analyze.add_argument("--high-frequency-guard-stop-cpp", type=float, default=0.5)
    analyze.add_argument(
        "--mtf-shape-correction-mode",
        choices=["none", "hf_noise_share_gated_bump"],
        default="none",
    )
    analyze.add_argument("--mtf-shape-correction-gain", type=float, default=0.035)
    analyze.add_argument(
        "--mtf-shape-correction-share-gate-lo",
        type=float,
        default=MTF_SHAPE_CORRECTION_SHARE_GATE[0],
    )
    analyze.add_argument(
        "--mtf-shape-correction-share-gate-hi",
        type=float,
        default=MTF_SHAPE_CORRECTION_SHARE_GATE[1],
    )
    analyze.add_argument("--mtf-shape-correction-mid-start-cpp", type=float, default=0.095)
    analyze.add_argument("--mtf-shape-correction-mid-peak-cpp", type=float, default=0.145)
    analyze.add_argument("--mtf-shape-correction-mid-stop-cpp", type=float, default=0.19)
    analyze.add_argument("--mtf-shape-correction-high-start-cpp", type=float, default=0.36)
    analyze.add_argument("--mtf-shape-correction-high-peak-cpp", type=float, default=0.40)
    analyze.add_argument("--mtf-shape-correction-high-stop-cpp", type=float, default=0.49)
    analyze.add_argument("--mtf-shape-correction-high-weight", type=float, default=0.25)
    analyze.add_argument("--picture-height-cm", type=float, default=40.0)
    analyze.add_argument("--view-distance-cm", type=float, default=100.0)
    analyze.add_argument("--compare-csv", type=Path)

    return parser


def cmd_analyze(args: argparse.Namespace) -> int:
    raw = load_raw_u16(args.raw_path, args.width, args.height)
    plane = extract_analysis_plane(
        raw,
        bayer_pattern=BayerPattern(args.bayer_pattern),
        mode=BayerMode(args.bayer_mode),
    )
    image = normalize_for_analysis(
        plane,
        gamma=args.gamma,
        black_level=args.black_level,
        white_level=args.white_level,
        black_percentile=args.black_percentile,
        white_percentile=args.white_percentile,
    )
    seed_roi = None
    if args.roi_width or args.roi_height:
        detected = detect_texture_roi(image)
        cx = (detected.left + detected.right) // 2
        cy = (detected.top + detected.bottom) // 2
        roi_width = args.roi_width or detected.width
        roi_height = args.roi_height or detected.height
        seed_roi = RoiBounds.centered(
            center_x=cx,
            center_y=cy,
            width=roi_width,
            height=roi_height,
            image_width=image.shape[1],
            image_height=image.shape[0],
        )
        if args.refine_roi_center:
            seed_roi = refine_roi_to_texture_support(
                image,
                seed_roi=seed_roi,
                target_width=roi_width,
                target_height=roi_height,
                percentile=args.texture_support_percentile,
                min_border_margin=args.texture_support_margin,
                search_radius=args.roi_search_radius,
                step=args.roi_search_step,
            )
    bin_centers = None
    if args.reference_bins:
        bin_centers = IMATEST_REFERENCE_BINS.copy()
    calibration = (
        load_ideal_psd_calibration(args.calibration_file)
        if args.calibration_file is not None
        else None
    )
    result = estimate_dead_leaves_mtf(
        image,
        num_bins=len(bin_centers) if bin_centers is not None else args.bins,
        ideal_psd_mode=args.ideal_psd_mode,
        ideal_psd_calibration=calibration,
        bin_centers=bin_centers,
        roi_override=seed_roi,
        normalization_band=(args.normalization_band_lo, args.normalization_band_hi),
        normalization_mode=args.normalization_mode,
        acutance_reference_band=(args.acutance_band_lo, args.acutance_band_hi),
        acutance_reference_mode=args.acutance_band_mode,
        signal_psd_correction_gain=args.signal_psd_correction_gain,
        signal_psd_correction_start_cpp=args.signal_psd_correction_start_cpp,
        signal_psd_correction_peak_cpp=args.signal_psd_correction_peak_cpp,
        signal_psd_correction_stop_cpp=args.signal_psd_correction_stop_cpp,
        noise_psd_model=args.noise_psd_model,
        noise_psd_log_polynomial_degree=args.noise_psd_log_polynomial_degree,
        noise_psd_scale=args.noise_psd_scale,
        noise_psd_scale_for_acutance=args.noise_psd_scale_for_acutance,
        acutance_noise_scale_model=args.acutance_noise_scale_mode,
        acutance_noise_share_band=(
            args.acutance_noise_share_band_lo,
            args.acutance_noise_share_band_hi,
        ),
        acutance_noise_share_scale_coefficients=tuple(
            args.acutance_noise_share_scale_coefficients
        ),
        high_frequency_guard_start_cpp=args.high_frequency_guard_start_cpp,
        high_frequency_guard_stop_cpp=args.high_frequency_guard_stop_cpp,
    )
    effective_frequency_scale = args.frequency_scale
    texture_support = None
    if args.texture_support_scale:
        crop = image[result.roi.top : result.roi.bottom + 1, result.roi.left : result.roi.right + 1]
        texture_support = estimate_texture_support_scale(
            crop,
            percentile=args.texture_support_percentile,
        )
        effective_frequency_scale *= texture_support.frequency_scale
    scaled_frequencies = apply_frequency_scale(
        result.frequencies_cpp,
        scale=effective_frequency_scale,
    )
    corrected_mtf, mtf_shape_correction_curve = apply_mtf_shape_correction(
        result.mtf,
        result.frequencies_cpp,
        mode=args.mtf_shape_correction_mode,
        high_frequency_noise_share=result.acutance_high_frequency_noise_share,
        gain=args.mtf_shape_correction_gain,
        share_gate_lo=args.mtf_shape_correction_share_gate_lo,
        share_gate_hi=args.mtf_shape_correction_share_gate_hi,
        mid_start_cpp=args.mtf_shape_correction_mid_start_cpp,
        mid_peak_cpp=args.mtf_shape_correction_mid_peak_cpp,
        mid_stop_cpp=args.mtf_shape_correction_mid_stop_cpp,
        high_start_cpp=args.mtf_shape_correction_high_start_cpp,
        high_peak_cpp=args.mtf_shape_correction_high_peak_cpp,
        high_stop_cpp=args.mtf_shape_correction_high_stop_cpp,
        high_weight=args.mtf_shape_correction_high_weight,
    )
    corrected_mtf_for_acutance, _ = apply_mtf_shape_correction(
        result.mtf_for_acutance,
        result.frequencies_cpp,
        mode=args.mtf_shape_correction_mode,
        high_frequency_noise_share=result.acutance_high_frequency_noise_share,
        gain=args.mtf_shape_correction_gain,
        share_gate_lo=args.mtf_shape_correction_share_gate_lo,
        share_gate_hi=args.mtf_shape_correction_share_gate_hi,
        mid_start_cpp=args.mtf_shape_correction_mid_start_cpp,
        mid_peak_cpp=args.mtf_shape_correction_mid_peak_cpp,
        mid_stop_cpp=args.mtf_shape_correction_mid_stop_cpp,
        high_start_cpp=args.mtf_shape_correction_high_start_cpp,
        high_peak_cpp=args.mtf_shape_correction_high_peak_cpp,
        high_stop_cpp=args.mtf_shape_correction_high_stop_cpp,
        high_weight=args.mtf_shape_correction_high_weight,
    )
    scaled_metrics = compute_mtf_metrics(
        scaled_frequencies,
        corrected_mtf,
        smoothing_window=args.readout_smoothing_window,
        interpolation_mode=args.readout_interpolation,
    )
    acutance_normalized = acutance_from_mtf(
        scaled_frequencies,
        corrected_mtf,
        picture_height_cm=args.picture_height_cm,
        viewing_distance_cm=args.view_distance_cm,
        pixels_along_picture_height=result.roi.height,
    )
    acutance_unnormalized = acutance_from_mtf(
        result.frequencies_cpp,
        corrected_mtf_for_acutance,
        picture_height_cm=args.picture_height_cm,
        viewing_distance_cm=args.view_distance_cm,
        pixels_along_picture_height=result.roi.height,
    )
    acutance_curve = acutance_curve_from_mtf(
        result.frequencies_cpp,
        corrected_mtf_for_acutance,
        picture_height_cm=args.picture_height_cm,
        viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
        pixels_along_picture_height=result.roi.height,
    )
    acutance_presets = acutance_presets_from_mtf(
        result.frequencies_cpp,
        corrected_mtf_for_acutance,
        pixels_along_picture_height=result.roi.height,
    )
    quality_loss_presets = quality_loss_presets_from_acutance(acutance_presets)

    payload: dict[str, object] = {
        "raw_path": str(args.raw_path),
        "roi": {
            "left": result.roi.left,
            "right": result.roi.right,
            "top": result.roi.top,
            "bottom": result.roi.bottom,
            "width": result.roi.width,
            "height": result.roi.height,
        },
        "metrics": {
            "mtf70_cpp": scaled_metrics.mtf70,
            "mtf50_cpp": scaled_metrics.mtf50,
            "mtf30_cpp": scaled_metrics.mtf30,
            "mtf20_cpp": scaled_metrics.mtf20,
            "mtf10_cpp": scaled_metrics.mtf10,
            "undersharpening_pct": scaled_metrics.undersharpening_pct,
            "acutance": acutance_unnormalized,
            "acutance_normalized_mtf": acutance_normalized,
            "acutance_unnormalized_mtf": acutance_unnormalized,
            "frequency_scale": effective_frequency_scale,
            "normalization_band": [
                args.normalization_band_lo,
                args.normalization_band_hi,
            ],
            "normalization_mode": args.normalization_mode,
            "acutance_band": [
                args.acutance_band_lo,
                args.acutance_band_hi,
            ],
            "acutance_band_mode": args.acutance_band_mode,
            "readout_smoothing_window": args.readout_smoothing_window,
            "readout_interpolation": args.readout_interpolation,
            "signal_psd_correction_gain": args.signal_psd_correction_gain,
            "signal_psd_correction_start_cpp": args.signal_psd_correction_start_cpp,
            "signal_psd_correction_peak_cpp": args.signal_psd_correction_peak_cpp,
            "signal_psd_correction_stop_cpp": args.signal_psd_correction_stop_cpp,
            "noise_psd_model": args.noise_psd_model,
            "noise_psd_log_polynomial_degree": args.noise_psd_log_polynomial_degree,
            "noise_psd_scale": args.noise_psd_scale,
            "noise_psd_scale_for_acutance": args.noise_psd_scale_for_acutance,
            "acutance_noise_scale_mode": args.acutance_noise_scale_mode,
            "acutance_noise_share_band": [
                args.acutance_noise_share_band_lo,
                args.acutance_noise_share_band_hi,
            ],
            "acutance_noise_share_scale_coefficients": args.acutance_noise_share_scale_coefficients,
            "high_frequency_guard_start_cpp": args.high_frequency_guard_start_cpp,
            "high_frequency_guard_stop_cpp": args.high_frequency_guard_stop_cpp,
            "mtf_shape_correction_mode": args.mtf_shape_correction_mode,
            "mtf_shape_correction_gain": args.mtf_shape_correction_gain,
            "mtf_shape_correction_share_gate_lo": args.mtf_shape_correction_share_gate_lo,
            "mtf_shape_correction_share_gate_hi": args.mtf_shape_correction_share_gate_hi,
            "mtf_shape_correction_mid_start_cpp": args.mtf_shape_correction_mid_start_cpp,
            "mtf_shape_correction_mid_peak_cpp": args.mtf_shape_correction_mid_peak_cpp,
            "mtf_shape_correction_mid_stop_cpp": args.mtf_shape_correction_mid_stop_cpp,
            "mtf_shape_correction_high_start_cpp": args.mtf_shape_correction_high_start_cpp,
            "mtf_shape_correction_high_peak_cpp": args.mtf_shape_correction_high_peak_cpp,
            "mtf_shape_correction_high_stop_cpp": args.mtf_shape_correction_high_stop_cpp,
            "mtf_shape_correction_high_weight": args.mtf_shape_correction_high_weight,
            "acutance_noise_scale_used": result.acutance_noise_scale,
            "acutance_high_frequency_noise_share": result.acutance_high_frequency_noise_share,
        },
        "acutance_curve": [
            {
                "print_height_cm": point.print_height_cm,
                "viewing_distance_cm": point.viewing_distance_cm,
                "acutance": point.acutance,
            }
            for point in acutance_curve
        ],
        "acutance_presets": acutance_presets,
        "quality_loss_presets": quality_loss_presets,
        "mtf_shape_correction_curve": mtf_shape_correction_curve.tolist(),
    }
    if texture_support is not None:
        payload["texture_support"] = {
            "bbox": list(texture_support.bbox),
            "percentile": texture_support.percentile,
            "crop_support_size": texture_support.crop_support_size,
            "texture_support_size": texture_support.texture_support_size,
            "frequency_scale": texture_support.frequency_scale,
            "component_area_px": texture_support.component_area_px,
            "border_margin_px": texture_support.border_margin_px,
            "center_offset_px": texture_support.center_offset_px,
            "aspect_ratio": texture_support.aspect_ratio,
        }

    if args.compare_csv:
        reference = parse_imatest_random_csv(args.compare_csv)
        comparison = compare_to_imatest(result, reference)
        comparison["mtf50_estimate"] = scaled_metrics.mtf50
        comparison["mtf30_estimate"] = scaled_metrics.mtf30
        comparison["mtf20_estimate"] = scaled_metrics.mtf20
        comparison["use_unnormalized_mtf_for_acutance"] = (
            reference.use_unnormalized_mtf_for_acutance
        )
        comparison["acutance_curve"] = compare_acutance_curves(
            acutance_curve,
            reference.acutance_table,
        )
        comparison["acutance_presets"] = compare_acutance_presets(
            acutance_presets,
            reference.reported_acutance,
        )
        payload["comparison"] = comparison

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "analyze":
        return cmd_analyze(args)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
