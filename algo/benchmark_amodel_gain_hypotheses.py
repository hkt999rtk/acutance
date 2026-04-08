from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_amodel_gain_trend import analyze_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare A-model gain-trend hypotheses against a baseline release profile."
    )
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("baseline_profile", type=Path)
    parser.add_argument("hypothesis_profiles", nargs="+", type=Path)
    parser.add_argument("--width", type=int, default=4032)
    parser.add_argument("--height", type=int, default=3024)
    parser.add_argument("--flat-epsilon", type=float, default=0.002)
    parser.add_argument("--output", type=Path)
    return parser


def summarize_against_baseline(
    baseline: dict[str, object], hypothesis: dict[str, object]
) -> dict[str, object]:
    baseline_summary = baseline["summary"]
    hypothesis_summary = hypothesis["summary"]
    baseline_presets = baseline["presets"]
    hypothesis_presets = hypothesis["presets"]

    comparison_presets: dict[str, object] = {}
    for preset_name, baseline_preset in baseline_presets.items():
        hypothesis_preset = hypothesis_presets[preset_name]
        comparison_presets[preset_name] = {
            "reported_mean_gain_delta": baseline_preset["reported_mean_gain_delta"],
            "baseline_predicted_mean_gain_delta": baseline_preset["predicted_mean_gain_delta"],
            "hypothesis_predicted_mean_gain_delta": hypothesis_preset["predicted_mean_gain_delta"],
            "predicted_mean_gain_delta_delta": (
                hypothesis_preset["predicted_mean_gain_delta"]
                - baseline_preset["predicted_mean_gain_delta"]
            ),
            "gain_delta_mae_delta": (
                hypothesis_preset["gain_delta_mae_mean"] - baseline_preset["gain_delta_mae_mean"]
            ),
            "gain_delta_mae_improvement": (
                baseline_preset["gain_delta_mae_mean"] - hypothesis_preset["gain_delta_mae_mean"]
            ),
            "series_mae_delta": (
                hypothesis_preset["series_mae_mean"] - baseline_preset["series_mae_mean"]
            ),
            "series_mae_improvement": (
                baseline_preset["series_mae_mean"] - hypothesis_preset["series_mae_mean"]
            ),
            "direction_match_delta": (
                hypothesis_preset["direction_match_count"] - baseline_preset["direction_match_count"]
            ),
            "direction_group_count": hypothesis_preset["direction_group_count"],
        }

    return {
        "focus_preset_gain_delta_mae_delta": (
            hypothesis_summary["focus_preset_gain_delta_mae_mean"]
            - baseline_summary["focus_preset_gain_delta_mae_mean"]
        ),
        "focus_preset_gain_delta_mae_improvement": (
            baseline_summary["focus_preset_gain_delta_mae_mean"]
            - hypothesis_summary["focus_preset_gain_delta_mae_mean"]
        ),
        "focus_preset_series_mae_delta": (
            hypothesis_summary["focus_preset_series_mae_mean"]
            - baseline_summary["focus_preset_series_mae_mean"]
        ),
        "focus_preset_series_mae_improvement": (
            baseline_summary["focus_preset_series_mae_mean"]
            - hypothesis_summary["focus_preset_series_mae_mean"]
        ),
        "focus_preset_direction_match_delta": (
            hypothesis_summary["focus_preset_direction_match_count"]
            - baseline_summary["focus_preset_direction_match_count"]
        ),
        "focus_preset_direction_group_count": hypothesis_summary[
            "focus_preset_direction_group_count"
        ],
        "presets": comparison_presets,
    }


def main() -> int:
    args = build_parser().parse_args()
    baseline = analyze_profile(
        dataset_root=args.dataset_root,
        profile_path=args.baseline_profile,
        width=args.width,
        height=args.height,
        flat_epsilon=args.flat_epsilon,
    )
    hypotheses = []
    for path in args.hypothesis_profiles:
        profile = analyze_profile(
            dataset_root=args.dataset_root,
            profile_path=path,
            width=args.width,
            height=args.height,
            flat_epsilon=args.flat_epsilon,
        )
        hypotheses.append(
            {
                **profile,
                "comparison_vs_baseline": summarize_against_baseline(baseline, profile),
            }
        )

    payload = {
        "dataset_root": str(args.dataset_root),
        "flat_epsilon": args.flat_epsilon,
        "baseline": baseline,
        "hypotheses": hypotheses,
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
