from __future__ import annotations

import argparse
from pathlib import Path

from .dead_leaves import (
    fit_anchored_high_frequency_ideal_psd_calibration_from_csvs,
    fit_ideal_psd_calibration_from_csvs,
    fit_piecewise_ideal_psd_calibration_from_csvs,
    save_ideal_psd_calibration,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit a chart-specific dead-leaves ideal PSD model")
    parser.add_argument("csv_root", type=Path, help="Root directory containing Imatest Random CSV files")
    parser.add_argument("output_json", type=Path, help="Where to write the fitted calibration JSON")
    parser.add_argument("--glob", default="**/*_R_Random.csv")
    parser.add_argument("--name", default="dead-leaves-calibration")
    parser.add_argument(
        "--mode",
        choices=["polynomial", "piecewise", "anchored_high_frequency"],
        default="polynomial",
    )
    parser.add_argument("--polynomial-degree", type=int, default=2)
    parser.add_argument("--split-cpp", type=float, default=0.24)
    parser.add_argument("--overlap-cpp", type=float, default=0.08)
    parser.add_argument("--low-degree", type=int, default=2)
    parser.add_argument("--high-degree", type=int, default=2)
    parser.add_argument("--stop-cpp", type=float, default=0.5)
    parser.add_argument("--residual-term-count", type=int, default=2)
    parser.add_argument("--regularization-lambda", type=float, default=0.02)
    parser.add_argument("--nyquist-relax-start-cpp", type=float, default=0.35)
    parser.add_argument("--nyquist-relax-end-weight", type=float, default=0.5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    csv_paths = sorted(args.csv_root.glob(args.glob))
    if args.mode == "piecewise":
        calibration = fit_piecewise_ideal_psd_calibration_from_csvs(
            csv_paths,
            name=args.name,
            split_cpp=args.split_cpp,
            overlap_cpp=args.overlap_cpp,
            low_degree=args.low_degree,
            high_degree=args.high_degree,
        )
    elif args.mode == "anchored_high_frequency":
        calibration = fit_anchored_high_frequency_ideal_psd_calibration_from_csvs(
            csv_paths,
            name=args.name,
            split_cpp=args.split_cpp,
            stop_cpp=args.stop_cpp,
            residual_term_count=args.residual_term_count,
            regularization_lambda=args.regularization_lambda,
            nyquist_relax_start_cpp=args.nyquist_relax_start_cpp,
            nyquist_relax_end_weight=args.nyquist_relax_end_weight,
        )
    else:
        calibration = fit_ideal_psd_calibration_from_csvs(
            csv_paths,
            name=args.name,
            polynomial_degree=args.polynomial_degree,
        )
    save_ideal_psd_calibration(args.output_json, calibration)
    print(f"Wrote {args.output_json} from {calibration.source_count} CSV files")
    if calibration.is_piecewise:
        print("Mode: piecewise")
        print(f"Blend width: {calibration.blend_width_cpp}")
        for idx, segment in enumerate(calibration.piecewise_segments, start=1):
            print(
                f"Segment {idx}: [{segment.start_cpp}, {segment.stop_cpp}] "
                f"degree={segment.polynomial_degree} coeffs={segment.log_frequency_polynomial_coefficients}"
            )
    elif calibration.has_anchored_high_frequency_correction:
        correction = calibration.anchored_high_frequency_correction
        assert correction is not None
        print("Mode: anchored_high_frequency")
        print(f"Base coeffs: {calibration.log_frequency_polynomial_coefficients}")
        print(
            "Correction: "
            f"start={correction.start_cpp} stop={correction.stop_cpp} "
            f"terms={correction.term_count} "
            f"lambda={correction.regularization_lambda} "
            f"coeffs={correction.log_frequency_residual_coefficients}"
        )
    else:
        print(f"Mode: polynomial degree={calibration.polynomial_degree}")
        print(f"Coefficients: {calibration.log_frequency_polynomial_coefficients}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
