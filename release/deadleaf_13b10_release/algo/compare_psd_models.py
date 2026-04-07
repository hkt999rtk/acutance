from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    compare_acutance_curves,
    compare_acutance_presets,
    compute_mtf_metrics,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare multiple ideal PSD calibration files")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("calibration_files", nargs="+", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument("--acutance-band-lo", type=float, default=0.017)
    parser.add_argument("--acutance-band-hi", type=float, default=0.035)
    parser.add_argument("--acutance-band-mode", choices=["max", "mean", "p90"], default="mean")
    parser.add_argument("--high-frequency-guard-start-cpp", type=float)
    parser.add_argument("--high-frequency-guard-stop-cpp", type=float, default=0.5)
    return parser


def interpolate_threshold(frequencies: np.ndarray, mtf: np.ndarray, level: float) -> float:
    for idx in range(1, len(mtf)):
        if mtf[idx - 1] >= level >= mtf[idx]:
            t = (level - mtf[idx - 1]) / (mtf[idx] - mtf[idx - 1])
            return float(frequencies[idx - 1] + t * (frequencies[idx] - frequencies[idx - 1]))
    return 0.0


def main() -> int:
    args = build_parser().parse_args()
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
        samples.append((image, roi, parse_imatest_random_csv(csv_path)))

    payload = {}
    for calibration_path in args.calibration_files:
        calibration = load_ideal_psd_calibration(calibration_path)
        mtf50_errors = []
        curve_errors = []
        preset_errors = []
        for image, roi, reference in samples:
            estimate = estimate_dead_leaves_mtf(
                image,
                num_bins=len(IMATEST_REFERENCE_BINS),
                ideal_psd_mode="calibrated_log",
                ideal_psd_calibration=calibration,
                bin_centers=IMATEST_REFERENCE_BINS,
                roi_override=roi,
                acutance_reference_band=(args.acutance_band_lo, args.acutance_band_hi),
                acutance_reference_mode=args.acutance_band_mode,
                high_frequency_guard_start_cpp=args.high_frequency_guard_start_cpp,
                high_frequency_guard_stop_cpp=args.high_frequency_guard_stop_cpp,
            )
            metrics = compute_mtf_metrics(estimate.frequencies_cpp, estimate.mtf)
            ref50 = interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.5)
            mtf50_errors.append(abs(metrics.mtf50 - ref50))

            curve = acutance_curve_from_mtf(
                estimate.frequencies_cpp,
                estimate.mtf_for_acutance,
                picture_height_cm=40.0,
                viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
                pixels_along_picture_height=estimate.roi.height,
            )
            curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
            if curve_cmp.get("count", 0):
                curve_errors.append(float(curve_cmp["mae"]))

            presets = acutance_presets_from_mtf(
                estimate.frequencies_cpp,
                estimate.mtf_for_acutance,
                pixels_along_picture_height=estimate.roi.height,
            )
            preset_cmp = compare_acutance_presets(presets, reference.reported_acutance)
            preset_errors.extend(float(item["abs_error"]) for item in preset_cmp.values())

        payload[str(calibration_path)] = {
            "source_count": len(samples),
            "is_piecewise": calibration.is_piecewise,
            "polynomial_degree": calibration.polynomial_degree,
            "mtf50_mae": float(np.mean(mtf50_errors)),
            "curve_mae": float(np.mean(curve_errors)),
            "preset_mae_mean": float(np.mean(preset_errors)),
        }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
