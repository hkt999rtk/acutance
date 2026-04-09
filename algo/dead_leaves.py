from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import csv
import json
import math
from enum import Enum

import cv2
import numpy as np


EPS = 1e-12
IMATEST_REFERENCE_BINS = np.array([0.002 + 0.0079 * i for i in range(64)], dtype=np.float64)


class BayerPattern(str, Enum):
    RGGB = "RGGB"
    BGGR = "BGGR"
    GRBG = "GRBG"
    GBRG = "GBRG"


class BayerMode(str, Enum):
    GRAY = "gray"
    DEMOSAIC_RED = "demosaic_red"
    RAW_RED_UPSAMPLED = "raw_red_upsampled"


@dataclass(frozen=True)
class RoiBounds:
    left: int
    right: int
    top: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1

    def clamp(self, width: int, height: int) -> "RoiBounds":
        left = max(0, min(self.left, width - 1))
        right = max(left, min(self.right, width - 1))
        top = max(0, min(self.top, height - 1))
        bottom = max(top, min(self.bottom, height - 1))
        return RoiBounds(left=left, right=right, top=top, bottom=bottom)

    @classmethod
    def centered(
        cls,
        *,
        center_x: int,
        center_y: int,
        width: int,
        height: int,
        image_width: int,
        image_height: int,
    ) -> "RoiBounds":
        roi = cls(
            left=center_x - width // 2,
            right=center_x + width // 2 - 1,
            top=center_y - height // 2,
            bottom=center_y + height // 2 - 1,
        )
        return roi.clamp(image_width, image_height)


@dataclass
class MtfMetrics:
    mtf70: float
    mtf50: float
    mtf30: float
    mtf20: float
    mtf10: float
    undersharpening_pct: float


@dataclass
class SpectrumResult:
    roi: RoiBounds
    frequencies_cpp: np.ndarray
    psd_signal_plus_noise: np.ndarray
    psd_noise: np.ndarray
    psd_signal: np.ndarray
    mtf_unnormalized: np.ndarray
    mtf_with_noise_unnormalized: np.ndarray
    mtf_for_acutance: np.ndarray
    mtf: np.ndarray
    mtf_with_noise: np.ndarray
    acutance_noise_scale: float
    acutance_high_frequency_noise_share: float | None
    metrics: MtfMetrics


@dataclass(frozen=True)
class AcutancePoint:
    print_height_cm: float
    viewing_distance_cm: float
    acutance: float


@dataclass(frozen=True)
class AcutancePreset:
    name: str
    picture_height_cm: float
    viewing_distance_cm: float
    display_mtf_c50_cpd: float | None = None
    display_mtf_model: str = "gaussian"


DEFAULT_ACUTANCE_PRESETS = (
    AcutancePreset(
        name="Computer Monitor Acutance",
        picture_height_cm=30.0,
        viewing_distance_cm=39.3,
    ),
    AcutancePreset(
        name='5.5" Phone Display Acutance',
        picture_height_cm=5.1,
        viewing_distance_cm=29.5,
    ),
    AcutancePreset(
        name="UHDTV Display Acutance",
        picture_height_cm=50.0,
        viewing_distance_cm=113.4,
    ),
    AcutancePreset(
        name="Small Print Acutance",
        picture_height_cm=21.0,
        viewing_distance_cm=54.3,
        display_mtf_c50_cpd=18.0,
        display_mtf_model="ideal_lowpass",
    ),
    AcutancePreset(
        name="Large Print Acutance",
        picture_height_cm=26.0,
        viewing_distance_cm=55.4,
        display_mtf_c50_cpd=18.0,
        display_mtf_model="ideal_lowpass",
    ),
)

QUALITY_LOSS_OM_COEFFICIENTS = (64.99250542, 9.37974246, 0.72233291)
ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS = (521.08180962, -26.62905791, 1.59615575)
ACUTANCE_HF_NOISE_SHARE_BAND = (0.36, 0.5)
ACUTANCE_NOISE_SCALE_CLIP = (1.0, 3.5)
MTF_SHAPE_CORRECTION_SHARE_GATE = (0.05, 0.08)


@dataclass(frozen=True)
class TextureSupportEstimate:
    bbox: tuple[int, int, int, int]
    percentile: float
    crop_support_size: float
    texture_support_size: float
    frequency_scale: float
    component_area_px: int
    border_margin_px: int
    center_offset_px: float
    aspect_ratio: float


@dataclass(frozen=True)
class _TextureSupportComponent:
    bbox: tuple[int, int, int, int]
    area_px: int
    border_margin_px: int
    center_offset_px: float
    aspect_ratio: float


@dataclass
class ParsedImatestCsv:
    image_shape: tuple[int, int] | None
    crop: tuple[int, int]
    lrtb: RoiBounds
    report_gamma: float | None
    color_channel: str | None
    max_detected_frequency_cpp: float | None
    frequencies_cpp: np.ndarray
    mtf: np.ndarray
    mtf_with_noise: np.ndarray
    noise_psd: np.ndarray
    signal_plus_noise_psd: np.ndarray
    signal_psd: np.ndarray
    use_unnormalized_mtf_for_acutance: bool
    acutance_table: list[AcutancePoint]
    reported_acutance: dict[str, float]
    reported_quality_loss: dict[str, float]


@dataclass(frozen=True)
class RawLinearization:
    black_level: float | None = None
    white_level: float | None = None
    black_percentile: float = 0.1
    white_percentile: float = 99.9
    gamma: float = 1.0


@dataclass(frozen=True)
class IdealPsdSegment:
    start_cpp: float
    stop_cpp: float
    log_frequency_polynomial_coefficients: tuple[float, ...]

    @property
    def polynomial_degree(self) -> int:
        return len(self.log_frequency_polynomial_coefficients) - 1


@dataclass(frozen=True)
class AnchoredHighFrequencyCorrection:
    start_cpp: float
    stop_cpp: float
    log_frequency_residual_coefficients: tuple[float, ...]
    regularization_lambda: float = 0.0
    nyquist_relax_start_cpp: float = 0.35
    nyquist_relax_end_weight: float = 0.5

    @property
    def term_count(self) -> int:
        return len(self.log_frequency_residual_coefficients)


@dataclass(frozen=True)
class IdealPsdCalibration:
    name: str
    source_count: int
    log_frequency_polynomial_coefficients: tuple[float, ...] = ()
    piecewise_segments: tuple[IdealPsdSegment, ...] = ()
    blend_width_cpp: float = 0.0
    anchored_high_frequency_correction: AnchoredHighFrequencyCorrection | None = None

    @property
    def polynomial_degree(self) -> int:
        if not self.log_frequency_polynomial_coefficients:
            return -1
        return len(self.log_frequency_polynomial_coefficients) - 1

    @property
    def is_piecewise(self) -> bool:
        return bool(self.piecewise_segments)

    @property
    def has_anchored_high_frequency_correction(self) -> bool:
        return self.anchored_high_frequency_correction is not None


def load_raw_u16(
    path: str | Path,
    width: int,
    height: int,
    *,
    dtype: str = "<u2",
) -> np.ndarray:
    array = np.fromfile(path, dtype=np.dtype(dtype))
    expected = width * height
    if array.size != expected:
        raise ValueError(
            f"Unexpected raw size for {path}: got {array.size}, expected {expected}"
        )
    return array.reshape(height, width).astype(np.float32)


