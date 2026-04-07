from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    DEFAULT_ACUTANCE_PRESETS,
    RoiBounds,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare print display-MTF model shapes")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["gaussian", "exponential", "lorentzian", "ideal_lowpass"],
        default=["gaussian", "exponential", "lorentzian", "ideal_lowpass"],
    )
    parser.add_argument("--small-print-c50-values", type=float, nargs="+", default=[20.0, 22.0, 24.0, 26.0, 28.0])
    parser.add_argument("--large-print-c50-values", type=float, nargs="+", default=[20.0, 22.0, 24.0, 26.0, 28.0])
    parser.add_argument("--high-frequency-guard-start-cpp", type=float, default=0.36)
    parser.add_argument("--high-frequency-guard-stop-cpp", type=float, default=0.5)
    return parser


def display_mtf(model: str, angular_frequency: np.ndarray, c50_cpd: float) -> np.ndarray:
    v = np.asarray(angular_frequency, dtype=np.float64)
    c50 = max(float(c50_cpd), 1e-12)
    if model == "gaussian":
        return np.exp(-math.log(2.0) * np.square(v / c50))
    if model == "exponential":
        return np.exp(-math.log(2.0) * (v / c50))
    if model == "lorentzian":
        return 1.0 / (1.0 + v / c50)
    if model == "ideal_lowpass":
        return np.where(v <= c50, 1.0, 0.0)
    raise ValueError(f"Unknown model: {model}")


def acutance_with_display_model(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    picture_height_cm: float,
    viewing_distance_cm: float,
    pixels_along_picture_height: int,
    model: str,
    c50_cpd: float,
) -> float:
    angular_frequency = (
        np.pi
        * float(pixels_along_picture_height)
        * float(viewing_distance_cm)
        * np.asarray(frequencies_cpp, dtype=np.float64)
        / (180.0 * float(picture_height_cm))
    )
    effective_mtf = np.asarray(mtf, dtype=np.float64) * display_mtf(model, angular_frequency, c50_cpd)
    csf = (
        75.0
        * np.power(np.maximum(angular_frequency, 0.0), 0.8)
        * np.exp(-0.2 * angular_frequency)
        / 34.05
    )
    numerator = np.trapezoid(effective_mtf * csf, angular_frequency)
    denominator = (75.0 / 34.05) * math.gamma(1.8) / (0.2**1.8)
    return float(numerator / max(denominator, 1e-12))


def main() -> int:
    args = build_parser().parse_args()
    calibration = load_ideal_psd_calibration(args.calibration_file)
    csv_paths = sorted(args.dataset_root.glob("**/Results/*_R_Random.csv"))

    samples = []
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
        estimate = estimate_dead_leaves_mtf(
            image,
            num_bins=len(IMATEST_REFERENCE_BINS),
            ideal_psd_mode="calibrated_log",
            ideal_psd_calibration=calibration,
            bin_centers=IMATEST_REFERENCE_BINS,
            roi_override=roi,
            acutance_reference_band=(0.017, 0.035),
            acutance_reference_mode="mean",
            high_frequency_guard_start_cpp=args.high_frequency_guard_start_cpp,
            high_frequency_guard_stop_cpp=args.high_frequency_guard_stop_cpp,
        )
        samples.append((estimate, parse_imatest_random_csv(csv_path)))

    base_presets = {preset.name: preset for preset in DEFAULT_ACUTANCE_PRESETS}
    payload = {}
    for model in args.models:
        for small_c50 in args.small_print_c50_values:
            for large_c50 in args.large_print_c50_values:
                errors = {name: [] for name in base_presets}
                for estimate, reference in samples:
                    result = {}
                    for name, preset in base_presets.items():
                        if name == "Small Print Acutance":
                            result[name] = acutance_with_display_model(
                                estimate.frequencies_cpp,
                                estimate.mtf_for_acutance,
                                picture_height_cm=preset.picture_height_cm,
                                viewing_distance_cm=preset.viewing_distance_cm,
                                pixels_along_picture_height=estimate.roi.height,
                                model=model,
                                c50_cpd=small_c50,
                            )
                        elif name == "Large Print Acutance":
                            result[name] = acutance_with_display_model(
                                estimate.frequencies_cpp,
                                estimate.mtf_for_acutance,
                                picture_height_cm=preset.picture_height_cm,
                                viewing_distance_cm=preset.viewing_distance_cm,
                                pixels_along_picture_height=estimate.roi.height,
                                model=model,
                                c50_cpd=large_c50,
                            )
                        else:
                            result[name] = reference.reported_acutance[name]
                    for name, value in result.items():
                        if name not in ("Small Print Acutance", "Large Print Acutance"):
                            continue
                        errors[name].append(abs(value - reference.reported_acutance[name]))
                key = f"{model}:small={small_c50:g},large={large_c50:g}"
                small_mae = float(np.mean(errors["Small Print Acutance"]))
                large_mae = float(np.mean(errors["Large Print Acutance"]))
                payload[key] = {
                    "small_print_mae": small_mae,
                    "large_print_mae": large_mae,
                    "print_mae_mean": float(np.mean([small_mae, large_mae])),
                }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
