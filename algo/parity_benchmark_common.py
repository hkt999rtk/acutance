from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

import cv2
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


def center_crop_to_common_shape(
    reference_patch: np.ndarray,
    observed_patch: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    reference = np.asarray(reference_patch, dtype=np.float64)
    observed = np.asarray(observed_patch, dtype=np.float64)
    target_height = min(reference.shape[0], observed.shape[0])
    target_width = min(reference.shape[1], observed.shape[1])
    if target_height <= 0 or target_width <= 0:
        raise ValueError("reference and observed patches must both be non-empty")

    def crop_center(patch: np.ndarray) -> np.ndarray:
        top = max((patch.shape[0] - target_height) // 2, 0)
        left = max((patch.shape[1] - target_width) // 2, 0)
        return patch[top : top + target_height, left : left + target_width]

    return crop_center(reference), crop_center(observed)


def align_patch_phase_correlation(
    reference_patch: np.ndarray,
    observed_patch: np.ndarray,
) -> tuple[np.ndarray, tuple[float, float], float]:
    reference, observed = center_crop_to_common_shape(reference_patch, observed_patch)
    window = np.outer(
        np.hanning(reference.shape[0]),
        np.hanning(reference.shape[1]),
    ).astype(np.float32)
    shift, response = cv2.phaseCorrelate(
        reference.astype(np.float32),
        observed.astype(np.float32),
        window,
    )
    transform = np.array(
        [
            [1.0, 0.0, -float(shift[0])],
            [0.0, 1.0, -float(shift[1])],
        ],
        dtype=np.float32,
    )
    aligned = cv2.warpAffine(
        observed.astype(np.float32),
        transform,
        (reference.shape[1], reference.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    return aligned.astype(np.float64), (float(shift[0]), float(shift[1])), float(response)


def _radial_bin_average(
    values2d: np.ndarray,
    *,
    bin_centers: np.ndarray,
    valid_mask: np.ndarray | None = None,
) -> np.ndarray:
    centers = np.asarray(bin_centers, dtype=np.float64)
    values = np.asarray(values2d, dtype=np.float64)
    fy = np.fft.fftshift(np.fft.fftfreq(values.shape[0], d=1.0))
    fx = np.fft.fftshift(np.fft.fftfreq(values.shape[1], d=1.0))
    yy, xx = np.meshgrid(fy, fx, indexing="ij")
    radius = np.sqrt(xx * xx + yy * yy)

    edges = np.empty(centers.size + 1, dtype=np.float64)
    edges[0] = 0.0
    edges[-1] = 0.5
    if centers.size > 1:
        edges[1:-1] = 0.5 * (centers[:-1] + centers[1:])
    else:
        edges[1:-1] = centers[0]

    mask = radius <= 0.5
    if valid_mask is not None:
        mask &= np.asarray(valid_mask, dtype=bool)
    radius = radius[mask]
    sample_values = values[mask]

    averaged = np.ones(centers.size, dtype=np.float64)
    counts = np.zeros(centers.size, dtype=np.int64)
    if radius.size == 0:
        return averaged

    sums = np.zeros(centers.size, dtype=np.float64)
    bin_ids = np.digitize(radius, edges) - 1
    valid = (bin_ids >= 0) & (bin_ids < centers.size)
    for idx, value in zip(bin_ids[valid], sample_values[valid]):
        sums[idx] += float(value)
        counts[idx] += 1
    nonzero = counts > 0
    averaged[nonzero] = sums[nonzero] / counts[nonzero]
    return averaged


def derive_intrinsic_transfer_curve(
    reference_patch: np.ndarray,
    observed_patch: np.ndarray,
    *,
    bin_centers: np.ndarray,
    normalization_band: tuple[float, float],
    normalization_mode: str,
    clip_lo: float,
    clip_hi: float,
    registration_mode: str = "phase_correlation",
) -> np.ndarray:
    reference, observed = center_crop_to_common_shape(reference_patch, observed_patch)
    if registration_mode == "phase_correlation":
        observed_aligned, _, _ = align_patch_phase_correlation(reference, observed)
    elif registration_mode == "none":
        observed_aligned = observed
    else:
        raise ValueError(f"Unsupported intrinsic registration mode: {registration_mode}")

    reference = reference - float(np.mean(reference))
    observed_aligned = observed_aligned - float(np.mean(observed_aligned))
    window = np.outer(
        np.hanning(reference.shape[0]),
        np.hanning(reference.shape[1]),
    )
    reference_spectrum = np.fft.fftshift(np.fft.fft2(reference * window))
    observed_spectrum = np.fft.fftshift(np.fft.fft2(observed_aligned * window))
    reference_power = np.abs(reference_spectrum) ** 2
    transfer_2d = np.abs(observed_spectrum * np.conj(reference_spectrum)) / np.maximum(
        reference_power,
        EPS,
    )
    support = reference_power[reference_power > EPS]
    power_floor = max(float(np.percentile(support, 10)) * 0.1, EPS) if support.size else EPS
    transfer_curve = _radial_bin_average(
        np.clip(transfer_2d, clip_lo, clip_hi),
        bin_centers=np.asarray(bin_centers, dtype=np.float64),
        valid_mask=reference_power >= power_floor,
    )
    lo, hi = normalization_band
    band = (
        (np.asarray(bin_centers, dtype=np.float64) >= float(lo))
        & (np.asarray(bin_centers, dtype=np.float64) <= float(hi))
    )
    if np.any(band):
        if normalization_mode == "mean":
            anchor = float(np.mean(transfer_curve[band]))
        else:
            anchor = float(np.max(transfer_curve[band]))
        if anchor > EPS:
            transfer_curve = transfer_curve / anchor
    return np.clip(transfer_curve, clip_lo, clip_hi)


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
