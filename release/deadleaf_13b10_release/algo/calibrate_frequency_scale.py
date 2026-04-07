from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    apply_frequency_scale,
    extract_roi,
    ideal_dead_leaves_psd,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
    radial_psd,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit a global frequency scale against Imatest CSVs")
    parser.add_argument("csv_root", type=Path)
    parser.add_argument("--glob", default="**/*_R_Random.csv")
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--scale-min", type=float, default=1.0)
    parser.add_argument("--scale-max", type=float, default=1.15)
    parser.add_argument("--steps", type=int, default=31)
    return parser


def interpolate_threshold(f: np.ndarray, y: np.ndarray, level: float) -> float:
    for idx in range(1, len(y)):
        if y[idx - 1] >= level >= y[idx]:
            t = (level - y[idx - 1]) / (y[idx] - y[idx - 1])
            return float(f[idx - 1] + t * (f[idx] - f[idx - 1]))
    return 0.0


def main() -> int:
    args = build_parser().parse_args()
    calibration = load_ideal_psd_calibration(args.calibration_file)
    csv_paths = sorted(args.csv_root.glob(args.glob))
    scales = np.linspace(args.scale_min, args.scale_max, args.steps)
    totals = np.zeros_like(scales)

    for csv_path in csv_paths:
        reference = parse_imatest_random_csv(csv_path)
        rows = list(csv.reader(csv_path.open("r", encoding="utf-8", errors="ignore")))
        ref50 = next(float(r[1]) for r in rows if r and r[0].startswith("MTF50 C/P"))
        ref30 = next(float(r[1]) for r in rows if r and r[0].startswith("MTF30 C/P"))
        ref20 = next(float(r[1]) for r in rows if r and r[0].startswith("MTF20 C/P"))

        raw_path = csv_path.parent.parent / csv_path.name.replace("_R_Random.csv", ".raw")
        raw = load_raw_u16(raw_path, args.width, args.height)
        image = normalize_for_analysis(raw, gamma=1.0)
        crop = extract_roi(image, reference.lrtb)
        frequencies, psd = radial_psd(
            crop,
            num_bins=len(reference.frequencies_cpp),
            bin_centers=IMATEST_REFERENCE_BINS,
            window=True,
        )
        ideal = ideal_dead_leaves_psd(
            frequencies,
            length_px=max(crop.shape),
            mode="calibrated_log",
            calibration=calibration,
        )
        mtf = np.sqrt(np.maximum(psd / ideal, 0.0))
        mtf /= max(float(mtf[np.argmin(np.abs(frequencies - 0.0177))]), 1e-12)

        for idx, scale in enumerate(scales):
            scaled = apply_frequency_scale(frequencies, scale=float(scale))
            pred50 = interpolate_threshold(scaled, mtf, 0.5)
            pred30 = interpolate_threshold(scaled, mtf, 0.3)
            pred20 = interpolate_threshold(scaled, mtf, 0.2)
            totals[idx] += abs(pred50 - ref50) + abs(pred30 - ref30) + abs(pred20 - ref20)

    best_idx = int(np.argmin(totals))
    payload = {
        "best_scale": float(scales[best_idx]),
        "total_error": float(totals[best_idx]),
        "source_count": len(csv_paths),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
