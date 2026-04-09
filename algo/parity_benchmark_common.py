from __future__ import annotations

from pathlib import Path
import re

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
) -> np.ndarray:
    correction = np.interp(
        np.asarray(frequencies, dtype=np.float64),
        np.asarray(correction_frequencies, dtype=np.float64),
        np.asarray(correction_curve, dtype=np.float64),
        left=float(correction_curve[0]),
        right=float(correction_curve[-1]),
    )
    return np.asarray(mtf, dtype=np.float64) * correction
