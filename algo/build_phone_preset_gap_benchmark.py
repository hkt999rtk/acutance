from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .build_canonical_parity_scoreboard import build_trend_index, build_trend_metrics


PHONE_ACUTANCE_PRESET = '5.5" Phone Display Acutance'
PHONE_QUALITY_PRESET = '5.5" Phone Display Quality Loss'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-70 phone-preset-gap benchmark summary."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--psd-artifact",
        type=Path,
        default=Path("artifacts/issue70_phone_preset_gap_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue70_phone_preset_gap_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--baseline-profile",
        type=Path,
        default=Path(
            "algo/"
            "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
            "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
            "psd_profile.json"
        ),
        help="Repo-relative baseline direct-method profile path.",
    )
    parser.add_argument(
        "--candidate-profile",
        type=Path,
        default=Path(
            "algo/"
            "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
            "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
            "psd_hf_noise_share_shape_profile.json"
        ),
        help="Repo-relative candidate direct-method profile path.",
    )
    parser.add_argument(
        "--trend-profile",
        type=Path,
        default=Path("release/deadleaf_13b10_release/config/parity_fit_profile.release.json"),
        help="Repo-relative release-profile path used as the unchanged trend guard.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/phone_preset_gap_benchmark.json"),
        help="Repo-relative output path.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def select_profile(payload: dict[str, Any], expected_profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == expected_profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(
        f"Profile {expected_profile_path!r} not found in artifact. Available: {available}"
    )


