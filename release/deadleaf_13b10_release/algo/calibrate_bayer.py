from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dead_leaves import (
    BayerMode,
    BayerPattern,
    extract_analysis_plane,
    estimate_dead_leaves_mtf,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare Bayer options against Imatest CSV")
    parser.add_argument("raw_path", type=Path)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--gamma", type=float, default=0.5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    raw = load_raw_u16(args.raw_path, args.width, args.height)
    reference = parse_imatest_random_csv(args.csv_path)

    modes = [
        (BayerMode.GRAY, None),
        (BayerMode.DEMOSAIC_RED, BayerPattern.RGGB),
        (BayerMode.DEMOSAIC_RED, BayerPattern.BGGR),
        (BayerMode.DEMOSAIC_RED, BayerPattern.GRBG),
        (BayerMode.DEMOSAIC_RED, BayerPattern.GBRG),
        (BayerMode.RAW_RED_UPSAMPLED, BayerPattern.RGGB),
        (BayerMode.RAW_RED_UPSAMPLED, BayerPattern.BGGR),
        (BayerMode.RAW_RED_UPSAMPLED, BayerPattern.GRBG),
        (BayerMode.RAW_RED_UPSAMPLED, BayerPattern.GBRG),
    ]

    rows = []
    for mode, pattern in modes:
        plane = extract_analysis_plane(
            raw,
            bayer_pattern=pattern or BayerPattern.RGGB,
            mode=mode,
        )
        image = normalize_for_analysis(plane, gamma=args.gamma)
        result = estimate_dead_leaves_mtf(image)
        rows.append(
            {
                "mode": str(mode.value),
                "pattern": None if pattern is None else pattern.value,
                "roi": [result.roi.left, result.roi.right, result.roi.top, result.roi.bottom],
                "mtf50": result.metrics.mtf50,
                "mtf30": result.metrics.mtf30,
                "mtf20": result.metrics.mtf20,
                "mtf50_error": abs(result.metrics.mtf50 - reference_reported_mtf(reference, 0.5)),
                "mtf30_error": abs(result.metrics.mtf30 - reference_reported_mtf(reference, 0.3)),
                "mtf20_error": abs(result.metrics.mtf20 - reference_reported_mtf(reference, 0.2)),
            }
        )

    print(json.dumps(rows, indent=2))
    return 0


def reference_reported_mtf(reference, level: float) -> float:
    from .dead_leaves import interpolate_threshold

    return interpolate_threshold(reference.frequencies_cpp, reference.mtf, level)


if __name__ == "__main__":
    raise SystemExit(main())
