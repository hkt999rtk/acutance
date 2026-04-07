from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .dead_leaves import (
    IMATEST_REFERENCE_BINS,
    AcutancePreset,
    DEFAULT_ACUTANCE_PRESETS,
    RoiBounds,
    acutance_presets_from_mtf,
    compare_acutance_presets,
    detect_texture_roi,
    estimate_dead_leaves_mtf,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep print display-MTF Gaussian cutoff")
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--roi-width", type=int, default=1655)
    parser.add_argument("--roi-height", type=int, default=1673)
    parser.add_argument("--small-print-c50-values", type=float, nargs="+", default=[9999.0, 48.0, 32.0, 24.0, 20.0, 16.0])
    parser.add_argument("--large-print-c50-values", type=float, nargs="+", default=[9999.0, 48.0, 32.0, 24.0, 20.0, 16.0])
    parser.add_argument("--high-frequency-guard-start-cpp", type=float, default=0.36)
    parser.add_argument("--high-frequency-guard-stop-cpp", type=float, default=0.5)
    return parser


def with_print_c50s(small_print_c50: float | None, large_print_c50: float | None) -> tuple[AcutancePreset, ...]:
    presets = []
    for preset in DEFAULT_ACUTANCE_PRESETS:
        if preset.name == "Small Print Acutance":
            presets.append(
                AcutancePreset(
                    name=preset.name,
                    picture_height_cm=preset.picture_height_cm,
                    viewing_distance_cm=preset.viewing_distance_cm,
                    display_mtf_c50_cpd=small_print_c50,
                )
            )
        elif preset.name == "Large Print Acutance":
            presets.append(
                AcutancePreset(
                    name=preset.name,
                    picture_height_cm=preset.picture_height_cm,
                    viewing_distance_cm=preset.viewing_distance_cm,
                    display_mtf_c50_cpd=large_print_c50,
                )
            )
        else:
            presets.append(preset)
    return tuple(presets)


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

    payload = {}
    for small_c50 in args.small_print_c50_values:
        for large_c50 in args.large_print_c50_values:
            presets = with_print_c50s(
                None if small_c50 >= 9999.0 else float(small_c50),
                None if large_c50 >= 9999.0 else float(large_c50),
            )
            preset_errors = []
            by_name: dict[str, list[float]] = {}
            for estimate, reference in samples:
                result = acutance_presets_from_mtf(
                    estimate.frequencies_cpp,
                    estimate.mtf_for_acutance,
                    pixels_along_picture_height=estimate.roi.height,
                    presets=presets,
                )
                compared = compare_acutance_presets(result, reference.reported_acutance)
                for name, values in compared.items():
                    error = float(values["abs_error"])
                    preset_errors.append(error)
                    by_name.setdefault(name, []).append(error)

            key = f"small={small_c50:g},large={large_c50:g}"
            payload[key] = {
                "preset_mae_mean": float(np.mean(preset_errors)),
                "small_print_mae": float(np.mean(by_name["Small Print Acutance"])),
                "large_print_mae": float(np.mean(by_name["Large Print Acutance"])),
                "monitor_mae": float(np.mean(by_name["Computer Monitor Acutance"])),
                "phone_mae": float(np.mean(by_name['5.5" Phone Display Acutance'])),
                "uhdtv_mae": float(np.mean(by_name["UHDTV Display Acutance"])),
            }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
