from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    ideal_dead_leaves_psd,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)

BANDS = (
    ("low", 0.01, 0.08),
    ("mid", 0.08, 0.2),
    ("high", 0.2, 0.35),
    ("top", 0.35, 0.5),
)

SHAPE_SAMPLE_INDICES = (2, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 63)

METRIC_NAMES = (
    "mtf",
    "signal_psd",
    "noise_psd",
    "signal_plus_noise_psd",
)

SHAPE_NAMES = (
    "mtf_shape_delta",
    "signal_shape_delta",
    "ideal_shape_delta",
    "ratio_shape_delta",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze dead-leaves MTF / PSD residuals against Imatest CSVs")
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
    return parser


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
        "metric_rows": {name: [] for name in METRIC_NAMES},
        "shape_rows": {name: [] for name in SHAPE_NAMES},
    }


def append_summary(
    accumulator: dict[str, object],
    *,
    band_payloads: dict[str, dict[str, dict[str, float]]],
    shape_payloads: dict[str, np.ndarray],
) -> None:
    accumulator["count"] = int(accumulator["count"]) + 1
    metric_rows = accumulator["metric_rows"]
    shape_rows = accumulator["shape_rows"]
    assert isinstance(metric_rows, dict)
    assert isinstance(shape_rows, dict)
    for name, payload in band_payloads.items():
        metric_rows[name].append(payload)
    for name, payload in shape_payloads.items():
        shape_rows[name].append(payload)


def summarize_accumulator(accumulator: dict[str, object]) -> dict[str, object]:
    metric_rows = accumulator["metric_rows"]
    shape_rows = accumulator["shape_rows"]
    assert isinstance(metric_rows, dict)
    assert isinstance(shape_rows, dict)
    payload = {
        "count": int(accumulator["count"]),
        "bands": {
            name: summarize_band_collection(rows)
            for name, rows in metric_rows.items()
            if rows
        },
        "shape_samples": {},
    }
    for name, rows in shape_rows.items():
        if not rows:
            continue
        mean_delta = np.mean(np.stack(rows, axis=0), axis=0)
        payload["shape_samples"][name] = {
            f"{IMATEST_REFERENCE_BINS[idx]:.4f}": float(mean_delta[idx])
            for idx in SHAPE_SAMPLE_INDICES
            if idx < len(mean_delta)
        }
    return payload


def band_error_summary(
    frequencies: np.ndarray,
    estimate: np.ndarray,
    reference: np.ndarray,
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for label, lo, hi in BANDS:
        band = (frequencies >= lo) & (frequencies < hi)
        if not np.any(band):
            continue
        est = np.asarray(estimate[band], dtype=np.float64)
        ref = np.asarray(reference[band], dtype=np.float64)
        abs_err = np.abs(est - ref)
        rel_err = abs_err / np.maximum(np.abs(ref), 1e-12)
        signed_rel = (est - ref) / np.maximum(np.abs(ref), 1e-12)
        log_abs_err = np.abs(
            np.log(np.maximum(est, 1e-12)) - np.log(np.maximum(ref, 1e-12))
        )
        summary[label] = {
            "mae": float(np.mean(abs_err)),
            "mre": float(np.mean(rel_err)),
            "signed_rel": float(np.mean(signed_rel)),
            "log_mae": float(np.mean(log_abs_err)),
        }
    return summary


def normalize_shape(frequencies: np.ndarray, values: np.ndarray) -> np.ndarray:
    band = (frequencies >= 0.0177) & (frequencies <= 0.0335)
    if np.any(band):
        base = float(np.mean(values[band]))
    else:
        base = float(np.mean(values[: min(4, values.size)]))
    return np.log(np.maximum(values / max(base, 1e-12), 1e-12))


def summarize_band_collection(
    items: list[dict[str, dict[str, float]]],
) -> dict[str, dict[str, float]]:
    payload: dict[str, dict[str, float]] = {}
    for label, _, _ in BANDS:
        maes = [row[label]["mae"] for row in items]
        mres = [row[label]["mre"] for row in items]
        signed = [row[label]["signed_rel"] for row in items]
        log_maes = [row[label]["log_mae"] for row in items]
        payload[label] = {
            "mae_mean": float(np.mean(maes)),
            "mre_mean": float(np.mean(mres)),
            "signed_rel_mean": float(np.mean(signed)),
            "log_mae_mean": float(np.mean(log_maes)),
        }
    return payload


def main() -> int:
    args = build_parser().parse_args()
    calibration = load_ideal_psd_calibration(args.calibration_file)
    csv_paths = sorted(args.dataset_root.glob("**/Results/*_R_Random.csv"))

    overall = make_accumulator()
    by_source: dict[str, dict[str, object]] = {}
    by_variant: dict[str, dict[str, object]] = {}
    by_group: dict[str, dict[str, object]] = {}

    for csv_path in csv_paths:
        raw_path = csv_path.parent.parent / csv_path.name.replace("_R_Random.csv", ".raw")
        if not raw_path.exists():
            continue

        reference = parse_imatest_random_csv(csv_path)
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
        )

        n = min(len(estimate.frequencies_cpp), len(reference.frequencies_cpp))
        frequencies = reference.frequencies_cpp[:n]
        estimate_ideal = ideal_dead_leaves_psd(
            estimate.frequencies_cpp[:n],
            length_px=max(roi.width, roi.height),
            mode="calibrated_log",
            calibration=calibration,
        )
        reference_ideal = reference.signal_psd[:n] / np.maximum(reference.mtf[:n] ** 2, 1e-12)

        band_payloads = {
            "mtf": band_error_summary(frequencies, estimate.mtf[:n], reference.mtf[:n]),
            "signal_psd": band_error_summary(
                frequencies, estimate.psd_signal[:n], reference.signal_psd[:n]
            ),
            "noise_psd": band_error_summary(
                frequencies, estimate.psd_noise[:n], reference.noise_psd[:n]
            ),
            "signal_plus_noise_psd": band_error_summary(
                frequencies,
                estimate.psd_signal_plus_noise[:n],
                reference.signal_plus_noise_psd[:n],
            ),
        }

        shape_payloads = {
            "mtf_shape_delta": normalize_shape(frequencies, estimate.mtf[:n])
            - normalize_shape(frequencies, reference.mtf[:n]),
            "signal_shape_delta": normalize_shape(frequencies, estimate.psd_signal[:n])
            - normalize_shape(frequencies, reference.signal_psd[:n]),
            "ideal_shape_delta": normalize_shape(frequencies, estimate_ideal)
            - normalize_shape(frequencies, reference_ideal),
            "ratio_shape_delta": normalize_shape(
                frequencies,
                estimate.psd_signal[:n] / np.maximum(estimate_ideal, 1e-12),
            )
            - normalize_shape(
                frequencies,
                reference.signal_psd[:n] / np.maximum(reference_ideal, 1e-12),
            ),
        }

        labels = classify_csv(csv_path, args.dataset_root)
        append_summary(overall, band_payloads=band_payloads, shape_payloads=shape_payloads)
        append_summary(
            by_source.setdefault(labels["source"], make_accumulator()),
            band_payloads=band_payloads,
            shape_payloads=shape_payloads,
        )
        append_summary(
            by_variant.setdefault(labels["variant"], make_accumulator()),
            band_payloads=band_payloads,
            shape_payloads=shape_payloads,
        )
        append_summary(
            by_group.setdefault(labels["group"], make_accumulator()),
            band_payloads=band_payloads,
            shape_payloads=shape_payloads,
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
