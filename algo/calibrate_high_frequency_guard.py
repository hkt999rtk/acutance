from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    anchor_mtf_to_dc,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_high_frequency_guard,
    compare_acutance_curves,
    compare_acutance_presets,
    compute_mtf_metrics,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    ideal_dead_leaves_psd,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_mtf_curve,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep high-frequency guard settings")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument("--guard-start-min", type=float, default=0.28)
    parser.add_argument("--guard-start-max", type=float, default=0.42)
    parser.add_argument("--guard-start-step", type=float, default=0.02)
    parser.add_argument("--guard-stop", type=float, default=0.5)
    return parser


def interpolate_threshold(frequencies: np.ndarray, mtf: np.ndarray, level: float) -> float:
    for idx in range(1, len(mtf)):
        if mtf[idx - 1] >= level >= mtf[idx]:
            t = (level - mtf[idx - 1]) / (mtf[idx] - mtf[idx - 1])
            return float(frequencies[idx - 1] + t * (frequencies[idx] - frequencies[idx - 1]))
    return 0.0


def main() -> int:
    args = build_parser().parse_args()
    calibration = load_ideal_psd_calibration(args.calibration_file)
    csv_paths = sorted(args.dataset_root.glob("**/Results/*_R_Random.csv"))
    starts = np.arange(
        args.guard_start_min,
        args.guard_start_max + args.guard_start_step * 0.5,
        args.guard_start_step,
    )

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
        reference = parse_imatest_random_csv(csv_path)
        estimate = estimate_dead_leaves_mtf(
            image,
            num_bins=len(IMATEST_REFERENCE_BINS),
            ideal_psd_mode="calibrated_log",
            ideal_psd_calibration=calibration,
            bin_centers=IMATEST_REFERENCE_BINS,
            roi_override=roi,
            acutance_reference_band=(0.017, 0.035),
            acutance_reference_mode="mean",
        )
        samples.append(
            {
                "reference": reference,
                "roi_height": estimate.roi.height,
                "frequencies": estimate.frequencies_cpp.copy(),
                "signal_plus_noise_psd": estimate.psd_signal_plus_noise.copy(),
                "noise_psd": estimate.psd_noise.copy(),
                "ideal_psd": ideal_dead_leaves_psd(
                    estimate.frequencies_cpp,
                    length_px=max(roi.width, roi.height),
                    mode="calibrated_log",
                    calibration=calibration,
                ),
            }
        )

    results = []
    for start in starts:
        mtf50_errors = []
        curve_errors = []
        preset_errors = []
        preset_errors_by_name: dict[str, list[float]] = {}
        for sample in samples:
            frequencies = sample["frequencies"]
            signal_psd = np.maximum(
                sample["signal_plus_noise_psd"] - sample["noise_psd"],
                0.0,
            )
            guarded_signal_psd = apply_high_frequency_guard(
                signal_psd,
                frequencies,
                start_cpp=float(start),
                stop_cpp=args.guard_stop,
            )
            reference = sample["reference"]
            ideal_psd = sample["ideal_psd"]
            mtf_unnormalized = np.sqrt(
                np.maximum(guarded_signal_psd / np.maximum(ideal_psd, 1e-12), 0.0)
            )
            mtf = normalize_mtf_curve(
                mtf_unnormalized,
                frequencies,
                reference_band=(0.01, 0.03),
                reference_mode="max",
            )
            mtf_for_acutance = anchor_mtf_to_dc(
                mtf_unnormalized,
                frequencies,
                reference_band=(0.017, 0.035),
                reference_mode="mean",
            )
            metrics = compute_mtf_metrics(frequencies, mtf)
            ref50 = interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.5)
            mtf50_errors.append(abs(metrics.mtf50 - ref50))

            curve = acutance_curve_from_mtf(
                frequencies,
                mtf_for_acutance,
                picture_height_cm=40.0,
                viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
                pixels_along_picture_height=int(sample["roi_height"]),
            )
            curve_cmp = compare_acutance_curves(curve, reference.acutance_table)
            if curve_cmp.get("count", 0):
                curve_errors.append(float(curve_cmp["mae"]))

            presets = acutance_presets_from_mtf(
                frequencies,
                mtf_for_acutance,
                pixels_along_picture_height=int(sample["roi_height"]),
            )
            preset_cmp = compare_acutance_presets(presets, reference.reported_acutance)
            for key, values in preset_cmp.items():
                abs_error = float(values["abs_error"])
                preset_errors.append(abs_error)
                preset_errors_by_name.setdefault(key, []).append(abs_error)

        results.append(
            {
                "guard_start_cpp": float(start),
                "guard_stop_cpp": float(args.guard_stop),
                "mtf50_mae": float(np.mean(mtf50_errors)),
                "curve_mae": float(np.mean(curve_errors)) if curve_errors else None,
                "preset_mae_mean": float(np.mean(preset_errors)) if preset_errors else None,
                "preset_mae": {
                    key: float(np.mean(values))
                    for key, values in sorted(preset_errors_by_name.items())
                },
            }
        )

    best_mtf50 = min(results, key=lambda row: row["mtf50_mae"])
    best_curve = min(results, key=lambda row: float(row["curve_mae"]))
    best_preset = min(results, key=lambda row: float(row["preset_mae_mean"]))
    payload = {
        "count": len(samples),
        "results": results,
        "best_mtf50": best_mtf50,
        "best_curve": best_curve,
        "best_preset": best_preset,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
