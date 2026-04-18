from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 124
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 118
CURRENT_BEST_PR = 119
BASELINE_PR = 30
SUMMARY_KIND = "issue124_curve_only_high_mixup_ori_summary"
CANDIDATE_LABEL = "issue124_curve_only_high_mixup_ori_candidate"
RESULT_KIND = "positive_partial_not_promotable"
README_GATES = {
    "curve_mae_mean": 0.020,
    "focus_preset_acutance_mae_mean": 0.030,
    "overall_quality_loss_mae_mean": 1.30,
    "non_phone_acutance_preset_mae_max": 0.030,
    '5.5" Phone Display Acutance': 0.050,
}
PHONE_PRESET = '5.5" Phone Display Acutance'
HIGH_MIXUP_KEYS = ("0.8", "ori")
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build issue-124 curve-only summary.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue120-summary",
        type=Path,
        default=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
    )
    parser.add_argument(
        "--issue122-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue120_next_slice_benchmark.json"),
    )
    parser.add_argument(
        "--candidate-acutance",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_acutance_benchmark.json"),
    )
    parser.add_argument(
        "--candidate-psd",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_psd_benchmark.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue124_curve_only_high_mixup_ori_summary.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_single_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profiles = payload["profiles"]
    if len(profiles) != 1:
        raise ValueError(f"Expected exactly one profile, found {len(profiles)}")
    return profiles[0]


def readme_gate_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    acutance = metrics["acutance_preset_mae"]
    non_phone = {key: value for key, value in acutance.items() if key != PHONE_PRESET}
    worst_preset, worst_value = max(non_phone.items(), key=lambda item: item[1])
    gates = {
        "curve_mae_mean": gate(metrics["curve_mae_mean"], README_GATES["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": gate(
            metrics["acutance_focus_preset_mae_mean"],
            README_GATES["focus_preset_acutance_mae_mean"],
        ),
        "overall_quality_loss_mae_mean": gate(
            metrics["overall_quality_loss_mae_mean"],
            README_GATES["overall_quality_loss_mae_mean"],
        ),
        "non_phone_acutance_preset_mae_max": {
            **gate(worst_value, README_GATES["non_phone_acutance_preset_mae_max"]),
            "worst_preset": worst_preset,
            "by_preset": {key: float(value) for key, value in sorted(non_phone.items())},
        },
        PHONE_PRESET: gate(acutance[PHONE_PRESET], README_GATES[PHONE_PRESET]),
    }
    return {
        "all_readme_gates_pass": all(row["pass"] for row in gates.values()),
        "failed_gates": [name for name, row in gates.items() if not row["pass"]],
        "gates": gates,
    }


def gate(value: float, threshold: float) -> dict[str, Any]:
    value = float(value)
    return {
        "value": value,
        "threshold": threshold,
        "operator": "<=",
        "pass": value <= threshold,
        "delta_to_gate": value - threshold,
    }


def metric_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["acutance_focus_preset_mae_mean"]
            - baseline["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            candidate["overall_quality_loss_mae_mean"]
            - baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in candidate["mtf_threshold_mae"]
        },
        "acutance_preset_mae": {
            key: float(
                candidate["acutance_preset_mae"][key] - baseline["acutance_preset_mae"][key]
            )
            for key in candidate["acutance_preset_mae"]
        },
    }


def is_close(left: float, right: float, *, tolerance: float = 1e-12) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def collect_candidate_metrics(
    *,
    candidate_acutance: dict[str, Any],
    candidate_psd: dict[str, Any],
) -> dict[str, Any]:
    acutance_overall = candidate_acutance["overall"]
    psd_overall = candidate_psd["overall"]
    return {
        "curve_mae_mean": float(acutance_overall["curve_mae_mean"]),
        "acutance_focus_preset_mae_mean": float(
            acutance_overall["acutance_focus_preset_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            acutance_overall["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(psd_overall["mtf_abs_signed_rel_mean"]),
        "mtf_threshold_mae": {
            key: float(value) for key, value in psd_overall["mtf_threshold_mae"].items()
        },
        "acutance_preset_mae": {
            key: float(value) for key, value in acutance_overall["acutance_preset_mae"].items()
        },
        "quality_loss_preset_mae": {
            key: float(value)
            for key, value in acutance_overall["quality_loss_preset_mae"].items()
        },
    }


def build_payload(
    repo_root: Path,
    *,
    issue120_summary_path: Path,
    issue122_summary_path: Path,
    candidate_acutance_path: Path,
    candidate_psd_path: Path,
) -> dict[str, Any]:
    issue120 = load_json(resolve_path(repo_root, issue120_summary_path))
    issue122 = load_json(resolve_path(repo_root, issue122_summary_path))
    candidate_acutance = select_single_profile(load_json(resolve_path(repo_root, candidate_acutance_path)))
    candidate_psd = select_single_profile(load_json(resolve_path(repo_root, candidate_psd_path)))
    current_best = issue120["current_best"]
    pr30 = issue120["baseline"]
    baseline_metrics = current_best["metrics"]
    candidate_metrics = collect_candidate_metrics(
        candidate_acutance=candidate_acutance,
        candidate_psd=candidate_psd,
    )
    gate_summary = readme_gate_summary(candidate_metrics)
    candidate_vs_pr119 = metric_delta(candidate_metrics, baseline_metrics)
    candidate_vs_pr30 = metric_delta(candidate_metrics, pr30["metrics"])
    by_mixup_before = issue122["residual_curve_evidence"]["by_mixup"]
    by_mixup_after = candidate_acutance["by_mixup_curve_mae_mean"]
    by_mixup_delta = {
        key: float(by_mixup_after[key] - by_mixup_before[key]["current_best_curve_mae"])
        for key in by_mixup_after
    }
    high_mixup_after_weighted = sum(
        by_mixup_after[key] * by_mixup_before[key]["record_fraction"]
        for key in HIGH_MIXUP_KEYS
    )
    weighted_curve_after = sum(
        by_mixup_after[key] * by_mixup_before[key]["record_fraction"]
        for key in by_mixup_after
    )
    candidate_path = candidate_acutance["profile_path"]
    source_artifacts = [
        str(candidate_acutance_path),
        str(candidate_psd_path),
        str(issue120_summary_path),
        str(issue122_summary_path),
    ]
    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "result_kind": RESULT_KIND,
        "candidate": {
            "label": CANDIDATE_LABEL,
            "profile_path": candidate_path,
            "curve_only_acutance_anchor_mixups": list(HIGH_MIXUP_KEYS),
            "source_artifacts": source_artifacts,
            "metrics": candidate_metrics,
        },
        "baseline_current_best": current_best,
        "baseline_pr30": pr30,
        "readme_gate_summary": gate_summary,
        "comparisons": {
            "candidate_vs_pr119": {"delta": candidate_vs_pr119},
            "candidate_vs_pr30": {"delta": candidate_vs_pr30},
        },
        "curve_tail_result": {
            "selected_mixups": list(HIGH_MIXUP_KEYS),
            "by_mixup_before": {
                key: float(row["current_best_curve_mae"])
                for key, row in sorted(by_mixup_before.items())
            },
            "by_mixup_after": {key: float(value) for key, value in sorted(by_mixup_after.items())},
            "by_mixup_delta": {key: float(value) for key, value in sorted(by_mixup_delta.items())},
            "high_mixup_weighted_curve_mae_after": float(high_mixup_after_weighted),
            "weighted_curve_mae_after": float(weighted_curve_after),
            "weighted_curve_mae_matches_candidate": is_close(
                weighted_curve_after,
                candidate_metrics["curve_mae_mean"],
            ),
        },
        "acceptance": {
            "curve_mae_reduced_vs_pr119": candidate_vs_pr119["curve_mae_mean"] < 0.0,
            "reported_mtf_preserved": (
                is_close(candidate_vs_pr119["mtf_abs_signed_rel_mean"], 0.0)
                and all(
                    is_close(value, 0.0)
                    for value in candidate_vs_pr119["mtf_threshold_mae"].values()
                )
            ),
            "overall_quality_loss_preserved": is_close(
                candidate_vs_pr119["overall_quality_loss_mae_mean"],
                0.0,
            ),
            "focus_preset_acutance_gate_pass": gate_summary["gates"][
                "focus_preset_acutance_mae_mean"
            ]["pass"],
            "small_print_acutance_preserved": is_close(
                candidate_vs_pr119["acutance_preset_mae"]["Small Print Acutance"],
                0.0,
            ),
            "all_readme_gates_pass": gate_summary["all_readme_gates_pass"],
        },
        "next_result": {
            "summary": (
                "The high-mixup/ori curve-only anchor is a positive partial result: it "
                "materially lowers curve MAE while preserving reported-MTF, preset "
                "Acutance, and Quality Loss, but the README curve gate still misses."
            ),
            "remaining_misses": gate_summary["failed_gates"],
            "recommended_follow_up": (
                "Do not broaden this issue into Small Print preset work. If PM splits "
                "another engineering pass, target the remaining curve residual now "
                "visible in `ori`, `0.15`, and `0.25`, while preserving the issue #124 "
                "curve-only isolation."
            ),
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "The candidate profile is canonical-target research only.",
                "No fitted outputs are written under golden/reference data roots.",
                "No release-facing config is promoted in this issue.",
            ],
        },
        "refs": {
            "umbrella_issue": UMBRELLA_ISSUE,
            "current_issue": ISSUE,
            "current_best_issue": CURRENT_BEST_ISSUE,
            "current_best_pr": CURRENT_BEST_PR,
            "baseline_pr": BASELINE_PR,
        },
    }
    assert_storage_separation(payload)
    return payload


def assert_storage_separation(payload: dict[str, Any]) -> None:
    paths = [payload["candidate"]["profile_path"], *payload["candidate"]["source_artifacts"]]
    for path in paths:
        if path.startswith(GOLDEN_REFERENCE_ROOTS):
            raise ValueError(f"candidate path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    metrics = payload["candidate"]["metrics"]
    pr119 = payload["baseline_current_best"]["metrics"]
    delta = payload["comparisons"]["candidate_vs_pr119"]["delta"]
    gates = payload["readme_gate_summary"]["gates"]
    curve_tail = payload["curve_tail_result"]
    return "\n".join(
        [
            "# Issue 124 Curve-Only High-Mixup/Ori Summary",
            "",
            f"- Result: `{payload['result_kind']}`.",
            f"- Candidate profile: `{payload['candidate']['profile_path']}`",
            "- Scoped boundary: only the main Acutance curve is anchored for mixups "
            "`0.8` and `ori`; preset Acutance, Quality Loss, and reported-MTF/readout "
            "paths stay unchanged.",
            "",
            "## Metrics",
            "",
            "| Metric | PR #119 | Issue #124 | Delta | Gate |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(pr119['curve_mae_mean'])} | "
            f"{format_metric(metrics['curve_mae_mean'])} | "
            f"{format_metric(delta['curve_mae_mean'])} | "
            f"<= 0.020 ({'pass' if gates['curve_mae_mean']['pass'] else 'miss'}) |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(pr119['focus_preset_acutance_mae_mean'])} | "
            f"{format_metric(metrics['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(delta['focus_preset_acutance_mae_mean'])} | "
            f"<= 0.030 ({'pass' if gates['focus_preset_acutance_mae_mean']['pass'] else 'miss'}) |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(pr119['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(metrics['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(delta['overall_quality_loss_mae_mean'])} | "
            f"<= 1.30 ({'pass' if gates['overall_quality_loss_mae_mean']['pass'] else 'miss'}) |",
            f"| mtf_abs_signed_rel_mean | {format_metric(pr119['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(metrics['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(delta['mtf_abs_signed_rel_mean'])} | preserve |",
            f"| Small Print Acutance | "
            f"{format_metric(pr119['acutance_preset_mae']['Small Print Acutance'])} | "
            f"{format_metric(metrics['acutance_preset_mae']['Small Print Acutance'])} | "
            f"{format_metric(delta['acutance_preset_mae']['Small Print Acutance'])} | "
            f"<= 0.030 ({'pass' if gates['non_phone_acutance_preset_mae_max']['pass'] else 'miss'}) |",
            "",
            "## Curve Tail",
            "",
            "| Mixup | Before | After | Delta |",
            "| --- | ---: | ---: | ---: |",
            *[
                f"| {key} | {format_metric(curve_tail['by_mixup_before'][key])} | "
                f"{format_metric(curve_tail['by_mixup_after'][key])} | "
                f"{format_metric(curve_tail['by_mixup_delta'][key])} |"
                for key in sorted(curve_tail["by_mixup_after"])
            ],
            "",
            "The selected high-mixup/ori intervention reduces `0.8` and `ori` curve error, "
            "but the remaining README curve miss is now spread across `ori`, `0.15`, "
            "and `0.25` rather than being solved by this slice alone.",
            "",
            "## Acceptance",
            "",
            f"- Curve MAE reduced versus PR #119: `{payload['acceptance']['curve_mae_reduced_vs_pr119']}`.",
            f"- Reported-MTF preserved: `{payload['acceptance']['reported_mtf_preserved']}`.",
            f"- Overall Quality Loss preserved: `{payload['acceptance']['overall_quality_loss_preserved']}`.",
            f"- Small Print Acutance preserved: `{payload['acceptance']['small_print_acutance_preserved']}`.",
            f"- All README gates pass: `{payload['acceptance']['all_readme_gates_pass']}`.",
            "",
            "## Next Result",
            "",
            payload["next_result"]["summary"],
            "",
            payload["next_result"]["recommended_follow_up"],
            "",
            "## Release Separation",
            "",
            "This remains canonical-target research, not a release-facing config promotion. "
            "No fitted outputs are written under golden/reference data roots or release configs.",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = args.repo_root
    payload = build_payload(
        repo_root,
        issue120_summary_path=args.issue120_summary,
        issue122_summary_path=args.issue122_summary,
        candidate_acutance_path=args.candidate_acutance,
        candidate_psd_path=args.candidate_psd,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
