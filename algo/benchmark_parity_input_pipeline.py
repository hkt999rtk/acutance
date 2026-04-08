from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys


MTF_BANDS = ("low", "mid", "high", "top")


@dataclass(frozen=True)
class Candidate:
    name: str
    bayer_mode: str
    bayer_pattern: str
    parity_valid: bool
    rationale: str


DEFAULT_CANDIDATES = (
    Candidate(
        name="gray",
        bayer_mode="gray",
        bayer_pattern="RGGB",
        parity_valid=False,
        rationale="Diagnostic grayscale control; kept to show why a non-R path should not be used for parity fitting.",
    ),
    Candidate(
        name="demosaic_red",
        bayer_mode="demosaic_red",
        bayer_pattern="RGGB",
        parity_valid=True,
        rationale="Current release/workaround R-channel path from full Bayer demosaic, then red-plane extraction.",
    ),
    Candidate(
        name="raw_red_upsampled",
        bayer_mode="raw_red_upsampled",
        bayer_pattern="RGGB",
        parity_valid=True,
        rationale="R-only raw subsampling path with bilinear upsampling back to full image size.",
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark parity input-pipeline candidates against golden-sample outputs."
    )
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--calibration-file", type=Path, required=True)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument(
        "--analysis-gamma",
        type=float,
        default=1.0,
        help="Analysis-domain gamma held fixed while comparing input-pipeline candidates.",
    )
    parser.add_argument(
        "--roi-source",
        choices=["fixed", "reference"],
        default="fixed",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. When omitted, the benchmark JSON is printed to stdout.",
    )
    return parser


def run_module(module: str, *, candidate: Candidate, args: argparse.Namespace) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        module,
        str(args.dataset_root),
        "--calibration-file",
        str(args.calibration_file),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--gamma",
        str(args.analysis_gamma),
        "--bayer-pattern",
        candidate.bayer_pattern,
        "--bayer-mode",
        candidate.bayer_mode,
        "--roi-source",
        args.roi_source,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    payload["command"] = command
    return payload


def mean_abs_signed_rel(mtf_payload: dict[str, object]) -> float:
    bands = mtf_payload["overall"]["bands"]["mtf"]
    values = [abs(float(bands[band]["signed_rel_mean"])) for band in MTF_BANDS]
    return sum(values) / len(values)


def mean_named_metrics(values: dict[str, float], names: tuple[str, ...]) -> float:
    rows = [float(values[name]) for name in names]
    return sum(rows) / len(rows)


def selection_tuple(result: dict[str, object]) -> tuple[float, float, float]:
    return (
        float(result["curve_mae_mean"]),
        float(result["mtf_abs_signed_rel_mean"]),
        float(result["overall_quality_loss_mae_mean"]),
    )


def benchmark_candidate(candidate: Candidate, args: argparse.Namespace) -> dict[str, object]:
    acutance = run_module("algo.calibrate_acutance", candidate=candidate, args=args)
    quality_loss = run_module("algo.calibrate_quality_loss", candidate=candidate, args=args)
    mtf = run_module("algo.analyze_mtf_residuals", candidate=candidate, args=args)

    acutance_presets = acutance["overall"]["preset_mae"]
    quality_loss_presets = quality_loss["overall"]["preset_mae"]
    acutance_focus_presets = (
        "Computer Monitor Acutance",
        "UHDTV Display Acutance",
        "Small Print Acutance",
        "Large Print Acutance",
    )
    quality_loss_focus_presets = (
        "Computer Monitor Quality Loss",
        "UHDTV Display Quality Loss",
        "Small Print Quality Loss",
        "Large Print Quality Loss",
    )

    return {
        "candidate": asdict(candidate),
        "curve_mae_mean": float(acutance["overall"]["curve_mae_mean"]),
        "curve_max_error_mean": float(acutance["overall"]["curve_max_error_mean"]),
        "acutance_focus_preset_mae_mean": mean_named_metrics(
            acutance_presets, acutance_focus_presets
        ),
        "overall_quality_loss_mae_mean": float(quality_loss["overall"]["overall_mae_mean"]),
        "quality_loss_focus_preset_mae_mean": mean_named_metrics(
            quality_loss_presets, quality_loss_focus_presets
        ),
        "mtf_abs_signed_rel_mean": mean_abs_signed_rel(mtf),
        "mtf_signed_rel_mean": {
            band: float(mtf["overall"]["bands"]["mtf"][band]["signed_rel_mean"])
            for band in MTF_BANDS
        },
        "acutance": acutance,
        "quality_loss": quality_loss,
        "mtf": mtf,
    }


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    results = [benchmark_candidate(candidate, args) for candidate in DEFAULT_CANDIDATES]
    parity_candidates = [item for item in results if item["candidate"]["parity_valid"]]
    recommended = min(parity_candidates, key=selection_tuple)
    ranked = sorted(parity_candidates, key=selection_tuple)
    return {
        "observable_target_context": {
            "report_gamma": 0.5,
            "report_color_channel": "R",
            "analysis_gamma_is_latent": True,
        },
        "comparison_frame": {
            "dataset_root": str(args.dataset_root),
            "calibration_file": str(args.calibration_file),
            "width": args.width,
            "height": args.height,
            "analysis_gamma": args.analysis_gamma,
            "roi_source": args.roi_source,
            "fixed_bayer_pattern": "RGGB",
            "selection_rule": [
                "Rank only parity-valid R-channel candidates.",
                "Lower curve_mae_mean wins.",
                "Use mean absolute band-wise MTF signed relative error as tie-break 1.",
                "Use overall_quality_loss_mae_mean as tie-break 2.",
                "Keep gray only as a diagnostic non-parity control.",
            ],
        },
        "results": results,
        "ranked_parity_candidates": [
            {
                "name": item["candidate"]["name"],
                "selection_tuple": list(selection_tuple(item)),
            }
            for item in ranked
        ],
        "recommended_candidate": {
            "name": recommended["candidate"]["name"],
            "selection_tuple": list(selection_tuple(recommended)),
            "reason": "Best parity-valid candidate under the current analysis frame.",
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    payload = build_payload(args)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
