from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    apply_frequency_scale,
    compute_mtf_metrics,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    estimate_texture_support_scale,
    interpolate_threshold,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark MTF threshold readout policies")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument(
        "--windows",
        type=int,
        nargs="+",
        default=[1, 5, 7],
        help="Odd smoothing windows to benchmark",
    )
    parser.add_argument(
        "--interpolations",
        nargs="+",
        choices=["linear", "log_frequency"],
        default=["linear", "log_frequency"],
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    calibration = load_ideal_psd_calibration(args.calibration_file)
    bin_centers = IMATEST_REFERENCE_BINS.copy()
    csv_paths = sorted(args.dataset_root.glob("output*_*/**/Results/*_R_Random.csv"))

    policies = [
        (window, interpolation)
        for window in args.windows
        for interpolation in args.interpolations
    ]
    summary: dict[str, dict[str, list[float] | int]] = {
        f"window={window},interpolation={interpolation}": {
            "e50": [],
            "e30": [],
            "e20": [],
            "count": 0,
        }
        for window, interpolation in policies
    }

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
        )
        crop = image[result.roi.top : result.roi.bottom + 1, result.roi.left : result.roi.right + 1]
        support = estimate_texture_support_scale(crop, percentile=45.0)
        frequencies = apply_frequency_scale(
            result.frequencies_cpp,
            scale=support.frequency_scale,
        )

        reference = parse_imatest_random_csv(csv_path)
        ref50 = interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.5)
        ref30 = interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.3)
        ref20 = interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.2)

        for window, interpolation in policies:
            metrics = compute_mtf_metrics(
                frequencies,
                result.mtf,
                smoothing_window=window,
                interpolation_mode=interpolation,
            )
            key = f"window={window},interpolation={interpolation}"
            summary[key]["e50"].append(abs(metrics.mtf50 - ref50))
            summary[key]["e30"].append(abs(metrics.mtf30 - ref30))
            summary[key]["e20"].append(abs(metrics.mtf20 - ref20))
            summary[key]["count"] += 1

    payload = {}
    for key, values in summary.items():
        count = int(values["count"])
        payload[key] = {
            "count": count,
            "mae50": float(np.mean(values["e50"])) if count else None,
            "mae30": float(np.mean(values["e30"])) if count else None,
            "mae20": float(np.mean(values["e20"])) if count else None,
        }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