def extract_analysis_plane(
    raw: np.ndarray,
    *,
    bayer_pattern: BayerPattern = BayerPattern.RGGB,
    mode: BayerMode = BayerMode.GRAY,
) -> np.ndarray:
    if mode == BayerMode.GRAY:
        return raw.astype(np.float32)

    if mode == BayerMode.DEMOSAIC_RED:
        code = {
            BayerPattern.RGGB: cv2.COLOR_BAYER_RG2RGB_EA,
            BayerPattern.BGGR: cv2.COLOR_BAYER_BG2RGB_EA,
            BayerPattern.GRBG: cv2.COLOR_BAYER_GR2RGB_EA,
            BayerPattern.GBRG: cv2.COLOR_BAYER_GB2RGB_EA,
        }[bayer_pattern]
        demosaiced = cv2.cvtColor(raw.astype(np.uint16), code).astype(np.float32)
        return demosaiced[:, :, 0]

    if mode == BayerMode.RAW_RED_UPSAMPLED:
        row_offset, col_offset = {
            BayerPattern.RGGB: (0, 0),
            BayerPattern.BGGR: (1, 1),
            BayerPattern.GRBG: (0, 1),
            BayerPattern.GBRG: (1, 0),
        }[bayer_pattern]
        red_plane = raw[row_offset::2, col_offset::2].astype(np.float32)
        return cv2.resize(
            red_plane,
            (raw.shape[1], raw.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )

    raise ValueError(f"Unsupported Bayer mode: {mode}")


def linearize_raw(
    raw: np.ndarray,
    *,
    config: RawLinearization | None = None,
) -> np.ndarray:
    config = config or RawLinearization()
    raw = raw.astype(np.float32)
    black = (
        float(config.black_level)
        if config.black_level is not None
        else float(np.percentile(raw, config.black_percentile))
    )
    white = (
        float(config.white_level)
        if config.white_level is not None
        else float(np.percentile(raw, config.white_percentile))
    )
    scale = max(white - black, 1.0)
    norm = np.clip((raw - black) / scale, 0.0, 1.0)
    if config.gamma != 1.0:
        norm = np.power(norm, config.gamma)
    return norm


def normalize_for_analysis(
    raw: np.ndarray,
    *,
    gamma: float = 1.0,
    black_level: float | None = None,
    white_level: float | None = None,
    black_percentile: float = 0.1,
    white_percentile: float = 99.9,
) -> np.ndarray:
    return linearize_raw(
        raw,
        config=RawLinearization(
            black_level=black_level,
            white_level=white_level,
            black_percentile=black_percentile,
            white_percentile=white_percentile,
            gamma=gamma,
        ),
    )


def detect_texture_roi(image: np.ndarray) -> RoiBounds:
    height, width = image.shape
    scale = min(512.0 / max(height, width), 1.0)
    small = cv2.resize(
        image,
        (max(32, round(width * scale)), max(32, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )

    mean = cv2.GaussianBlur(small, (0, 0), 7)
    mean_sq = cv2.GaussianBlur(small * small, (0, 0), 7)
    local_std = np.sqrt(np.clip(mean_sq - mean * mean, 0.0, None))

    threshold = np.percentile(local_std, 85)
    mask = (local_std >= threshold).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        fallback = RoiBounds(
            left=int(width * 0.3),
            right=int(width * 0.7),
            top=int(height * 0.2),
            bottom=int(height * 0.8),
        )
        return fallback.clamp(width, height)

    cx = small.shape[1] / 2.0
    cy = small.shape[0] / 2.0

    def score(cnt: np.ndarray) -> float:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        mx = x + w / 2.0
        my = y + h / 2.0
        center_penalty = math.hypot(mx - cx, my - cy)
        return area - 30.0 * center_penalty

    contour = max(contours, key=score)
    x, y, w, h = cv2.boundingRect(contour)

    pad_x = int(round(w * 0.06))
    pad_y = int(round(h * 0.06))

    left = int(round((x - pad_x) / scale))
    right = int(round((x + w + pad_x) / scale)) - 1
    top = int(round((y - pad_y) / scale))
    bottom = int(round((y + h + pad_y) / scale)) - 1

    # The variance map tends to include part of the outer gray surround.
    # Shrink the bounding box around its center to better isolate the texture ROI.
    shrink = 0.79
    cx_full = 0.5 * (left + right)
    cy_full = 0.5 * (top + bottom)
    half_w = 0.5 * (right - left + 1) * shrink
    half_h = 0.5 * (bottom - top + 1) * shrink
    roi = RoiBounds(
        left=int(round(cx_full - half_w)),
        right=int(round(cx_full + half_w)) - 1,
        top=int(round(cy_full - half_h)),
        bottom=int(round(cy_full + half_h)) - 1,
    )
    return roi.clamp(width, height)


def extract_roi(image: np.ndarray, roi: RoiBounds) -> np.ndarray:
    return image[roi.top : roi.bottom + 1, roi.left : roi.right + 1]


def _iter_candidate_noise_patches(
    image: np.ndarray,
    roi: RoiBounds,
    *,
    patch_size: int = 128,
    stride: int | None = None,
) -> Iterable[np.ndarray]:
    stride = stride or max(16, patch_size // 2)
    regions = [
        image[:, : max(0, roi.left - 16)],
        image[:, min(image.shape[1], roi.right + 17) :],
        image[: max(0, roi.top - 16), :],
        image[min(image.shape[0], roi.bottom + 17) :, :],
    ]
    for region in regions:
        rh, rw = region.shape
        if rh < patch_size or rw < patch_size:
            continue
        for top in range(0, rh - patch_size + 1, stride):
            for left in range(0, rw - patch_size + 1, stride):
                yield region[top : top + patch_size, left : left + patch_size]


def estimate_noise_psd(
    image: np.ndarray,
    roi: RoiBounds,
    num_bins: int,
    *,
    patch_size: int = 128,
    max_patches: int = 12,
    bin_centers: np.ndarray | None = None,
    model: str = "empirical",
    log_polynomial_degree: int = 2,
) -> np.ndarray:
    patches = list(_iter_candidate_noise_patches(image, roi, patch_size=patch_size))
    if not patches:
        return np.zeros(num_bins, dtype=np.float64)

    ranked = sorted(patches, key=lambda patch: float(np.std(patch)))
    chosen = ranked[:max_patches]
    spectra = []
    for patch in chosen:
        _, psd = radial_psd(patch, num_bins=num_bins, bin_centers=bin_centers)
        spectra.append(psd)
    noise_psd = np.mean(np.stack(spectra, axis=0), axis=0)
    if model == "empirical":
        return noise_psd
    if model != "colored_log_polynomial":
        raise ValueError(f"Unknown noise PSD model: {model}")

    if bin_centers is None:
        frequencies = np.linspace(0.0, 0.5, num_bins, endpoint=False) + 0.25 / max(num_bins, 1)
    else:
        frequencies = np.asarray(bin_centers, dtype=np.float64)
    valid = (frequencies > 0.0) & np.isfinite(noise_psd) & (noise_psd > 0.0)
    if np.count_nonzero(valid) < log_polynomial_degree + 1:
        return noise_psd
    fit = np.polyfit(
        np.log(frequencies[valid]),
        np.log(np.maximum(noise_psd[valid], EPS)),
        log_polynomial_degree,
    )
    return np.exp(np.polyval(fit, np.log(np.maximum(frequencies, 1e-4))))


def _texture_support_mask(
    crop: np.ndarray,
    *,
    percentile: float = 45.0,
    sigma: float = 5.0,
    open_kernel: int = 5,
    close_kernel: int = 5,
) -> np.ndarray:
    blur = cv2.GaussianBlur(crop, (0, 0), sigma)
    blur_sq = cv2.GaussianBlur(crop * crop, (0, 0), sigma)
    local_std = np.sqrt(np.clip(blur_sq - blur * blur, 0.0, None))
    threshold = float(np.percentile(local_std, percentile))
    mask = np.uint8(local_std >= threshold)
    if open_kernel > 1:
        kernel = np.ones((open_kernel, open_kernel), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    if close_kernel > 1:
        kernel = np.ones((close_kernel, close_kernel), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask


def _select_texture_support_component(
    mask: np.ndarray,
    *,
    min_border_margin: int = 0,
    interior_min_area_ratio: float = 0.35,
) -> _TextureSupportComponent | None:
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return None

    components: list[_TextureSupportComponent] = []
    crop_h, crop_w = mask.shape
    crop_cx = crop_w / 2.0
    crop_cy = crop_h / 2.0
    for idx in range(1, count):
        x, y, w, h, area = stats[idx]
        if w <= 0 or h <= 0 or area <= 0:
            continue
        center_x, center_y = centroids[idx]
        border_margin = int(min(x, y, crop_w - (x + w), crop_h - (y + h)))
        components.append(
            _TextureSupportComponent(
                bbox=(int(x), int(y), int(w), int(h)),
                area_px=int(area),
                border_margin_px=border_margin,
                center_offset_px=float(math.hypot(center_x - crop_cx, center_y - crop_cy)),
                aspect_ratio=float(min(w, h) / max(w, h)),
            )
        )

    if not components:
        return None

    dominant = max(
        components,
        key=lambda comp: (comp.area_px, -comp.center_offset_px, comp.aspect_ratio),
    )
    interior = [
        comp
        for comp in components
        if comp.border_margin_px >= min_border_margin
        and comp.area_px >= dominant.area_px * interior_min_area_ratio
    ]
    pool = interior or [dominant]
    return max(
        pool,
        key=lambda comp: (comp.area_px, -comp.center_offset_px, comp.aspect_ratio),
    )


def estimate_texture_support_scale(
    crop: np.ndarray,
    *,
    percentile: float = 45.0,
    sigma: float = 5.0,
    min_border_margin: int = 0,
    interior_min_area_ratio: float = 0.35,
) -> TextureSupportEstimate:
    mask = _texture_support_mask(crop, percentile=percentile, sigma=sigma)
    component = _select_texture_support_component(
        mask,
        min_border_margin=min_border_margin,
        interior_min_area_ratio=interior_min_area_ratio,
    )
    if component is None:
        width = crop.shape[1]
        height = crop.shape[0]
        crop_support = float(np.sqrt(width * height))
        return TextureSupportEstimate(
            bbox=(0, 0, width, height),
            percentile=percentile,
            crop_support_size=crop_support,
            texture_support_size=crop_support,
            frequency_scale=1.0,
            component_area_px=width * height,
            border_margin_px=0,
            center_offset_px=0.0,
            aspect_ratio=min(width, height) / max(width, height),
        )

    x, y, w, h = component.bbox
    crop_support = float(np.sqrt(crop.shape[0] * crop.shape[1]))
    texture_support = float(np.sqrt(w * h))
    return TextureSupportEstimate(
        bbox=component.bbox,
        percentile=percentile,
        crop_support_size=crop_support,
        texture_support_size=texture_support,
        frequency_scale=crop_support / max(texture_support, 1.0),
        component_area_px=component.area_px,
        border_margin_px=component.border_margin_px,
        center_offset_px=component.center_offset_px,
        aspect_ratio=component.aspect_ratio,
    )


def refine_roi_to_texture_support(
    image: np.ndarray,
    *,
    seed_roi: RoiBounds,
    target_width: int,
    target_height: int,
    percentile: float = 45.0,
    sigma: float = 5.0,
    min_border_margin: int = 8,
    search_radius: int = 12,
    step: int = 2,
    area_tolerance: float = 0.98,
) -> RoiBounds:
    seed_cx = (seed_roi.left + seed_roi.right) // 2
    seed_cy = (seed_roi.top + seed_roi.bottom) // 2
    candidates: list[tuple[RoiBounds, TextureSupportEstimate]] = []

    for dy in range(-search_radius, search_radius + 1, step):
        for dx in range(-search_radius, search_radius + 1, step):
            candidate = RoiBounds.centered(
                center_x=seed_cx + dx,
                center_y=seed_cy + dy,
                width=target_width,
                height=target_height,
                image_width=image.shape[1],
                image_height=image.shape[0],
            )
            crop = extract_roi(image, candidate)
            support = estimate_texture_support_scale(
                crop,
                percentile=percentile,
                sigma=sigma,
                min_border_margin=0,
            )
            candidates.append((candidate, support))

    if not candidates:
        return seed_roi

    max_area = max(support.component_area_px for _, support in candidates)
    near_max = [
        (candidate, support)
        for candidate, support in candidates
        if support.component_area_px >= max_area * area_tolerance
    ]
    preferred = [
        (candidate, support)
        for candidate, support in near_max
        if support.border_margin_px >= min_border_margin
    ]
    pool = preferred or near_max
    best_roi, _ = max(
        pool,
        key=lambda item: (
            item[1].border_margin_px,
            -item[1].center_offset_px,
            item[1].aspect_ratio,
        ),
    )
    return best_roi


def radial_psd(
    image: np.ndarray,
    *,
    num_bins: int = 64,
    window: bool = True,
    bin_centers: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    data = image.astype(np.float64)
    data = data - float(np.mean(data))

    if window:
        wy = np.hanning(data.shape[0])
        wx = np.hanning(data.shape[1])
        data = data * np.outer(wy, wx)

    spectrum = np.fft.fftshift(np.fft.fft2(data))
    psd2 = (np.abs(spectrum) ** 2) / data.size

    fy = np.fft.fftshift(np.fft.fftfreq(data.shape[0], d=1.0))
    fx = np.fft.fftshift(np.fft.fftfreq(data.shape[1], d=1.0))
    yy, xx = np.meshgrid(fy, fx, indexing="ij")
    radius = np.sqrt(xx * xx + yy * yy)

    mask = radius <= 0.5
    radius = radius[mask]
    psd2 = psd2[mask]

    if bin_centers is None:
        edges = np.linspace(0.0, 0.5, num_bins + 1)
        centers = 0.5 * (edges[:-1] + edges[1:])
    else:
        centers = np.asarray(bin_centers, dtype=np.float64)
        edges = np.empty(centers.size + 1, dtype=np.float64)
        edges[0] = 0.0
        edges[-1] = 0.5
        if centers.size > 1:
            edges[1:-1] = 0.5 * (centers[:-1] + centers[1:])
        else:
            edges[1:-1] = centers[0]
    psd = np.zeros(num_bins, dtype=np.float64)
    counts = np.zeros(num_bins, dtype=np.int64)

    bin_ids = np.digitize(radius, edges) - 1
    valid = (bin_ids >= 0) & (bin_ids < num_bins)
    for idx, value in zip(bin_ids[valid], psd2[valid]):
        psd[idx] += float(value)
        counts[idx] += 1

    counts = np.maximum(counts, 1)
    psd /= counts
    return centers, psd


def interpolate_dead_leaves_coefficients(length_px: int) -> tuple[float, float, float]:
    lengths = np.array([128.0, 256.0, 512.0, 1024.0, 2048.0], dtype=np.float64)
    log_a = np.array([12.531, 13.985, 15.476, 16.690, 17.253], dtype=np.float64)
    b = np.array([2.295, 2.400, 2.407, 2.718, 3.601], dtype=np.float64)
    c = np.array([0.09991, 0.12613, 0.12067, 0.19723, 0.39951], dtype=np.float64)
    x = float(np.clip(length_px, lengths.min(), lengths.max()))
    return (
        float(np.interp(x, lengths, log_a)),
        float(np.interp(x, lengths, b)),
        float(np.interp(x, lengths, c)),
    )


def load_ideal_psd_calibration(path: str | Path) -> IdealPsdCalibration:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "log_frequency_polynomial_coefficients" in data:
        coeffs = tuple(float(x) for x in data["log_frequency_polynomial_coefficients"])
    elif "log_frequency_quadratic_coefficients" in data:
        coeffs = tuple(float(x) for x in data["log_frequency_quadratic_coefficients"])
    else:
        coeffs = ()
    piecewise_segments = tuple(
        IdealPsdSegment(
            start_cpp=float(item["start_cpp"]),
            stop_cpp=float(item["stop_cpp"]),
            log_frequency_polynomial_coefficients=tuple(
                float(x) for x in item["log_frequency_polynomial_coefficients"]
            ),
        )
        for item in data.get("piecewise_segments", [])
    )
    anchored_high_frequency_correction = None
    if "anchored_high_frequency_correction" in data:
        item = data["anchored_high_frequency_correction"]
        anchored_high_frequency_correction = AnchoredHighFrequencyCorrection(
            start_cpp=float(item["start_cpp"]),
            stop_cpp=float(item["stop_cpp"]),
            log_frequency_residual_coefficients=tuple(
                float(x) for x in item["log_frequency_residual_coefficients"]
            ),
            regularization_lambda=float(item.get("regularization_lambda", 0.0)),
            nyquist_relax_start_cpp=float(item.get("nyquist_relax_start_cpp", 0.35)),
            nyquist_relax_end_weight=float(item.get("nyquist_relax_end_weight", 0.5)),
        )
    return IdealPsdCalibration(
        name=str(data["name"]),
        source_count=int(data["source_count"]),
        log_frequency_polynomial_coefficients=coeffs,
        piecewise_segments=piecewise_segments,
        blend_width_cpp=float(data.get("blend_width_cpp", 0.0)),
        anchored_high_frequency_correction=anchored_high_frequency_correction,
    )


def save_ideal_psd_calibration(
    path: str | Path,
    calibration: IdealPsdCalibration,
) -> None:
    payload = {
        "name": calibration.name,
        "source_count": calibration.source_count,
        "blend_width_cpp": calibration.blend_width_cpp,
    }
    if calibration.log_frequency_polynomial_coefficients:
        payload["log_frequency_polynomial_coefficients"] = list(
            calibration.log_frequency_polynomial_coefficients
        )
        payload["polynomial_degree"] = calibration.polynomial_degree
    if calibration.piecewise_segments:
        payload["piecewise_segments"] = [
            {
                "start_cpp": segment.start_cpp,
                "stop_cpp": segment.stop_cpp,
                "log_frequency_polynomial_coefficients": list(
                    segment.log_frequency_polynomial_coefficients
                ),
                "polynomial_degree": segment.polynomial_degree,
            }
            for segment in calibration.piecewise_segments
        ]
    if calibration.anchored_high_frequency_correction is not None:
        correction = calibration.anchored_high_frequency_correction
        payload["anchored_high_frequency_correction"] = {
            "start_cpp": correction.start_cpp,
            "stop_cpp": correction.stop_cpp,
            "log_frequency_residual_coefficients": list(
                correction.log_frequency_residual_coefficients
            ),
            "regularization_lambda": correction.regularization_lambda,
            "nyquist_relax_start_cpp": correction.nyquist_relax_start_cpp,
            "nyquist_relax_end_weight": correction.nyquist_relax_end_weight,
            "term_count": correction.term_count,
        }
    if calibration.polynomial_degree == 2 and calibration.log_frequency_polynomial_coefficients:
        payload["log_frequency_quadratic_coefficients"] = list(
            calibration.log_frequency_polynomial_coefficients
        )
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def fit_ideal_psd_calibration_from_csvs(
    csv_paths: Iterable[str | Path],
    *,
    name: str,
    polynomial_degree: int = 2,
) -> IdealPsdCalibration:
    coefficients = []
    for path in csv_paths:
        parsed = parse_imatest_random_csv(path)
        valid = (parsed.frequencies_cpp > 0.0) & (parsed.mtf > 0.0) & (parsed.signal_psd > 0.0)
        frequencies = parsed.frequencies_cpp[valid]
        mtf = parsed.mtf[valid]
        signal_psd = parsed.signal_psd[valid]
        ideal_psd = signal_psd / np.maximum(np.square(mtf), EPS)
        fit = np.polyfit(np.log(frequencies), np.log(ideal_psd), polynomial_degree)
        coefficients.append(fit)

    if not coefficients:
        raise ValueError("No CSVs provided for ideal PSD calibration")

    mean_fit = np.mean(np.stack(coefficients, axis=0), axis=0)
    return IdealPsdCalibration(
        name=name,
        source_count=len(coefficients),
        log_frequency_polynomial_coefficients=tuple(float(x) for x in mean_fit),
    )


def fit_piecewise_ideal_psd_calibration_from_csvs(
    csv_paths: Iterable[str | Path],
    *,
    name: str,
    split_cpp: float = 0.24,
    overlap_cpp: float = 0.08,
    low_degree: int = 2,
    high_degree: int = 2,
) -> IdealPsdCalibration:
    if overlap_cpp <= 0.0:
        raise ValueError("overlap_cpp must be positive")

    frequency_rows = []
    ideal_rows = []
    for path in csv_paths:
        parsed = parse_imatest_random_csv(path)
        valid = (parsed.frequencies_cpp > 0.0) & (parsed.mtf > 0.0) & (parsed.signal_psd > 0.0)
        frequencies = parsed.frequencies_cpp[valid]
        signal_psd = parsed.signal_psd[valid]
        ideal_psd = signal_psd / np.maximum(np.square(parsed.mtf[valid]), EPS)
        frequency_rows.append(frequencies)
        ideal_rows.append(ideal_psd)

    if not frequency_rows:
        raise ValueError("No CSVs provided for ideal PSD calibration")

    all_frequencies = np.concatenate(frequency_rows, axis=0)
    all_ideal = np.concatenate(ideal_rows, axis=0)
    log_frequencies = np.log(all_frequencies)
    log_ideal = np.log(np.maximum(all_ideal, EPS))

    blend_lo = split_cpp - overlap_cpp * 0.5
    blend_hi = split_cpp + overlap_cpp * 0.5

    low_weights = np.ones_like(all_frequencies)
    high_weights = np.ones_like(all_frequencies)
    high_weights[all_frequencies < blend_lo] = 0.0
    low_weights[all_frequencies > blend_hi] = 0.0

    transition = (all_frequencies >= blend_lo) & (all_frequencies <= blend_hi)
    if np.any(transition):
        phase = (all_frequencies[transition] - blend_lo) / max(blend_hi - blend_lo, EPS)
        high_weights[transition] = 0.5 * (1.0 - np.cos(np.pi * phase))
        low_weights[transition] = 0.5 * (1.0 + np.cos(np.pi * phase))

    low_fit = np.polyfit(
        log_frequencies,
        log_ideal,
        low_degree,
        w=np.sqrt(np.maximum(low_weights, EPS)),
    )
    high_fit = np.polyfit(
        log_frequencies,
        log_ideal,
        high_degree,
        w=np.sqrt(np.maximum(high_weights, EPS)),
    )

    return IdealPsdCalibration(
        name=name,
        source_count=len(frequency_rows),
        piecewise_segments=(
            IdealPsdSegment(
                start_cpp=0.0,
                stop_cpp=blend_hi,
                log_frequency_polynomial_coefficients=tuple(float(x) for x in low_fit),
            ),
            IdealPsdSegment(
                start_cpp=blend_lo,
                stop_cpp=0.5,
                log_frequency_polynomial_coefficients=tuple(float(x) for x in high_fit),
            ),
        ),
        blend_width_cpp=overlap_cpp,
    )


def fit_anchored_high_frequency_ideal_psd_calibration_from_csvs(
    csv_paths: Iterable[str | Path],
    *,
    name: str,
    split_cpp: float = 0.18,
    stop_cpp: float = 0.5,
    residual_term_count: int = 2,
    regularization_lambda: float = 0.02,
    nyquist_relax_start_cpp: float = 0.35,
    nyquist_relax_end_weight: float = 0.5,
) -> IdealPsdCalibration:
    if residual_term_count <= 0:
        raise ValueError("residual_term_count must be positive")
    if stop_cpp <= split_cpp:
        raise ValueError("stop_cpp must be greater than split_cpp")

    base = fit_ideal_psd_calibration_from_csvs(
        csv_paths,
        name=name,
        polynomial_degree=2,
    )

    log_frequencies_rows = []
    residual_rows = []
    weight_rows = []
    log_split = math.log(max(split_cpp, 1e-4))

    for path in csv_paths:
        parsed = parse_imatest_random_csv(path)
        valid = (
            (parsed.frequencies_cpp >= split_cpp)
            & (parsed.frequencies_cpp <= stop_cpp)
            & (parsed.mtf > 0.0)
            & (parsed.signal_psd > 0.0)
        )
        if not np.any(valid):
            continue
        frequencies = parsed.frequencies_cpp[valid]
        signal_psd = parsed.signal_psd[valid]
        ideal_psd = signal_psd / np.maximum(np.square(parsed.mtf[valid]), EPS)
        log_frequencies = np.log(frequencies)
        base_log_ideal = np.polyval(base.log_frequency_polynomial_coefficients, log_frequencies)
        residual = np.log(np.maximum(ideal_psd, EPS)) - base_log_ideal

        weights = np.ones_like(frequencies, dtype=np.float64)
        if nyquist_relax_start_cpp < stop_cpp:
            high = frequencies >= nyquist_relax_start_cpp
            if np.any(high):
                phase = (frequencies[high] - nyquist_relax_start_cpp) / max(
                    stop_cpp - nyquist_relax_start_cpp,
                    EPS,
                )
                phase = np.clip(phase, 0.0, 1.0)
                weights[high] = 1.0 - (1.0 - nyquist_relax_end_weight) * phase

        log_frequencies_rows.append(log_frequencies)
        residual_rows.append(residual)
        weight_rows.append(weights)

    if not log_frequencies_rows:
        raise ValueError("No CSVs provided for anchored high-frequency calibration")

    log_frequencies = np.concatenate(log_frequencies_rows, axis=0)
    residuals = np.concatenate(residual_rows, axis=0)
    weights = np.concatenate(weight_rows, axis=0)
    finite = np.isfinite(log_frequencies) & np.isfinite(residuals) & np.isfinite(weights)
    log_frequencies = log_frequencies[finite]
    residuals = residuals[finite]
    weights = weights[finite]
    delta = np.maximum(log_frequencies - log_split, 0.0)
    design = np.stack(
        [np.power(delta, power) for power in range(2, 2 + residual_term_count)],
        axis=1,
    )
    column_scale = np.maximum(np.linalg.norm(design, axis=0), 1.0)
    design_scaled = design / column_scale

    weighted_design = design_scaled * weights[:, None]
    lhs = np.einsum("ni,nj->ij", design_scaled, weighted_design)
    lhs += regularization_lambda * np.eye(residual_term_count, dtype=np.float64)
    rhs = np.einsum("ni,n->i", design_scaled, weights * residuals)
    coefficients = np.linalg.solve(lhs, rhs) / column_scale

    return IdealPsdCalibration(
        name=name,
        source_count=len(log_frequencies_rows),
        log_frequency_polynomial_coefficients=base.log_frequency_polynomial_coefficients,
        anchored_high_frequency_correction=AnchoredHighFrequencyCorrection(
            start_cpp=split_cpp,
            stop_cpp=stop_cpp,
            log_frequency_residual_coefficients=tuple(float(x) for x in coefficients),
            regularization_lambda=regularization_lambda,
            nyquist_relax_start_cpp=nyquist_relax_start_cpp,
            nyquist_relax_end_weight=nyquist_relax_end_weight,
        ),
    )


def ideal_dead_leaves_psd(
    frequencies_cpp: np.ndarray,
    *,
    length_px: int,
    mode: str = "quadratic_log",
    exponent: float = 2.0,
    calibration: IdealPsdCalibration | None = None,
) -> np.ndarray:
    f = np.clip(np.asarray(frequencies_cpp, dtype=np.float64), 1e-4, None)
    if mode == "power_law":
        return np.power(f, -exponent)
    if mode == "calibrated_log":
        if calibration is None:
            raise ValueError("calibrated_log mode requires an IdealPsdCalibration")
        if calibration.is_piecewise:
            if len(calibration.piecewise_segments) != 2:
                raise ValueError("Piecewise calibration currently expects exactly 2 segments")
            low_segment, high_segment = calibration.piecewise_segments
            low_psd = np.exp(
                np.polyval(low_segment.log_frequency_polynomial_coefficients, np.log(f))
            )
            high_psd = np.exp(
                np.polyval(high_segment.log_frequency_polynomial_coefficients, np.log(f))
            )
            blend_lo = max(high_segment.start_cpp, 1e-4)
            blend_hi = max(low_segment.stop_cpp, blend_lo + EPS)
            weights = np.ones_like(f)
            weights[f >= blend_hi] = 0.0
            transition = (f > blend_lo) & (f < blend_hi)
            if np.any(transition):
                phase = (f[transition] - blend_lo) / max(blend_hi - blend_lo, EPS)
                weights[transition] = 0.5 * (1.0 + np.cos(np.pi * phase))
            return low_psd * weights + high_psd * (1.0 - weights)
        psd = np.exp(
            np.polyval(calibration.log_frequency_polynomial_coefficients, np.log(f))
        )
        correction = calibration.anchored_high_frequency_correction
        if correction is not None:
            log_f = np.log(f)
            log_split = math.log(max(correction.start_cpp, 1e-4))
            residual = np.zeros_like(f)
            active = f >= correction.start_cpp
            if np.any(active):
                delta = np.maximum(log_f[active] - log_split, 0.0)
                correction_terms = np.stack(
                    [
                        np.power(delta, power)
                        for power in range(
                            2, 2 + len(correction.log_frequency_residual_coefficients)
                        )
                    ],
                    axis=1,
                )
                residual[active] = correction_terms @ np.asarray(
                    correction.log_frequency_residual_coefficients,
                    dtype=np.float64,
                )
            if correction.stop_cpp > correction.start_cpp:
                taper = np.ones_like(f)
                high = f >= correction.stop_cpp
                taper[high] = 0.0
                transition = (f > correction.start_cpp) & (f < correction.stop_cpp)
                if np.any(transition):
                    phase = (f[transition] - correction.start_cpp) / max(
                        correction.stop_cpp - correction.start_cpp,
                        EPS,
                    )
                    taper[transition] = 0.5 * (1.0 - np.cos(np.pi * phase))
                residual *= taper
            psd *= np.exp(residual)
        return psd
    if mode != "quadratic_log":
        raise ValueError(f"Unknown ideal PSD mode: {mode}")

    log_a, b, c = interpolate_dead_leaves_coefficients(length_px)
    log_f = np.log(f)
    return np.exp(log_a - b * log_f - c * np.square(log_f))


def normalize_mtf_curve(
    mtf: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    reference_band: tuple[float, float] = (0.01, 0.03),
    reference_mode: str = "max",
) -> np.ndarray:
    lo, hi = reference_band
    band = (frequencies_cpp >= lo) & (frequencies_cpp <= hi)
    values = mtf[band] if np.any(band) else mtf
    if reference_mode == "max":
        ref = float(np.max(values))
    elif reference_mode == "mean":
        ref = float(np.mean(values))
    elif reference_mode == "p90":
        ref = float(np.percentile(values, 90.0))
    else:
        raise ValueError(f"Unknown normalization mode: {reference_mode}")
    ref = max(ref, EPS)
    return mtf / ref


def anchor_mtf_to_dc(
    mtf: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    reference_band: tuple[float, float] = (0.017, 0.035),
    reference_mode: str = "mean",
) -> np.ndarray:
    # Dead-leaves PSD methods do not directly observe the f=0 DC point.
    # For acutance we need an MTF whose low-frequency gain is referenced to 1,
    # while still preserving sharpening peaks above 1. We therefore estimate
    # the DC anchor from a stable low-frequency band rather than the global peak.
    return normalize_mtf_curve(
        mtf,
        frequencies_cpp,
        reference_band=reference_band,
        reference_mode=reference_mode,
    )


def smooth_curve_1d(
    values: np.ndarray,
    *,
    window: int = 1,
) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    if window <= 1:
        return data.copy()
    if window % 2 == 0:
        raise ValueError("Smoothing window must be odd")
    kernel = np.hanning(window)
    if float(np.sum(kernel)) <= EPS:
        return data.copy()
    kernel /= np.sum(kernel)
    pad = window // 2
    padded = np.pad(data, (pad, pad), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def _first_descending_branch(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    smoothing_window: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    usable = frequencies_cpp >= 0.005
    f = frequencies_cpp[usable]
    y = smooth_curve_1d(mtf[usable], window=smoothing_window)
    if f.size == 0:
        return frequencies_cpp, mtf

    peak_limit = f <= 0.12
    peak_idx = int(np.argmax(y[peak_limit])) if np.any(peak_limit) else int(np.argmax(y))

    end_idx = len(y) - 1
    for idx in range(peak_idx + 2, len(y) - 1):
        if y[idx - 1] >= y[idx] and y[idx + 1] > y[idx]:
            end_idx = idx
            break

    branch_f = f[peak_idx : end_idx + 1]
    branch_y = y[peak_idx : end_idx + 1]
    envelope = np.minimum.accumulate(branch_y)
    return branch_f, envelope


def interpolate_threshold(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    level: float,
    *,
    smoothing_window: int = 1,
    interpolation_mode: str = "linear",
) -> float:
    branch_f, branch_y = _first_descending_branch(
        frequencies_cpp,
        mtf,
        smoothing_window=smoothing_window,
    )
    if branch_y.size == 0 or float(np.min(branch_y)) > level:
        return 0.0

    for idx in range(1, branch_y.size):
        y0 = branch_y[idx - 1]
        y1 = branch_y[idx]
        if y0 >= level >= y1:
            f0 = branch_f[idx - 1]
            f1 = branch_f[idx]
            if abs(y1 - y0) < EPS:
                return float(f1)
            t = (level - y0) / (y1 - y0)
            if interpolation_mode == "log_frequency":
                return float(np.exp(np.log(f0) + t * (np.log(f1) - np.log(f0))))
            if interpolation_mode != "linear":
                raise ValueError(f"Unknown interpolation mode: {interpolation_mode}")
            return float(f0 + t * (f1 - f0))
    return 0.0


def compute_mtf_metrics(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    smoothing_window: int = 1,
    interpolation_mode: str = "linear",
) -> MtfMetrics:
    peak = float(np.max(mtf))
    undersharpening = max(0.0, (1.0 - peak) * 100.0)
    return MtfMetrics(
        mtf70=interpolate_threshold(
            frequencies_cpp,
            mtf,
            0.7,
            smoothing_window=smoothing_window,
            interpolation_mode=interpolation_mode,
        ),
        mtf50=interpolate_threshold(
            frequencies_cpp,
            mtf,
            0.5,
            smoothing_window=smoothing_window,
            interpolation_mode=interpolation_mode,
        ),
        mtf30=interpolate_threshold(
            frequencies_cpp,
            mtf,
            0.3,
            smoothing_window=smoothing_window,
            interpolation_mode=interpolation_mode,
        ),
        mtf20=interpolate_threshold(
            frequencies_cpp,
            mtf,
            0.2,
            smoothing_window=smoothing_window,
            interpolation_mode=interpolation_mode,
        ),
        mtf10=interpolate_threshold(
            frequencies_cpp,
            mtf,
            0.1,
            smoothing_window=smoothing_window,
            interpolation_mode=interpolation_mode,
        ),
        undersharpening_pct=undersharpening,
    )


def apply_frequency_scale(
    frequencies_cpp: np.ndarray,
    *,
    scale: float = 1.0,
) -> np.ndarray:
    return np.asarray(frequencies_cpp, dtype=np.float64) * float(scale)


def _sinc_pi(values: np.ndarray) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    output = np.ones_like(data)
    nonzero = np.abs(data) > EPS
    output[nonzero] = np.sin(np.pi * data[nonzero]) / (np.pi * data[nonzero])
    return output


def estimate_mtf_compensation_curve(
    frequencies_cpp: np.ndarray,
    *,
    mode: str = "none",
    sensor_fill_factor: float = 1.0,
    denominator_clip: float = 0.25,
    max_gain: float = 3.0,
) -> np.ndarray:
    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    if mode == "none":
        return np.ones_like(frequencies)
    if mode != "sensor_aperture_sinc":
        raise ValueError(f"Unknown MTF compensation mode: {mode}")
    if sensor_fill_factor <= 0.0:
        raise ValueError("sensor_fill_factor must be positive")
    if denominator_clip <= 0.0:
        raise ValueError("denominator_clip must be positive")
    if max_gain < 1.0:
        raise ValueError("max_gain must be at least 1.0")

    sensor_mtf = _sinc_pi(sensor_fill_factor * frequencies)
    compensation = 1.0 / np.clip(sensor_mtf, denominator_clip, None)
    return np.clip(compensation, 1.0, max_gain)


def apply_mtf_compensation(
    mtf: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    mode: str = "none",
    sensor_fill_factor: float = 1.0,
    denominator_clip: float = 0.25,
    max_gain: float = 3.0,
) -> tuple[np.ndarray, np.ndarray]:
    compensation = estimate_mtf_compensation_curve(
        frequencies_cpp,
        mode=mode,
        sensor_fill_factor=sensor_fill_factor,
        denominator_clip=denominator_clip,
        max_gain=max_gain,
    )
    return np.asarray(mtf, dtype=np.float64) * compensation, compensation


def apply_high_frequency_guard(
    signal_psd: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    start_cpp: float | None = None,
    stop_cpp: float = 0.5,
) -> np.ndarray:
    if start_cpp is None:
        return np.asarray(signal_psd, dtype=np.float64)

    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    guarded = np.asarray(signal_psd, dtype=np.float64).copy()
    if start_cpp >= stop_cpp:
        raise ValueError("high-frequency guard start must be less than stop")

    weights = np.ones_like(frequencies)
    high = frequencies >= stop_cpp
    taper = (frequencies > start_cpp) & (frequencies < stop_cpp)
    weights[high] = 0.0
    weights[taper] = 0.5 * (
        1.0
        + np.cos(
            np.pi * (frequencies[taper] - start_cpp) / (stop_cpp - start_cpp)
        )
    )
    return guarded * np.clip(weights, 0.0, 1.0)


def apply_signal_psd_band_correction(
    signal_psd: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    start_cpp: float = 0.08,
    peak_cpp: float = 0.15,
    stop_cpp: float = 0.22,
    gain: float = 0.0,
) -> np.ndarray:
    corrected = np.asarray(signal_psd, dtype=np.float64).copy()
    if abs(gain) < EPS:
        return corrected
    if not (start_cpp < peak_cpp < stop_cpp):
        raise ValueError("signal PSD correction requires start < peak < stop")

    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    weights = np.zeros_like(frequencies)

    rising = (frequencies > start_cpp) & (frequencies <= peak_cpp)
    if np.any(rising):
        phase = (frequencies[rising] - start_cpp) / max(peak_cpp - start_cpp, EPS)
        weights[rising] = 0.5 * (1.0 - np.cos(np.pi * phase))

    falling = (frequencies > peak_cpp) & (frequencies < stop_cpp)
    if np.any(falling):
        phase = (frequencies[falling] - peak_cpp) / max(stop_cpp - peak_cpp, EPS)
        weights[falling] = 0.5 * (1.0 + np.cos(np.pi * phase))

    return corrected * (1.0 + gain * weights)


def cosine_bump(
    frequencies_cpp: np.ndarray,
    *,
    start_cpp: float,
    peak_cpp: float,
    stop_cpp: float,
) -> np.ndarray:
    weights = np.zeros_like(np.asarray(frequencies_cpp, dtype=np.float64))
    if not (start_cpp < peak_cpp < stop_cpp):
        raise ValueError("cosine bump requires start < peak < stop")

    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    rising = (frequencies > start_cpp) & (frequencies <= peak_cpp)
    if np.any(rising):
        phase = (frequencies[rising] - start_cpp) / max(peak_cpp - start_cpp, EPS)
        weights[rising] = 0.5 * (1.0 - np.cos(np.pi * phase))

    falling = (frequencies > peak_cpp) & (frequencies < stop_cpp)
    if np.any(falling):
        phase = (frequencies[falling] - peak_cpp) / max(stop_cpp - peak_cpp, EPS)
        weights[falling] = 0.5 * (1.0 + np.cos(np.pi * phase))
    return weights


def estimate_mtf_shape_correction_curve(
    frequencies_cpp: np.ndarray,
    *,
    mode: str = "none",
    high_frequency_noise_share: float | None = None,
    gain: float = 0.035,
    share_gate_lo: float = MTF_SHAPE_CORRECTION_SHARE_GATE[0],
    share_gate_hi: float = MTF_SHAPE_CORRECTION_SHARE_GATE[1],
    mid_start_cpp: float = 0.095,
    mid_peak_cpp: float = 0.145,
    mid_stop_cpp: float = 0.19,
    high_start_cpp: float = 0.36,
    high_peak_cpp: float = 0.40,
    high_stop_cpp: float = 0.49,
    high_weight: float = 0.25,
) -> np.ndarray:
    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    if mode == "none":
        return np.ones_like(frequencies)
    if mode != "hf_noise_share_gated_bump":
        raise ValueError(f"Unknown MTF shape correction mode: {mode}")
    if high_frequency_noise_share is None:
        raise ValueError("high_frequency_noise_share is required for gated bump correction")
    if share_gate_hi <= share_gate_lo:
        raise ValueError("share gate requires hi > lo")

    gate = float(
        np.clip(
            (share_gate_hi - high_frequency_noise_share) / (share_gate_hi - share_gate_lo),
            0.0,
            1.0,
        )
    )
    correction_shape = cosine_bump(
        frequencies,
        start_cpp=mid_start_cpp,
        peak_cpp=mid_peak_cpp,
        stop_cpp=mid_stop_cpp,
    ) - high_weight * cosine_bump(
        frequencies,
        start_cpp=high_start_cpp,
        peak_cpp=high_peak_cpp,
        stop_cpp=high_stop_cpp,
    )
    return np.exp((gain * gate) * correction_shape)


def apply_mtf_shape_correction(
    mtf: np.ndarray,
    frequencies_cpp: np.ndarray,
    *,
    mode: str = "none",
    high_frequency_noise_share: float | None = None,
    gain: float = 0.035,
    share_gate_lo: float = MTF_SHAPE_CORRECTION_SHARE_GATE[0],
    share_gate_hi: float = MTF_SHAPE_CORRECTION_SHARE_GATE[1],
    mid_start_cpp: float = 0.095,
    mid_peak_cpp: float = 0.145,
    mid_stop_cpp: float = 0.19,
    high_start_cpp: float = 0.36,
    high_peak_cpp: float = 0.40,
    high_stop_cpp: float = 0.49,
    high_weight: float = 0.25,
) -> tuple[np.ndarray, np.ndarray]:
    correction = estimate_mtf_shape_correction_curve(
        frequencies_cpp,
        mode=mode,
        high_frequency_noise_share=high_frequency_noise_share,
        gain=gain,
        share_gate_lo=share_gate_lo,
        share_gate_hi=share_gate_hi,
        mid_start_cpp=mid_start_cpp,
        mid_peak_cpp=mid_peak_cpp,
        mid_stop_cpp=mid_stop_cpp,
        high_start_cpp=high_start_cpp,
        high_peak_cpp=high_peak_cpp,
        high_stop_cpp=high_stop_cpp,
        high_weight=high_weight,
    )
    return np.asarray(mtf, dtype=np.float64) * correction, correction


def estimate_high_frequency_noise_share(
    frequencies_cpp: np.ndarray,
    psd_signal_plus_noise: np.ndarray,
    psd_noise: np.ndarray,
    *,
    band: tuple[float, float] = ACUTANCE_HF_NOISE_SHARE_BAND,
) -> float:
    frequencies = np.asarray(frequencies_cpp, dtype=np.float64)
    signal_plus_noise = np.asarray(psd_signal_plus_noise, dtype=np.float64)
    noise = np.asarray(psd_noise, dtype=np.float64)
    band_mask = (frequencies >= band[0]) & (frequencies <= band[1])
    if not np.any(band_mask):
        return 0.0
    return float(
        np.mean(noise[band_mask] / np.maximum(signal_plus_noise[band_mask], EPS))
    )


def estimate_acutance_noise_scale(
    frequencies_cpp: np.ndarray,
    psd_signal_plus_noise: np.ndarray,
    psd_noise: np.ndarray,
    *,
    model: str = "fixed",
    fixed_scale: float = 1.0,
    band: tuple[float, float] = ACUTANCE_HF_NOISE_SHARE_BAND,
    coefficients: tuple[float, float, float] = ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS,
    clip_range: tuple[float, float] = ACUTANCE_NOISE_SCALE_CLIP,
) -> tuple[float, float | None]:
    if model == "fixed":
        return float(fixed_scale), None
    if model != "high_frequency_noise_share_quadratic":
        raise ValueError(f"Unknown acutance noise scale model: {model}")

    noise_share = estimate_high_frequency_noise_share(
        frequencies_cpp,
        psd_signal_plus_noise,
        psd_noise,
        band=band,
    )
    scale = float(np.polyval(coefficients, noise_share))
    scale = float(np.clip(scale, clip_range[0], clip_range[1]))
    return scale, noise_share


def estimate_dead_leaves_mtf(
    image: np.ndarray,
    *,
    num_bins: int = 64,
    ideal_psd_mode: str = "quadratic_log",
    ideal_psd_calibration: IdealPsdCalibration | None = None,
    bin_centers: np.ndarray | None = None,
    roi_override: RoiBounds | None = None,
    normalization_band: tuple[float, float] = (0.01, 0.03),
    normalization_mode: str = "max",
    acutance_reference_band: tuple[float, float] = (0.017, 0.035),
    acutance_reference_mode: str = "mean",
    signal_psd_correction_gain: float = 0.0,
    signal_psd_correction_start_cpp: float = 0.08,
    signal_psd_correction_peak_cpp: float = 0.15,
    signal_psd_correction_stop_cpp: float = 0.22,
    noise_psd_model: str = "empirical",
    noise_psd_log_polynomial_degree: int = 2,
    noise_psd_scale: float = 1.0,
    noise_psd_scale_for_acutance: float | None = None,
    acutance_noise_scale_model: str = "fixed",
    acutance_noise_share_band: tuple[float, float] = ACUTANCE_HF_NOISE_SHARE_BAND,
    acutance_noise_share_scale_coefficients: tuple[float, float, float] = ACUTANCE_HF_NOISE_SHARE_SCALE_COEFFICIENTS,
    acutance_noise_scale_clip: tuple[float, float] = ACUTANCE_NOISE_SCALE_CLIP,
    high_frequency_guard_start_cpp: float | None = None,
    high_frequency_guard_stop_cpp: float = 0.5,
) -> SpectrumResult:
    roi = roi_override or detect_texture_roi(image)
    crop = extract_roi(image, roi)
    frequencies_cpp, psd_signal_plus_noise = radial_psd(
        crop,
        num_bins=num_bins,
        bin_centers=bin_centers,
    )
    base_psd_noise = estimate_noise_psd(
        image,
        roi,
        num_bins=num_bins,
        bin_centers=bin_centers,
        model=noise_psd_model,
        log_polynomial_degree=noise_psd_log_polynomial_degree,
    )
    psd_noise = np.asarray(base_psd_noise, dtype=np.float64) * float(noise_psd_scale)
    psd_signal = np.maximum(psd_signal_plus_noise - psd_noise, 0.0)
    acutance_noise_scale, acutance_high_frequency_noise_share = estimate_acutance_noise_scale(
        frequencies_cpp,
        psd_signal_plus_noise,
        np.asarray(base_psd_noise, dtype=np.float64),
        model=acutance_noise_scale_model,
        fixed_scale=(
            float(noise_psd_scale)
            if noise_psd_scale_for_acutance is None
            else float(noise_psd_scale_for_acutance)
        ),
        band=acutance_noise_share_band,
        coefficients=acutance_noise_share_scale_coefficients,
        clip_range=acutance_noise_scale_clip,
    )
    psd_signal_for_acutance = np.maximum(
        psd_signal_plus_noise - np.asarray(base_psd_noise, dtype=np.float64) * acutance_noise_scale,
        0.0,
    )
    psd_signal = apply_signal_psd_band_correction(
        psd_signal,
        frequencies_cpp,
        start_cpp=signal_psd_correction_start_cpp,
        peak_cpp=signal_psd_correction_peak_cpp,
        stop_cpp=signal_psd_correction_stop_cpp,
        gain=signal_psd_correction_gain,
    )
    psd_signal_for_acutance = apply_signal_psd_band_correction(
        psd_signal_for_acutance,
        frequencies_cpp,
        start_cpp=signal_psd_correction_start_cpp,
        peak_cpp=signal_psd_correction_peak_cpp,
        stop_cpp=signal_psd_correction_stop_cpp,
        gain=signal_psd_correction_gain,
    )
    psd_signal_for_acutance = apply_high_frequency_guard(
        psd_signal_for_acutance,
        frequencies_cpp,
        start_cpp=high_frequency_guard_start_cpp,
        stop_cpp=high_frequency_guard_stop_cpp,
    )
    ideal = ideal_dead_leaves_psd(
        frequencies_cpp,
        length_px=max(crop.shape),
        mode=ideal_psd_mode,
        calibration=ideal_psd_calibration,
    )
    mtf_with_noise_unnormalized = np.sqrt(
        np.maximum(psd_signal_plus_noise / np.maximum(ideal, EPS), 0.0)
    )
    mtf_unnormalized = np.sqrt(np.maximum(psd_signal / np.maximum(ideal, EPS), 0.0))
    mtf_for_acutance_unnormalized = np.sqrt(
        np.maximum(psd_signal_for_acutance / np.maximum(ideal, EPS), 0.0)
    )

    mtf = normalize_mtf_curve(
        mtf_unnormalized,
        frequencies_cpp,
        reference_band=normalization_band,
        reference_mode=normalization_mode,
    )
    mtf_with_noise = normalize_mtf_curve(
        mtf_with_noise_unnormalized,
        frequencies_cpp,
        reference_band=normalization_band,
        reference_mode=normalization_mode,
    )
    mtf_for_acutance = anchor_mtf_to_dc(
        mtf_for_acutance_unnormalized,
        frequencies_cpp,
        reference_band=acutance_reference_band,
        reference_mode=acutance_reference_mode,
    )
    metrics = compute_mtf_metrics(frequencies_cpp, mtf)

    return SpectrumResult(
        roi=roi,
        frequencies_cpp=frequencies_cpp,
        psd_signal_plus_noise=psd_signal_plus_noise,
        psd_noise=psd_noise,
        psd_signal=psd_signal,
        mtf_unnormalized=mtf_unnormalized,
        mtf_with_noise_unnormalized=mtf_with_noise_unnormalized,
        mtf_for_acutance=mtf_for_acutance,
        mtf=mtf,
        mtf_with_noise=mtf_with_noise,
        acutance_noise_scale=acutance_noise_scale,
        acutance_high_frequency_noise_share=acutance_high_frequency_noise_share,
        metrics=metrics,
    )


def acutance_from_mtf(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    picture_height_cm: float,
    viewing_distance_cm: float,
    pixels_along_picture_height: int,
    display_mtf_c50_cpd: float | None = None,
    display_mtf_model: str = "gaussian",
) -> float:
    angular_frequency = (
        np.pi
        * float(pixels_along_picture_height)
        * float(viewing_distance_cm)
        * np.asarray(frequencies_cpp, dtype=np.float64)
        / (180.0 * float(picture_height_cm))
    )
    effective_mtf = np.asarray(mtf, dtype=np.float64)
    if display_mtf_c50_cpd is not None:
        cutoff = max(display_mtf_c50_cpd, EPS)
        if display_mtf_model == "gaussian":
            display_mtf = np.exp(
                -math.log(2.0) * np.square(angular_frequency / cutoff)
            )
        elif display_mtf_model == "ideal_lowpass":
            display_mtf = np.where(angular_frequency <= cutoff, 1.0, 0.0)
        else:
            raise ValueError(f"Unknown display MTF model: {display_mtf_model}")
        effective_mtf = effective_mtf * display_mtf
    # Imatest documents acutance as the integral of MTF(v) * CSF(v) over
    # angular frequency, normalized by the full CSF integral from 0 to infinity.
    # The denominator must not be truncated at the camera Nyquist frequency,
    # otherwise small viewing distances are overstated.
    csf = (
        75.0
        * np.power(np.maximum(angular_frequency, 0.0), 0.8)
        * np.exp(-0.2 * angular_frequency)
        / 34.05
    )
    numerator = np.trapz(effective_mtf * csf, angular_frequency)
    denominator = (75.0 / 34.05) * math.gamma(1.8) / (0.2**1.8)
    return float(numerator / max(denominator, EPS))


def acutance_curve_from_mtf(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    picture_height_cm: float,
    viewing_distances_cm: Iterable[float],
    pixels_along_picture_height: int,
) -> list[AcutancePoint]:
    return [
        AcutancePoint(
            print_height_cm=float(picture_height_cm),
            viewing_distance_cm=float(distance_cm),
            acutance=acutance_from_mtf(
                frequencies_cpp,
                mtf,
                picture_height_cm=picture_height_cm,
                viewing_distance_cm=float(distance_cm),
                pixels_along_picture_height=pixels_along_picture_height,
            ),
        )
        for distance_cm in viewing_distances_cm
    ]


def acutance_presets_from_mtf(
    frequencies_cpp: np.ndarray,
    mtf: np.ndarray,
    *,
    pixels_along_picture_height: int,
    presets: Iterable[AcutancePreset] = DEFAULT_ACUTANCE_PRESETS,
) -> dict[str, float]:
    return {
        preset.name: acutance_from_mtf(
            frequencies_cpp,
            mtf,
            picture_height_cm=preset.picture_height_cm,
            viewing_distance_cm=preset.viewing_distance_cm,
            pixels_along_picture_height=pixels_along_picture_height,
            display_mtf_c50_cpd=preset.display_mtf_c50_cpd,
            display_mtf_model=preset.display_mtf_model,
        )
        for preset in presets
    }


def quality_loss_from_acutance(
    acutance: float,
    *,
    om_ceiling: float = 0.8851,
    coefficients: tuple[float, float, float] = QUALITY_LOSS_OM_COEFFICIENTS,
) -> float:
    objective_metric = max(0.0, float(om_ceiling) - float(acutance))
    a2, a1, a0 = coefficients
    return float(a2 * objective_metric * objective_metric + a1 * objective_metric + a0)


def quality_loss_presets_from_acutance(
    acutance_presets: dict[str, float],
    *,
    om_ceiling: float = 0.8851,
    coefficients: tuple[float, float, float] = QUALITY_LOSS_OM_COEFFICIENTS,
) -> dict[str, float]:
    return {
        name.replace("Acutance", "Quality Loss"): quality_loss_from_acutance(
            value,
            om_ceiling=om_ceiling,
            coefficients=coefficients,
        )
        for name, value in acutance_presets.items()
    }


def parse_imatest_random_csv(path: str | Path) -> ParsedImatestCsv:
    with Path(path).open("r", encoding="utf-8", errors="ignore") as handle:
        rows = list(csv.reader(handle))

    def find_row(prefix: str) -> list[str]:
        for row in rows:
            if row and row[0].strip().startswith(prefix):
                return row
        raise KeyError(f"Could not find row starting with {prefix!r} in {path}")

    def find_optional_row(prefix: str) -> list[str] | None:
        for row in rows:
            if row and row[0].strip().startswith(prefix):
                return row
        return None

    image_pixels_row = find_optional_row("Image pixels (WxH)")
    crop_row = find_row("Crop")
    lrtb_row = find_row("L R T B")
    gamma_row = find_optional_row("Gamma")
    color_channel_row = find_optional_row("Color channel")
    max_detected_f_row = find_optional_row("Max detected f (c/p)")

    table_start = next(
        idx for idx, row in enumerate(rows) if row and row[0].strip() == "f (c/p)"
    )
    table_rows: list[list[str]] = []
    for row in rows[table_start + 1 :]:
        if not row or not row[0].strip():
            break
        table_rows.append(row)

    frequencies = np.array([float(row[0]) for row in table_rows], dtype=np.float64)
    mtf = np.array([float(row[2]) for row in table_rows], dtype=np.float64)
    mtf_with_noise = np.array([float(row[3]) for row in table_rows], dtype=np.float64)
    noise_psd = np.array([float(row[4]) for row in table_rows], dtype=np.float64)
    signal_plus_noise_psd = np.array([float(row[5]) for row in table_rows], dtype=np.float64)
    signal_psd = np.array([float(row[6]) for row in table_rows], dtype=np.float64)

    acutance_table: list[AcutancePoint] = []
    acutance_header_idx = next(
        (
            idx
            for idx, row in enumerate(rows)
            if row
            and row[0].strip() == "Print height"
            and len(row) > 2
            and row[1].strip().startswith("Viewing dist")
        ),
        None,
    )
    if acutance_header_idx is not None:
        for row in rows[acutance_header_idx + 1 :]:
            if len(row) < 3 or not row[0].strip():
                break
            if not row[0].strip()[0].isdigit():
                break
            acutance_table.append(
                AcutancePoint(
                    print_height_cm=float(row[0]),
                    viewing_distance_cm=float(row[1]),
                    acutance=float(row[2]),
                )
            )

    use_unnormalized_mtf_for_acutance = any(
        row and row[0].strip() == "Use unnormalized MTF for Acutance calculation"
        for row in rows
    )

    reported_acutance = {}
    for key in [
        "Computer Monitor Acutance",
        '5.5" Phone Display Acutance',
        "UHDTV Display Acutance",
        "Small Print Acutance",
        "Large Print Acutance",
    ]:
        row = find_row(key)
        reported_acutance[key] = float(row[1])

    reported_quality_loss = {}
    for key in [
        "Computer Monitor Quality Loss",
        '5.5" Phone Display Quality Loss',
        "UHDTV Display Quality Loss",
        "Small Print Quality Loss",
        "Large Print Quality Loss",
    ]:
        row = find_row(key)
        reported_quality_loss[key] = float(row[1])

    left = int(float(lrtb_row[1]))
    right = int(float(lrtb_row[2]))
    top = int(float(lrtb_row[3]))
    bottom = int(float(lrtb_row[4]))

    return ParsedImatestCsv(
        image_shape=(
            int(float(image_pixels_row[1])),
            int(float(image_pixels_row[2])),
        )
        if image_pixels_row is not None
        else None,
        crop=(int(float(crop_row[1])), int(float(crop_row[2]))),
        lrtb=RoiBounds(left=left, right=right, top=top, bottom=bottom),
        report_gamma=float(gamma_row[1]) if gamma_row is not None else None,
        color_channel=color_channel_row[1].strip() if color_channel_row is not None else None,
        max_detected_frequency_cpp=(
            float(max_detected_f_row[1]) if max_detected_f_row is not None else None
        ),
        frequencies_cpp=frequencies,
        mtf=mtf,
        mtf_with_noise=mtf_with_noise,
        noise_psd=noise_psd,
        signal_plus_noise_psd=signal_plus_noise_psd,
        signal_psd=signal_psd,
        use_unnormalized_mtf_for_acutance=use_unnormalized_mtf_for_acutance,
        acutance_table=acutance_table,
        reported_acutance=reported_acutance,
        reported_quality_loss=reported_quality_loss,
    )


def compare_to_imatest(
    estimate: SpectrumResult,
    reference: ParsedImatestCsv,
) -> dict[str, float | tuple[int, int, int, int]]:
    return {
        "roi_estimate": (
            estimate.roi.left,
            estimate.roi.right,
            estimate.roi.top,
            estimate.roi.bottom,
        ),
        "roi_reference": (
            reference.lrtb.left,
            reference.lrtb.right,
            reference.lrtb.top,
            reference.lrtb.bottom,
        ),
        "mtf50_estimate": estimate.metrics.mtf50,
        "mtf50_reference": interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.5),
        "mtf30_estimate": estimate.metrics.mtf30,
        "mtf30_reference": interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.3),
        "mtf20_estimate": estimate.metrics.mtf20,
        "mtf20_reference": interpolate_threshold(reference.frequencies_cpp, reference.mtf, 0.2),
    }


def compare_acutance_curves(
    estimate: list[AcutancePoint],
    reference: list[AcutancePoint],
) -> dict[str, float | int]:
    ref_map = {
        (point.print_height_cm, point.viewing_distance_cm): point.acutance
        for point in reference
    }
    errors = []
    for point in estimate:
        key = (point.print_height_cm, point.viewing_distance_cm)
        if key not in ref_map:
            continue
        errors.append(abs(point.acutance - ref_map[key]))
    if not errors:
        return {"count": 0}
    return {
        "count": len(errors),
        "mae": float(np.mean(errors)),
        "max_error": float(np.max(errors)),
    }


def compare_acutance_presets(
    estimate: dict[str, float],
    reference: dict[str, float],
) -> dict[str, dict[str, float]]:
    comparison: dict[str, dict[str, float]] = {}
    for key, ref_value in reference.items():
        if key not in estimate:
            continue
        comparison[key] = {
            "estimate": float(estimate[key]),
            "reference": float(ref_value),
            "abs_error": abs(float(estimate[key]) - float(ref_value)),
        }
    return comparison
