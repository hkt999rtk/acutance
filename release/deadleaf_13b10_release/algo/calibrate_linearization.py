from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dead_leaves import (
    RawLinearization,
    compare_to_imatest,
    estimate_dead_leaves_mtf,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep raw linearization parameters")
    parser.add_argument("raw_path", type=Path)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--calibration-file", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    raw = load_raw_u16(args.raw_path, args.width, args.height)
    reference = parse_imatest_random_csv(args.csv_path)
    ideal_psd_calibration = load_ideal_psd_calibration(args.calibration_file)

    candidates = []
    for gamma in [1.0, 0.8, 0.67, 0.5]:
        for black_percentile in [0.0, 0.05, 0.1, 0.5]:
            for white_percentile in [99.5, 99.8, 99.9, 99.95, 100.0]:
                image = normalize_for_analysis(
                    raw,
                    gamma=gamma,
                    black_percentile=black_percentile,
                    white_percentile=white_percentile,
                )
                result = estimate_dead_leaves_mtf(
                    image,
                    ideal_psd_mode="calibrated_log",
                    ideal_psd_calibration=ideal_psd_calibration,
                )
                comparison = compare_to_imatest(result, reference)
                total_error = (
                    abs(comparison["mtf50_estimate"] - comparison["mtf50_reference"])
                    + abs(comparison["mtf30_estimate"] - comparison["mtf30_reference"])
                    + abs(comparison["mtf20_estimate"] - comparison["mtf20_reference"])
                )
                candidates.append(
                    {
                        "gamma": gamma,
                        "black_percentile": black_percentile,
                        "white_percentile": white_percentile,
                        "mtf50": comparison["mtf50_estimate"],
                        "mtf30": comparison["mtf30_estimate"],
                        "mtf20": comparison["mtf20_estimate"],
                        "error": total_error,
                    }
                )

    candidates.sort(key=lambda item: item["error"])
    print(json.dumps(candidates[:12], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
