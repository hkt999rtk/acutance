from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

import numpy as np


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
    shaped_correction = 1.0 + (correction - 1.0) * strength_curve * blend
    return np.asarray(mtf, dtype=np.float64) * shaped_correction
