from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

import numpy as np

from .dead_leaves import (
    AcutancePreset,
    BayerMode,
    BayerPattern,
    DEFAULT_ACUTANCE_PRESETS,
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    acutance_presets_from_mtf,
    apply_frequency_scale,
    apply_mtf_shape_correction,
    estimate_dead_leaves_mtf,
    estimate_texture_support_scale,
    extract_analysis_plane,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    parse_imatest_random_csv,
)

FOCUS_PRESETS = (
    "Computer Monitor Acutance",
    '5.5" Phone Display Acutance',
    "UHDTV Display Acutance",
    "Small Print Acutance",
    "Large Print Acutance",
)

GAIN_PATTERN = re.compile(r"_AG([0-9.]+)_")
MIXUP_PATTERN = re.compile(r"_ppqpkl_([0-9.]+)$")


@dataclass(frozen=True)
class GainTrendPoint:
    gain: float
    reported: float
    predicted: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark A-model Acutance gain-trend mismatch against release profiles."
    )
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("profiles", nargs="+", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--flat-epsilon", type=float, default=0.002)
    parser.add_argument("--output", type=Path)
    return parser


def parse_gain_value(path: str | Path) -> float:
    name = Path(path).name
    match = GAIN_PATTERN.search(name)
    if match is None:
        raise ValueError(f"Could not parse gain from path: {path}")
    return float(match.group(1))


def parse_mixup_group(path: Path) -> str:
    match = MIXUP_PATTERN.search(path.parent.parent.name)
    if match is None:
        return "unknown"
    return match.group(1)


def classify_direction(delta: float, *, flat_epsilon: float) -> str:
    if delta > flat_epsilon:
        return "up"
    if delta < -flat_epsilon:
        return "down"
    return "flat"


def build_acutance_presets(
    overrides: dict[str, dict[str, float | str | None]] | None = None,
) -> tuple[AcutancePreset, ...]:
    presets: list[AcutancePreset] = []
    override_map = overrides or {}
    for preset in DEFAULT_ACUTANCE_PRESETS:
        override = override_map.get(preset.name, {})
        display_mtf_c50_cpd = override.get("display_mtf_c50_cpd", preset.display_mtf_c50_cpd)
        presets.append(
            AcutancePreset(
                name=preset.name,
                picture_height_cm=float(override.get("picture_height_cm", preset.picture_height_cm)),
                viewing_distance_cm=float(
                    override.get("viewing_distance_cm", preset.viewing_distance_cm)
                ),
                display_mtf_c50_cpd=(
                    None if display_mtf_c50_cpd is None else float(display_mtf_c50_cpd)
                ),
                display_mtf_model=str(override.get("display_mtf_model", preset.display_mtf_model)),
            )
        )
    return tuple(presets)


def resolve_release_path(profile_path: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    release_root = profile_path.parents[1]
    return (release_root / path).resolve()


def analyze_profile(
    *,
    dataset_root: Path,
    profile_path: Path,
    width: int,
    height: int,
    flat_epsilon: float,
) -> dict[str, object]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    shared = profile["shared"]
    mtf_profile = profile["mtf_profile"]
    acutance_profile = profile["acutance_profile"]
    analysis_gamma = float(shared.get("analysis_gamma", shared["gamma"]))
    presets = build_acutance_presets(acutance_profile.get("preset_overrides"))
    calibration = load_ideal_psd_calibration(
        resolve_release_path(profile_path, shared["calibration_file"])
    )

    by_preset: dict[str, dict[str, list[GainTrendPoint]]] = {
        preset: {} for preset in FOCUS_PRESETS
    }

    for csv_path in sorted(dataset_root.glob("**/Results/*_R_Random.csv")):
        raw_path = csv_path.parent.parent / csv_path.name.replace("_R_Random.csv", ".raw")
        if not raw_path.exists():
            continue

        reference = parse_imatest_random_csv(csv_path)
        raw = load_raw_u16(raw_path, width, height)
        plane = extract_analysis_plane(
            raw,
            bayer_pattern=BayerPattern(str(shared["bayer_pattern"])),
            mode=BayerMode(str(shared["bayer_mode"])),
        )
        image = normalize_for_analysis(plane, gamma=analysis_gamma)

        center_x, center_y = extract_texture_center(image)
        detected = RoiBounds.centered(
            center_x=center_x,
            center_y=center_y,
            width=int(shared["roi_width"]),
            height=int(shared["roi_height"]),
            image_width=image.shape[1],
            image_height=image.shape[0],
        )
        result = estimate_dead_leaves_mtf(
            image,
            num_bins=len(IMATEST_REFERENCE_BINS) if bool(shared.get("reference_bins")) else 64,
            ideal_psd_mode=str(shared["ideal_psd_mode"]),
            ideal_psd_calibration=calibration,
            bin_centers=IMATEST_REFERENCE_BINS.copy() if bool(shared.get("reference_bins")) else None,
            roi_override=detected,
            normalization_band=(
                float(mtf_profile["normalization_band_lo"]),
                float(mtf_profile["normalization_band_hi"]),
            ),
            normalization_mode=str(mtf_profile["normalization_mode"]),
            acutance_reference_band=(
                float(acutance_profile["acutance_band_lo"]),
                float(acutance_profile["acutance_band_hi"]),
            ),
            acutance_reference_mode=str(acutance_profile["acutance_band_mode"]),
            noise_psd_model=str(mtf_profile["noise_psd_model"]),
            noise_psd_scale=float(mtf_profile["noise_psd_scale"]),
            acutance_noise_scale_model=str(acutance_profile["acutance_noise_scale_mode"]),
            acutance_noise_share_band=(
                float(acutance_profile["acutance_noise_share_band_lo"]),
                float(acutance_profile["acutance_noise_share_band_hi"]),
            ),
            acutance_noise_share_scale_coefficients=tuple(
                float(value) for value in acutance_profile["acutance_noise_share_scale_coefficients"]
            ),
            high_frequency_guard_start_cpp=(
                None
                if acutance_profile.get("high_frequency_guard_start_cpp") is None
                else float(acutance_profile["high_frequency_guard_start_cpp"])
            ),
            high_frequency_guard_stop_cpp=float(acutance_profile["high_frequency_guard_stop_cpp"]),
        )

        effective_frequency_scale = float(shared.get("frequency_scale", 1.0))
        texture_support = None
        if bool(shared.get("texture_support_scale")):
            crop = image[
                result.roi.top : result.roi.bottom + 1,
                result.roi.left : result.roi.right + 1,
            ]
            texture_support = estimate_texture_support_scale(crop, percentile=45.0)
            effective_frequency_scale *= texture_support.frequency_scale

        scaled_frequencies = apply_frequency_scale(
            result.frequencies_cpp,
            scale=effective_frequency_scale,
        )
        corrected_mtf_for_acutance, _ = apply_mtf_shape_correction(
            result.mtf_for_acutance,
            scaled_frequencies,
            mode=str(acutance_profile["mtf_shape_correction_mode"]),
            high_frequency_noise_share=result.acutance_high_frequency_noise_share,
            gain=float(acutance_profile["mtf_shape_correction_gain"]),
            share_gate_lo=float(acutance_profile["mtf_shape_correction_share_gate_lo"]),
            share_gate_hi=float(acutance_profile["mtf_shape_correction_share_gate_hi"]),
            mid_start_cpp=float(acutance_profile["mtf_shape_correction_mid_start_cpp"]),
            mid_peak_cpp=float(acutance_profile["mtf_shape_correction_mid_peak_cpp"]),
            mid_stop_cpp=float(acutance_profile["mtf_shape_correction_mid_stop_cpp"]),
            high_start_cpp=float(acutance_profile["mtf_shape_correction_high_start_cpp"]),
            high_peak_cpp=float(acutance_profile["mtf_shape_correction_high_peak_cpp"]),
            high_stop_cpp=float(acutance_profile["mtf_shape_correction_high_stop_cpp"]),
            high_weight=float(acutance_profile["mtf_shape_correction_high_weight"]),
        )
        acutance = acutance_presets_from_mtf(
            scaled_frequencies,
            corrected_mtf_for_acutance,
            pixels_along_picture_height=result.roi.height,
            presets=presets,
        )

        gain = parse_gain_value(csv_path)
        mixup = parse_mixup_group(csv_path)
        for preset in FOCUS_PRESETS:
            by_preset[preset].setdefault(mixup, []).append(
                GainTrendPoint(
                    gain=gain,
                    reported=float(reference.reported_acutance[preset]),
                    predicted=float(acutance[preset]),
                )
            )

    preset_payload: dict[str, object] = {}
    focus_delta_maes: list[float] = []
    focus_series_maes: list[float] = []
    direction_match_count = 0
    direction_total = 0

    for preset, groups in by_preset.items():
        group_payloads = []
        delta_maes = []
        series_maes = []
        for mixup, points in sorted(groups.items(), key=lambda item: float(item[0])):
            ordered = sorted(points, key=lambda point: point.gain)
            reported_gain_delta = ordered[-1].reported - ordered[0].reported
            predicted_gain_delta = ordered[-1].predicted - ordered[0].predicted
            reported_direction = classify_direction(reported_gain_delta, flat_epsilon=flat_epsilon)
            predicted_direction = classify_direction(predicted_gain_delta, flat_epsilon=flat_epsilon)
            direction_match = reported_direction == predicted_direction
            direction_match_count += int(direction_match)
            direction_total += 1
            delta_mae = abs(predicted_gain_delta - reported_gain_delta)
            series_mae = float(
                np.mean([abs(point.predicted - point.reported) for point in ordered])
            )
            delta_maes.append(delta_mae)
            series_maes.append(series_mae)
            group_payloads.append(
                {
                    "mixup": mixup,
                    "gains": [point.gain for point in ordered],
                    "reported": [point.reported for point in ordered],
                    "predicted": [point.predicted for point in ordered],
                    "reported_gain_delta": reported_gain_delta,
                    "predicted_gain_delta": predicted_gain_delta,
                    "reported_direction": reported_direction,
                    "predicted_direction": predicted_direction,
                    "direction_match": direction_match,
                    "series_mae_mean": series_mae,
                }
            )
        delta_mae_mean = float(np.mean(delta_maes))
        series_mae_mean = float(np.mean(series_maes))
        focus_delta_maes.append(delta_mae_mean)
        focus_series_maes.append(series_mae_mean)
        preset_payload[preset] = {
            "reported_mean_gain_delta": float(
                np.mean([group["reported_gain_delta"] for group in group_payloads])
            ),
            "predicted_mean_gain_delta": float(
                np.mean([group["predicted_gain_delta"] for group in group_payloads])
            ),
            "gain_delta_mae_mean": delta_mae_mean,
            "series_mae_mean": series_mae_mean,
            "direction_match_count": int(
                sum(1 for group in group_payloads if group["direction_match"])
            ),
            "direction_group_count": len(group_payloads),
            "groups": group_payloads,
        }

    return {
        "profile_path": str(profile_path),
        "profile_name": profile.get("name"),
        "summary": {
            "focus_preset_gain_delta_mae_mean": float(np.mean(focus_delta_maes)),
            "focus_preset_series_mae_mean": float(np.mean(focus_series_maes)),
            "focus_preset_direction_match_count": direction_match_count,
            "focus_preset_direction_group_count": direction_total,
        },
        "presets": preset_payload,
    }


def extract_texture_center(image: np.ndarray) -> tuple[int, int]:
    from .dead_leaves import detect_texture_roi

    detected = detect_texture_roi(image)
    return ((detected.left + detected.right) // 2, (detected.top + detected.bottom) // 2)


def main() -> int:
    args = build_parser().parse_args()
    payload = {
        "dataset_root": str(args.dataset_root),
        "flat_epsilon": args.flat_epsilon,
        "profiles": [
            analyze_profile(
                dataset_root=args.dataset_root,
                profile_path=path,
                width=args.width,
                height=args.height,
                flat_epsilon=args.flat_epsilon,
            )
            for path in args.profiles
        ],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
