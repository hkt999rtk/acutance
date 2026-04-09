from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

import numpy as np

from .dead_leaves import AcutancePoint


EPS = 1e-12
CAPTURE_KEY_RE = re.compile(r"(OV13b10_AG[^_]+_ET[^_]+_deadleaf_12M_[^_]+)")


def capture_key_from_stem(stem: str) -> str:
    match = CAPTURE_KEY_RE.match(stem)
    if match:
        return match.group(1)
    if stem.endswith("_R_Random"):
        return stem[: -len("_R_Random")]
    return stem


def build_ori_reference_map(dataset_root: Path) -> dict[str, tuple[Path, Path]]:
    ori_root = dataset_root / "OV13B10_AI_NR_OV13B10_ori"
    mapping: dict[str, tuple[Path, Path]] = {}
    for csv_path in sorted((ori_root / "Results").glob("*_R_Random.csv")):
        key = capture_key_from_stem(csv_path.stem)
        raw_path = ori_root / f"{key}.raw"
        if raw_path.exists():
            mapping[key] = (csv_path, raw_path)
    return mapping


def derive_quantile_transfer_curve(
    source_image: np.ndarray,
    target_image: np.ndarray,
    *,
    quantiles: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    sample_quantiles = np.asarray(quantiles, dtype=np.float64)
    if sample_quantiles.ndim != 1 or sample_quantiles.size < 2:
        raise ValueError("quantiles must contain at least two samples")
    if np.any(sample_quantiles < 0.0) or np.any(sample_quantiles > 1.0):
        raise ValueError("quantiles must stay within [0, 1]")
    if np.any(np.diff(sample_quantiles) < 0.0):
        raise ValueError("quantiles must be sorted ascending")

    source_values = np.quantile(np.asarray(source_image, dtype=np.float64), sample_quantiles)
    target_values = np.quantile(np.asarray(target_image, dtype=np.float64), sample_quantiles)
    source_values = np.maximum.accumulate(np.clip(source_values, 0.0, 1.0))
    target_values = np.maximum.accumulate(np.clip(target_values, 0.0, 1.0))

    collapsed_source = [float(source_values[0])]
    collapsed_target = [float(target_values[0])]
    for source_value, target_value in zip(source_values[1:], target_values[1:]):
        if source_value <= collapsed_source[-1] + 1e-9:
            collapsed_target[-1] = max(collapsed_target[-1], float(target_value))
        else:
            collapsed_source.append(float(source_value))
            collapsed_target.append(float(target_value))

    if collapsed_source[0] > 0.0:
        collapsed_source.insert(0, 0.0)
        collapsed_target.insert(0, 0.0)
    else:
        collapsed_source[0] = 0.0
        collapsed_target[0] = 0.0
    if collapsed_source[-1] < 1.0:
        collapsed_source.append(1.0)
        collapsed_target.append(1.0)
    else:
        collapsed_source[-1] = 1.0
        collapsed_target[-1] = 1.0

    return (
        np.asarray(collapsed_source, dtype=np.float64),
        np.asarray(collapsed_target, dtype=np.float64),
    )


def apply_quantile_transfer_curve(
    image: np.ndarray,
    source_values: np.ndarray,
    target_values: np.ndarray,
    *,
    strength: float = 1.0,
) -> np.ndarray:
    base = np.asarray(image, dtype=np.float64)
    mapped = np.interp(
        base,
        np.asarray(source_values, dtype=np.float64),
        np.asarray(target_values, dtype=np.float64),
        left=float(target_values[0]),
        right=float(target_values[-1]),
    )
    if strength != 1.0:
        mapped = base + (mapped - base) * float(strength)
    return np.clip(mapped, 0.0, 1.0)


def derive_reference_correction_curve(
    reference_frequencies: np.ndarray,
    reference_mtf: np.ndarray,
    estimate_frequencies: np.ndarray,
    estimate_mtf: np.ndarray,
    *,
    clip_lo: float,
    clip_hi: float,
) -> np.ndarray:
    ref_f = np.asarray(reference_frequencies, dtype=np.float64)
    ref = np.asarray(reference_mtf, dtype=np.float64)
    est_f = np.asarray(estimate_frequencies, dtype=np.float64)
    est = np.asarray(estimate_mtf, dtype=np.float64)
    estimate_on_reference = np.interp(
        ref_f,
        est_f,
        est,
        left=float(est[0]),
        right=float(est[-1]),
    )
    correction = ref / np.maximum(estimate_on_reference, EPS)
    return np.clip(correction, clip_lo, clip_hi)


def apply_reference_correction_curve(
    frequencies: np.ndarray,
    mtf: np.ndarray,
    correction_frequencies: np.ndarray,
    correction_curve: np.ndarray,
    *,
    strength: float = 1.0,
    blend_start_cpp: float = 0.0,
    blend_stop_cpp: float = 0.0,
    strength_low: float | None = None,
    strength_high: float | None = None,
    strength_ramp_start_cpp: float = 0.0,
    strength_ramp_stop_cpp: float = 0.0,
    strength_curve_frequencies: Sequence[float] | None = None,
    strength_curve_values: Sequence[float] | None = None,
    correction_delta_power: float = 1.0,
    correction_delta_power_positions: Sequence[float] | None = None,
    correction_delta_power_values: Sequence[float] | None = None,
) -> np.ndarray:
    sample_frequencies = np.asarray(frequencies, dtype=np.float64)
    correction = np.interp(
        sample_frequencies,
        np.asarray(correction_frequencies, dtype=np.float64),
        np.asarray(correction_curve, dtype=np.float64),
        left=float(correction_curve[0]),
        right=float(correction_curve[-1]),
    )
    if blend_stop_cpp <= 0.0 and blend_start_cpp <= 0.0:
        blend = np.ones_like(sample_frequencies)
    elif blend_stop_cpp <= blend_start_cpp:
        blend = (sample_frequencies >= blend_start_cpp).astype(np.float64)
    else:
        blend = np.clip(
            (sample_frequencies - blend_start_cpp) / (blend_stop_cpp - blend_start_cpp),
            0.0,
            1.0,
        )
    if strength_curve_frequencies and strength_curve_values:
        strength_curve = np.interp(
            sample_frequencies,
            np.asarray(strength_curve_frequencies, dtype=np.float64),
            np.asarray(strength_curve_values, dtype=np.float64),
            left=float(strength_curve_values[0]),
            right=float(strength_curve_values[-1]),
        )
    elif strength_low is None and strength_high is None:
        strength_curve = np.full_like(sample_frequencies, float(strength))
    else:
        lo = float(strength if strength_low is None else strength_low)
        hi = float(strength if strength_high is None else strength_high)
        if strength_ramp_stop_cpp <= strength_ramp_start_cpp:
            strength_mix = (sample_frequencies >= strength_ramp_start_cpp).astype(np.float64)
        else:
            strength_mix = np.clip(
                (sample_frequencies - strength_ramp_start_cpp)
                / (strength_ramp_stop_cpp - strength_ramp_start_cpp),
                0.0,
                1.0,
            )
        strength_curve = lo + (hi - lo) * strength_mix
    correction_delta = correction - 1.0
    if correction_delta_power_positions and correction_delta_power_values:
        delta_power_curve = np.interp(
            sample_frequencies,
            np.asarray(correction_delta_power_positions, dtype=np.float64),
            np.asarray(correction_delta_power_values, dtype=np.float64),
            left=float(correction_delta_power_values[0]),
            right=float(correction_delta_power_values[-1]),
        )
    else:
        delta_power_curve = np.full_like(sample_frequencies, float(correction_delta_power))
    if not np.allclose(delta_power_curve, 1.0):
        correction_delta = np.sign(correction_delta) * np.power(
            np.abs(correction_delta),
            delta_power_curve,
        )
    shaped_correction = 1.0 + correction_delta * strength_curve * blend
    return np.asarray(mtf, dtype=np.float64) * shaped_correction


def clip_reference_correction_curve(
    sample_positions: np.ndarray,
    correction_curve: np.ndarray,
    *,
    clip_lo: float | None,
    clip_hi: float | None,
    clip_lo_positions: Sequence[float] | None = None,
    clip_lo_values: Sequence[float] | None = None,
    clip_hi_positions: Sequence[float] | None = None,
    clip_hi_values: Sequence[float] | None = None,
) -> np.ndarray:
    clipped = np.asarray(correction_curve, dtype=np.float64).copy()
    if clip_lo is not None:
        clipped = np.maximum(clipped, float(clip_lo))
    if clip_lo_positions and clip_lo_values:
        variable_lo = np.interp(
            np.asarray(sample_positions, dtype=np.float64),
            np.asarray(clip_lo_positions, dtype=np.float64),
            np.asarray(clip_lo_values, dtype=np.float64),
            left=float(clip_lo_values[0]),
            right=float(clip_lo_values[-1]),
        )
        clipped = np.maximum(clipped, variable_lo)
    if clip_hi is not None:
        clipped = np.minimum(clipped, float(clip_hi))
    if clip_hi_positions and clip_hi_values:
        variable_hi = np.interp(
            np.asarray(sample_positions, dtype=np.float64),
            np.asarray(clip_hi_positions, dtype=np.float64),
            np.asarray(clip_hi_values, dtype=np.float64),
            left=float(clip_hi_values[0]),
            right=float(clip_hi_values[-1]),
        )
        clipped = np.minimum(clipped, variable_hi)
    return clipped


def derive_reference_acutance_correction_curve(
    reference_curve: Sequence[AcutancePoint],
    estimate_curve: Sequence[AcutancePoint],
    *,
    clip_lo: float | None,
    clip_hi: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    ref_map = {
        (point.print_height_cm, point.viewing_distance_cm): point.acutance
        for point in reference_curve
    }
    sample_positions: list[float] = []
    correction_values: list[float] = []
    for point in estimate_curve:
        key = (point.print_height_cm, point.viewing_distance_cm)
        if key not in ref_map:
            continue
        sample_positions.append(point.viewing_distance_cm / max(point.print_height_cm, EPS))
        correction = ref_map[key] / max(point.acutance, EPS)
        if clip_lo is not None and clip_hi is not None:
            correction = float(np.clip(correction, clip_lo, clip_hi))
        correction_values.append(float(correction))
    return (
        np.asarray(sample_positions, dtype=np.float64),
        np.asarray(correction_values, dtype=np.float64),
    )
