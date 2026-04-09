from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys

import numpy as np

RELEASE_ROOT = Path(__file__).resolve().parents[1]
if str(RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(RELEASE_ROOT))

from algo.dead_leaves import (
    AcutancePreset,
    BayerMode,
    BayerPattern,
    DEFAULT_ACUTANCE_PRESETS,
    IMATEST_REFERENCE_BINS,
    RoiBounds,
    acutance_curve_from_mtf,
    acutance_presets_from_mtf,
    apply_frequency_scale,
    apply_mtf_compensation,
    apply_mtf_shape_correction,
    compute_mtf_metrics,
    estimate_dead_leaves_mtf,
    estimate_texture_support_scale,
    extract_analysis_plane,
    load_ideal_psd_calibration,
    load_raw_u16,
    normalize_for_analysis,
    quality_loss_presets_from_acutance,
    detect_texture_roi,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run release dead-leaves batch analysis")
    parser.add_argument(
        "--profile",
        type=Path,
        default=Path("config/parity_fit_profile.release.json"),
        help="Release profile JSON path, relative to release root by default.",
    )
    parser.add_argument(
        "--release-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Release root directory.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        help="Override dataset root. Defaults to profile.dataset_root under release root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Override result root. Defaults to profile.result_root under release root.",
    )
    return parser


def resolve_path(root: Path, value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _fmt(value: float, places: int) -> str:
    return f"{float(value):.{places}f}"


def _color_channel_label(bayer_mode: str) -> str:
    if bayer_mode in {BayerMode.DEMOSAIC_RED.value, BayerMode.RAW_RED_UPSAMPLED.value}:
        return "R"
    return "Gray"


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


def analyze_one(
    release_root: Path,
    profile: dict[str, object],
    raw_path: Path,
) -> dict[str, object]:
    shared = profile["shared"]
    mtf_profile = profile["mtf_profile"]
    acutance_profile = profile["acutance_profile"]
    report = profile.get("report", {})
    analysis_gamma = float(shared.get("analysis_gamma", shared["gamma"]))
    linearization_mode = str(shared.get("linearization_mode", "power"))
    linearization_toe = float(shared.get("linearization_toe", 0.0))
    report_gamma = float(report.get("gamma", shared["gamma"]))
    report_color_channel = str(
        report.get("color_channel", _color_channel_label(str(shared["bayer_mode"])))
    )
    acutance_presets = build_acutance_presets(acutance_profile.get("preset_overrides"))

    raw = load_raw_u16(raw_path, int(shared["width"]), int(shared["height"]))
    plane = extract_analysis_plane(
        raw,
        bayer_pattern=BayerPattern(str(shared["bayer_pattern"])),
        mode=BayerMode(str(shared["bayer_mode"])),
    )
    image = normalize_for_analysis(
        plane,
        gamma=analysis_gamma,
        mode=linearization_mode,
        toe=linearization_toe,
    )

    detected = detect_texture_roi(image)
    roi = RoiBounds.centered(
        center_x=(detected.left + detected.right) // 2,
        center_y=(detected.top + detected.bottom) // 2,
        width=int(shared["roi_width"]),
        height=int(shared["roi_height"]),
        image_width=image.shape[1],
        image_height=image.shape[0],
    )

    calibration = load_ideal_psd_calibration(resolve_path(release_root, shared["calibration_file"]))
    result = estimate_dead_leaves_mtf(
        image,
        num_bins=len(IMATEST_REFERENCE_BINS) if bool(shared.get("reference_bins")) else 64,
        ideal_psd_mode=str(shared["ideal_psd_mode"]),
        ideal_psd_calibration=calibration,
        bin_centers=IMATEST_REFERENCE_BINS.copy() if bool(shared.get("reference_bins")) else None,
        roi_override=roi,
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
            float(v) for v in acutance_profile["acutance_noise_share_scale_coefficients"]
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
        crop = image[result.roi.top : result.roi.bottom + 1, result.roi.left : result.roi.right + 1]
        texture_support = estimate_texture_support_scale(crop, percentile=45.0)
        effective_frequency_scale *= texture_support.frequency_scale

    scaled_frequencies = apply_frequency_scale(result.frequencies_cpp, scale=effective_frequency_scale)

    corrected_mtf, _ = apply_mtf_shape_correction(
        apply_mtf_compensation(
            result.mtf,
            scaled_frequencies,
            mode=str(shared.get("mtf_compensation_mode", "none")),
            sensor_fill_factor=float(shared.get("sensor_fill_factor", 1.0)),
            denominator_clip=float(shared.get("compensation_denominator_clip", 0.25)),
            max_gain=float(shared.get("compensation_max_gain", 3.0)),
        )[0],
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
    corrected_mtf_with_noise, _ = apply_mtf_shape_correction(
        apply_mtf_compensation(
            result.mtf_with_noise,
            scaled_frequencies,
            mode=str(shared.get("mtf_compensation_mode", "none")),
            sensor_fill_factor=float(shared.get("sensor_fill_factor", 1.0)),
            denominator_clip=float(shared.get("compensation_denominator_clip", 0.25)),
            max_gain=float(shared.get("compensation_max_gain", 3.0)),
        )[0],
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
    corrected_mtf_for_acutance, _ = apply_mtf_shape_correction(
        apply_mtf_compensation(
            result.mtf_for_acutance,
            scaled_frequencies,
            mode=str(shared.get("mtf_compensation_mode", "none")),
            sensor_fill_factor=float(shared.get("sensor_fill_factor", 1.0)),
            denominator_clip=float(shared.get("compensation_denominator_clip", 0.25)),
            max_gain=float(shared.get("compensation_max_gain", 3.0)),
        )[0],
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

    metrics = compute_mtf_metrics(
        scaled_frequencies,
        corrected_mtf,
        smoothing_window=int(mtf_profile["readout_smoothing_window"]),
        interpolation_mode=str(mtf_profile["readout_interpolation"]),
    )
    acutance_curve = acutance_curve_from_mtf(
        scaled_frequencies,
        corrected_mtf_for_acutance,
        picture_height_cm=40.0,
        viewing_distances_cm=np.arange(1.0, 101.0, 1.0),
        pixels_along_picture_height=result.roi.height,
    )
    acutance_presets_result = acutance_presets_from_mtf(
        scaled_frequencies,
        corrected_mtf_for_acutance,
        pixels_along_picture_height=result.roi.height,
        presets=acutance_presets,
    )
    quality_loss_presets = quality_loss_presets_from_acutance(acutance_presets_result)

    return {
        "raw_path": raw_path,
        "roi": result.roi,
        "scaled_frequencies": scaled_frequencies,
        "mtf": corrected_mtf,
        "mtf_with_noise": corrected_mtf_with_noise,
        "noise_psd": result.psd_noise,
        "signal_plus_noise_psd": result.psd_signal_plus_noise,
        "signal_psd": result.psd_signal,
        "metrics": metrics,
        "acutance_curve": acutance_curve,
        "acutance_presets": acutance_presets_result,
        "quality_loss_presets": quality_loss_presets,
        "analysis_gamma": analysis_gamma,
        "linearization_mode": linearization_mode,
        "linearization_toe": linearization_toe,
        "report_gamma": report_gamma,
        "color_channel": report_color_channel,
        "max_detected_frequency_cpp": float(np.max(scaled_frequencies)),
        "effective_frequency_scale": effective_frequency_scale,
        "texture_support": texture_support,
    }


def write_imatest_style_csv(output_path: Path, analysis: dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    roi = analysis["roi"]
    metrics = analysis["metrics"]
    frequencies = analysis["scaled_frequencies"]
    mtf = analysis["mtf"]
    mtf_with_noise = analysis["mtf_with_noise"]
    noise_psd = analysis["noise_psd"]
    signal_plus_noise_psd = analysis["signal_plus_noise_psd"]
    signal_psd = analysis["signal_psd"]
    acutance_curve = analysis["acutance_curve"]
    acutance_presets = analysis["acutance_presets"]
    quality_loss_presets = analysis["quality_loss_presets"]

    rows: list[list[str]] = []
    rows.append(["Imatest-style", "Python Release", "", "Random"])
    rows.append(["File", analysis["raw_path"].name])
    rows.append(["Run date", datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "", "Release"])
    rows.append([])
    rows.append(["Image pixels (WxH)", "4032", "3024"])
    rows.append(["Crop", str(roi.height), str(roi.width)])
    rows.append(["L R T B", str(roi.left), str(roi.right), str(roi.top), str(roi.bottom)])
    rows.append(["pixels/in", "0"])
    rows.append(["pixels/mm", "0"])
    rows.append(["um/pixel", "0"])
    rows.append(["MTF30", f"{metrics.mtf30:.3f} Cy/Pxl", "Secondary readout"])
    rows.append([])
    rows.append(["Table of MTF"])
    rows.append(["f (c/p)", "f (C/P)", "MTF", "MTF w/noise", "Noise PSD", "S+N PSD", "Signal PSD", "", "Seg 1"])
    for idx in range(len(frequencies)):
        rows.append([
            _fmt(frequencies[idx], 4),
            _fmt(frequencies[idx], 4),
            _fmt(mtf[idx], 4),
            _fmt(mtf_with_noise[idx], 4),
            _fmt(noise_psd[idx], 7),
            _fmt(signal_plus_noise_psd[idx], 7),
            _fmt(signal_psd[idx], 7),
            "",
            _fmt(mtf[idx], 4),
        ])
    rows.append([])
    rows.append(["MTFnn C/P", "Mean", " Seg 1", ""])
    rows.append(["MTF70 C/P", _fmt(metrics.mtf70, 4), _fmt(metrics.mtf70, 4), ""])
    rows.append(["MTF50 C/P", _fmt(metrics.mtf50, 4), _fmt(metrics.mtf50, 4), ""])
    rows.append(["MTF30 C/P", _fmt(metrics.mtf30, 4), _fmt(metrics.mtf30, 4), ""])
    rows.append(["MTF20 C/P", _fmt(metrics.mtf20, 4), _fmt(metrics.mtf20, 4), ""])
    rows.append(["MTF10 C/P", _fmt(metrics.mtf10, 4), _fmt(metrics.mtf10, 4), ""])
    rows.append(["MTFnnP C/P", "Mean", " Seg 1", ""])
    rows.append(["MTF70P C/P", _fmt(metrics.mtf70, 4), _fmt(metrics.mtf70, 4), ""])
    rows.append(["MTF50P C/P", _fmt(metrics.mtf50, 4), _fmt(metrics.mtf50, 4), ""])
    rows.append(["MTF30P C/P", _fmt(metrics.mtf30, 4), _fmt(metrics.mtf30, 4), ""])
    rows.append(["MTF20P C/P", _fmt(metrics.mtf20, 4), _fmt(metrics.mtf20, 4), ""])
    rows.append(["MTF10P C/P", _fmt(metrics.mtf10, 4), _fmt(metrics.mtf10, 4), ""])
    rows.append(["Undersharpening %", _fmt(metrics.undersharpening_pct, 3)])
    rows.append([])
    rows.append(["Acutance (CPIQ)", "Region", "1 of 1"])
    rows.append(["Print height ", "Viewing dist (cm)", "Acutance"])
    for point in acutance_curve:
        rows.append([
            f"{point.print_height_cm:.0f}",
            _fmt(point.viewing_distance_cm, 2),
            _fmt(point.acutance, 2),
        ])
    rows.append(["Use unnormalized MTF for Acutance calculation"])
    rows.append(["CPIQ Results"])
    preset_order = [
        "Computer Monitor Acutance",
        '5.5" Phone Display Acutance',
        "UHDTV Display Acutance",
        "Small Print Acutance",
        "Large Print Acutance",
    ]
    for key in preset_order:
        rows.append([key, _fmt(acutance_presets[key], 3), ""])
        ql_key = key.replace("Acutance", "Quality Loss")
        rows.append([ql_key, _fmt(quality_loss_presets[ql_key], 3), ""])
    rows.append(["Gamma", _fmt(analysis["report_gamma"], 3)])
    rows.append(["Color channel", analysis["color_channel"]])
    rows.append(["Max detected f (c/p)", _fmt(analysis["max_detected_frequency_cpp"], 3)])
    rows.append([])
    rows.append(["Exif data"])

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    release_root = args.release_root.resolve()
    profile_path = resolve_path(release_root, args.profile)
    if profile_path is None or not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {args.profile}")

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    dataset_root = resolve_path(release_root, args.dataset_root or profile["dataset_root"])
    output_root = resolve_path(release_root, args.output_root or profile["result_root"])
    assert dataset_root is not None
    assert output_root is not None
    output_root.mkdir(parents=True, exist_ok=True)

    raw_paths = sorted(dataset_root.rglob("*.raw"))
    summary: dict[str, object] = {
        "profile": str(profile_path),
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "count_total": 0,
        "generated_files": [],
        "profile_name": profile.get("name"),
    }

    for raw_path in raw_paths:
        relative_raw = raw_path.relative_to(dataset_root)
        result_path = output_root / relative_raw.parent / "Results" / f"{raw_path.stem}_R_Random.csv"
        analysis = analyze_one(release_root, profile, raw_path)
        write_imatest_style_csv(result_path, analysis)

        summary["count_total"] = int(summary["count_total"]) + 1
        generated_files = summary["generated_files"]
        assert isinstance(generated_files, list)
        generated_files.append(str(result_path.relative_to(release_root)))

    summary_path = output_root / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