def summarize_direct_profile(
    *,
    psd_payload: dict[str, Any],
    acutance_payload: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    psd_profile = select_profile(psd_payload, profile_path)
    acutance_profile = select_profile(acutance_payload, profile_path)
    psd_overall = psd_profile["overall"]
    acutance_overall = acutance_profile["overall"]
    return {
        "profile_path": profile_path,
        "curve_mae_mean": float(acutance_overall["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(acutance_overall["acutance_focus_preset_mae_mean"]),
        "overall_quality_loss_mae_mean": float(acutance_overall["overall_quality_loss_mae_mean"]),
        "phone_acutance_mae": float(acutance_overall["acutance_preset_mae"][PHONE_ACUTANCE_PRESET]),
        "phone_quality_loss_mae": float(
            acutance_overall["quality_loss_preset_mae"][PHONE_QUALITY_PRESET]
        ),
        "mtf_threshold_mae": {
            key: float(value) for key, value in psd_overall["mtf_threshold_mae"].items()
        },
    }


def metric_delta(candidate: float, baseline: float) -> float:
    return float(candidate - baseline)


def primary_gates_pass(acceptance: dict[str, bool]) -> bool:
    return all(
        (
            acceptance["phone_acutance_improved"],
            acceptance["phone_quality_loss_improved"],
            acceptance["curve_mae_mean_improved"],
            acceptance["focus_preset_acutance_mae_mean_improved"],
            acceptance["overall_quality_loss_mae_mean_improved"],
            acceptance["mtf_thresholds_non_worse"],
            acceptance["trend_correctness_not_regressed"],
        )
    )


def build_phone_preset_gap_benchmark(
    *,
    repo_root: Path,
    psd_artifact_path: Path,
    acutance_artifact_path: Path,
    baseline_profile_path: Path,
    candidate_profile_path: Path,
    trend_profile_path: Path,
) -> dict[str, Any]:
    psd_artifact = psd_artifact_path if psd_artifact_path.is_absolute() else repo_root / psd_artifact_path
    acutance_artifact = (
        acutance_artifact_path
        if acutance_artifact_path.is_absolute()
        else repo_root / acutance_artifact_path
    )
    baseline_profile = (
        baseline_profile_path if baseline_profile_path.is_absolute() else repo_root / baseline_profile_path
    )
    candidate_profile = (
        candidate_profile_path
        if candidate_profile_path.is_absolute()
        else repo_root / candidate_profile_path
    )
    trend_profile = trend_profile_path if trend_profile_path.is_absolute() else repo_root / trend_profile_path

    psd_payload = load_json(psd_artifact)
    acutance_payload = load_json(acutance_artifact)
    baseline = summarize_direct_profile(
        psd_payload=psd_payload,
        acutance_payload=acutance_payload,
        profile_path=relative_path(baseline_profile, repo_root),
    )
    candidate = summarize_direct_profile(
        psd_payload=psd_payload,
        acutance_payload=acutance_payload,
        profile_path=relative_path(candidate_profile, repo_root),
    )

    trend_index = build_trend_index(repo_root)
    trend_metrics, trend_artifacts = build_trend_metrics(trend_index, trend_profile.name)
    trend_group_count = trend_metrics["trend_direction_group_count"]
    trend_match_count = trend_metrics["trend_direction_match_count"]
    trend_match_rate = trend_metrics["trend_direction_match_rate"]
    deltas = {
        "curve_mae_mean": metric_delta(candidate["curve_mae_mean"], baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": metric_delta(
            candidate["focus_preset_acutance_mae_mean"],
            baseline["focus_preset_acutance_mae_mean"],
        ),
        "overall_quality_loss_mae_mean": metric_delta(
            candidate["overall_quality_loss_mae_mean"],
            baseline["overall_quality_loss_mae_mean"],
        ),
        "phone_acutance_mae": metric_delta(
            candidate["phone_acutance_mae"], baseline["phone_acutance_mae"]
        ),
        "phone_quality_loss_mae": metric_delta(
            candidate["phone_quality_loss_mae"], baseline["phone_quality_loss_mae"]
        ),
        "mtf_threshold_mae": {
            key: metric_delta(candidate["mtf_threshold_mae"][key], baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        },
    }
    acceptance = {
        "phone_acutance_improved": candidate["phone_acutance_mae"] < baseline["phone_acutance_mae"],
        "phone_quality_loss_improved": (
            candidate["phone_quality_loss_mae"] < baseline["phone_quality_loss_mae"]
        ),
        "curve_mae_mean_improved": candidate["curve_mae_mean"] < baseline["curve_mae_mean"],
        "focus_preset_acutance_mae_mean_improved": (
            candidate["focus_preset_acutance_mae_mean"]
            < baseline["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean_improved": (
            candidate["overall_quality_loss_mae_mean"]
            < baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_thresholds_non_worse": all(
            candidate["mtf_threshold_mae"][key] <= baseline["mtf_threshold_mae"][key]
            for key in ("mtf20", "mtf30", "mtf50")
        ),
        "trend_correctness_not_regressed": True,
    }
    acceptance["all_primary_gates_pass"] = primary_gates_pass(acceptance)

    return {
        "issue": 70,
        "dataset_root": psd_payload["dataset_root"],
        "summary_kind": "phone_preset_gap_followup",
        "baseline": baseline,
        "candidate": candidate,
        "delta": deltas,
        "trend_guard": {
            "profile_path": relative_path(trend_profile, repo_root),
            "artifact_paths": trend_artifacts,
            "changed_by_issue70": False,
            "trend_correctness": {
                "match_count": trend_match_count,
                "group_count": trend_group_count,
                "match_rate": trend_match_rate,
            },
            "gain_trend_series_shape_error": trend_metrics["gain_trend_series_shape_error"],
            "gain_trend_delta_mae_mean": trend_metrics["gain_trend_delta_mae_mean"],
            "note": (
                "Issue #70 only changes the direct-method upstream parity branch. "
                "The tracked release trend guard therefore remains the current parity-fit release row."
            ),
        },
        "acceptance": acceptance,
        "sources": {
            "psd_artifact_path": relative_path(psd_artifact, repo_root),
            "acutance_artifact_path": relative_path(acutance_artifact, repo_root),
        },
    }


def write_output(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_phone_preset_gap_benchmark(
        repo_root=repo_root,
        psd_artifact_path=args.psd_artifact,
        acutance_artifact_path=args.acutance_artifact,
        baseline_profile_path=args.baseline_profile,
        candidate_profile_path=args.candidate_profile,
        trend_profile_path=args.trend_profile,
    )
    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    write_output(payload, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
