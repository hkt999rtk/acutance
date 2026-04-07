from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np

from .dead_leaves import (
    ACUTANCE_HF_NOISE_SHARE_BAND,
    ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS,
    IMATEST_REFERENCE_BINS,
    MTF_SHAPE_CORRECTION_SHARE_GATE,
    RoiBounds,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_mtf_shape_correction,
    compare_acutance_curves,
    compare_acutance_presets,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def classify_csv(csv_path: Path, dataset_root: Path) -> dict[str, str]:
    relative = csv_path.relative_to(dataset_root)
    parts = relative.parts

    if "OV13B10_AI_NR_OV13B10_ori" in parts:
        return {
            "source": "ori",
            "variant": "ori",
            "group": "ori",
        }

    parent = csv_path.parent.parent.name
    mixup_match = re.search(r"_ppqpkl_([0-9.]+)$", parent)
    mixup = mixup_match.group(1) if mixup_match else "unknown"

    if "output2_Bmodel" in parts:
        source = "Bmodel"
    elif "output3_Amodel" in parts:
        source = "Amodel"
    else:
        source = "unknown"

    return {
        "source": source,
        "variant": f"{source}:{mixup}",
        "group": mixup,
    }


def make_accumulator() -> dict[str, object]:
    return {
        "count": 0,
        "curve_mae": [],
        "curve_max_error": [],
        "preset_errors": {},
    }


def append_metrics(
    accumulator: dict[str, object],
    *,
    curve_cmp: dict[str, float],
    preset_cmp: dict[str, dict[str, float]],
) -> None:
    accumulator["count"] = int(accumulator["count"]) + 1

    if curve_cmp.get("count", 0):
        curve_mae = accumulator["curve_mae"]
        curve_max_error = accumulator["curve_max_error"]
        assert isinstance(curve_mae, list)
        assert isinstance(curve_max_error, list)
        curve_mae.append(float(curve_cmp["mae"]))
        curve_max_error.append(float(curve_cmp["max_error"]))

    preset_errors = accumulator["preset_errors"]
    assert isinstance(preset_errors, dict)
    for key, values in preset_cmp.items():
        preset_errors.setdefault(key, []).append(float(values["abs_error"]))


def summarize_accumulator(accumulator: dict[str, object]) -> dict[str, object]:
    curve_mae = accumulator["curve_mae"]
    curve_max_error = accumulator["curve_max_error"]
    preset_errors = accumulator["preset_errors"]
    assert isinstance(curve_mae, list)
    assert isinstance(curve_max_error, list)
    assert isinstance(preset_errors, dict)
    return {
        "count": int(accumulator["count"]),
        "curve_mae_mean": float(np.mean(curve_mae)) if curve_mae else None,
        "curve_max_error_mean": float(np.mean(curve_max_error)) if curve_max_error else None,
        "preset_mae": {
            key: float(np.mean(values))
            for key, values in sorted(preset_errors.items())
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark acutance curve and preset errors")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument("--normalization-band-lo", type=float, default=0.01)
    parser.add_argument("--normalization-band-hi", type=float, default=0.03)
    parser.add_argument(
        "--normalization-mode",
        choices=["max", "mean", "p90"],
        default="max",
    )
    parser.add_argument("--acutance-band-lo", type=float, default=0.017)
    parser.add_argument("--acutance-band-hi", type=float, default=0.035)
    parser.add_argument(
        "--acutance-band-mode",
        choices=["max", "mean", "p90"],
        default="mean",
    )
    parser.add_argument("--signal-psd-correction-gain", type=float, default=0.0)
    parser.add_argument("--signal-psd-correction-start-cpp", type=float, default=0.08)
    parser.add_argument("--signal-psd-correction-peak-cpp", type=float, default=0.15)
    parser.add_argument("--signal-psd-correction-stop-cpp", type=float, default=0.22)
    parser.add_argument(
        "--noise-psd-model",
        choices=["empirical", "colored_log_polynomial"],
        default="empirical",
    )
    parser.add_argument("--noise-psd-log-polynomial-degree", type=int, default=2)
    parser.add_argument("--noise-psd-scale", type=float, default=1.0)
    parser.add_argument("--noise-psd-scale-for-acutance", type=float)
    parser.add_argument(
        "--acutance-noise-scale-mode",
        choices=["fixed", "high_frequency_noise_share_quadratic"],
        default="fixed",
    )
    parser.add_argument(
        "--acutance-noise-share-band-lo",
        type=float,
        default=ACUTANCE_HF_NOISE_SHARE_BAND[0],
    )
    parser.add_argument(
        "--acutance-noise-share-band-hi",
        type=float,
        default=ACUTANCE_HF_NOISE_SHARE_BAND[1],
    )
    parser.add_argument(
        "--acutance-noise-share-scale-coefficients",
        type=float,
        nargs=3,
        default=list(ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS),
    )
    parser.add_argument("--high-frequency-guard-start-cpp", type=float)
    parser.add_argument("--high-frequency-guard-stop-cpp", type=float, default=0.5)
    parser.add_argument(
        "--mtf-shape-correction-mode",
        choices=["none", "hf_noise_share_gated_bump"],
        default="none",
    )
    parser.add_argument("--mtf-shape-correction-gain", type=float, default=0.035)
    parser.add_argument(
        "--mtf-shape-correction-share-gate-lo",
        type=float,
        default=MTF_SHAPE_CORRECTION_SHARE_GATE[0],
    )
    parser.add_argument(
        "--mtf-shape-correction-share-gate-hi",
        type=float,
        default=MTF_SHAPE_CORRECTION_SHARE_GATE[1],
    )
    parser.add_argument("--mtf-shape-correction-mid-start-cpp", type=float, default=0.095)
    parser.add_argument("--mtf-shape-correction-mid-peak-cpp", type=float, default=0.145)
    parser.add_argument("--mtf-shape-correction-mid-stop-cpp", type=float, default=0.19)
    parser.add_argument("--mtf-shape-correction-high-start-cpp", type=float, default=0.36)
    parser.add_argument("--mtf-shape-correction-high-peak-cpp", type=float, default=0.40)
    parser.add_argument("--mtf-shape-correction-high-stop-cpp", type=float, default=0.49)
    parser.add_argument("--mtf-shape-correction-high-weight", type=float, default=0.25)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    calibration = load_ideal_psd_calibration(args.calibration_file)
    bin_centers = IMATEST_REFERENCE_BINS.copy()
    csv_paths = sorted(args.dataset_root.glob("**/Results/*_R_Random.csv"))

    overall = make_accumulator()
    by_source: dict[str, dict[str, object]] = {}
    by_variant: dict[str, dict[str, object]] = {}
    by_group: dict[str, dict[str, object]] = {}

    for csv_path in csv_paths:
        raw_path = csv_path.parent.parent / csv_path.name.replace("_R_Random.csv", ".raw")
        if not raw_path.exists():
            continue

        raw = load_raw_u16(raw_path, args.width, args.height)
        image = normalize_for_analysis(raw, gamma=1.0)
        detected = detect_texture_roi(image)
        roi = RoiBounds.centered(
            center_x=(detected.left + detected.right) // 2,
            center_y=(detected.top + detected.bottom) // 2,
            width=args.roi_width,
            height=args.roi_height,
            image_width=image.shape[1],
            image_height=image.shape[0],
        )
        result = estimate_dead_leaves_mtf(
            image,
            num_bins=len(bin_centers),
            ideal_psd_mode="calibrated_log",
            ideal_psd_calibration=calibration,
            bin_centers=bin_centers,
            roi_override=roi,
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
        curve = acutance_curve_from_mtf(
            result.frequencies_cpp,
            corrected_mtf_for_acutance,
            picture_height_cm=40.0,
            viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
            pixels_along_picture_height=result.roi.height,
        )
        presets = acutance_presets_from_mtf(
            result.frequencies_cpp,
            corrected_mtf_for_acutance,
            pixels_along_picture_height=result.roi.height,
        )
        reference = parse_imatest_random_csv(csv_path)

        curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
        preset_cmp = compare_acutance_presets(presets, reference.reported_acutance)
        labels = classify_csv(csv_path, args.dataset_root)
        append_metrics(overall, curve_cmp=curve_cmp, preset_cmp=preset_cmp)
        append_metrics(
            by_source.setdefault(labels["source"], make_accumulator()),
            curve_cmp=curve_cmp,
            preset_cmp=preset_cmp,
        )
        append_metrics(
            by_variant.setdefault(labels["variant"], make_accumulator()),
            curve_cmp=curve_cmp,
            preset_cmp=preset_cmp,
        )
        append_metrics(
            by_group.setdefault(labels["group"], make_accumulator()),
            curve_cmp=curve_cmp,
            preset_cmp=preset_cmp,
        )

    payload = {
        "overall": summarize_accumulator(overall),
        "by_source": {
            key: summarize_accumulator(values)
            for key, values in sorted(by_source.items())
        },
        "by_variant": {
            key: summarize_accumulator(values)
            for key, values in sorted(by_variant.items())
        },
        "by_mixup": {
            key: summarize_accumulator(values)
            for key, values in sorted(by_group.items())
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
