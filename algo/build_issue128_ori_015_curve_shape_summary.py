from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 128
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 124
CURRENT_BEST_PR = 125
DISCOVERY_ISSUE = 126
DISCOVERY_PR = 127
BASELINE_PR = 30
SUMMARY_KIND = "issue128_ori_015_curve_shape_summary"
RESULT_KIND = "bounded_negative_not_promotable"
TARGET_MIXUPS = ("ori", "0.15")
DEFERRED_MIXUPS = ("0.25",)
CURVE_GATE = 0.020
FOCUS_PRESET_GATE = 0.030
QUALITY_LOSS_GATE = 1.30
NON_PHONE_ACUTANCE_GATE = 0.030
PHONE_PRESET = '5.5" Phone Display Acutance'
SMALL_PRINT_PRESET = "Small Print Acutance"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build issue-128 curve-shape summary.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue124-summary",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
    )
    parser.add_argument(
        "--issue126-discovery",
        type=Path,
        default=Path("artifacts/issue126_residual_curve_discovery.json"),
    )
    parser.add_argument(
        "--candidate-acutance",
        type=Path,
        default=Path("artifacts/issue128_ori_015_curve_shape_acutance_benchmark.json"),
    )
    parser.add_argument(
        "--candidate-psd",
        type=Path,
        default=Path("artifacts/issue128_ori_015_curve_shape_psd_benchmark.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue128_ori_015_curve_shape_summary.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_single_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profiles = payload["profiles"]
    if len(profiles) != 1:
        raise ValueError(f"Expected one profile, found {len(profiles)}")
    return profiles[0]


def gate(value: float, threshold: float) -> dict[str, Any]:
    value = float(value)
    return {
        "value": value,
        "threshold": threshold,
        "operator": "<=",
        "pass": value <= threshold,
        "delta_to_gate": value - threshold,
    }


def readme_gate_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    non_phone = {
        key: value for key, value in metrics["acutance_preset_mae"].items() if key != PHONE_PRESET
    }
    worst_preset, worst_value = max(non_phone.items(), key=lambda item: item[1])
    gates = {
        "curve_mae_mean": gate(metrics["curve_mae_mean"], CURVE_GATE),
        "focus_preset_acutance_mae_mean": gate(
            metrics["acutance_focus_preset_mae_mean"],
            FOCUS_PRESET_GATE,
        ),
        "overall_quality_loss_mae_mean": gate(
            metrics["overall_quality_loss_mae_mean"],
            QUALITY_LOSS_GATE,
        ),
        "non_phone_acutance_preset_mae_max": {
            **gate(worst_value, NON_PHONE_ACUTANCE_GATE),
            "worst_preset": worst_preset,
            "by_preset": {key: float(value) for key, value in sorted(non_phone.items())},
        },
        PHONE_PRESET: gate(metrics["acutance_preset_mae"][PHONE_PRESET], 0.050),
    }
    return {
        "all_readme_gates_pass": all(row["pass"] for row in gates.values()),
        "failed_gates": [key for key, row in gates.items() if not row["pass"]],
        "gates": gates,
    }


def collect_candidate_metrics(
    *,
    candidate_acutance: dict[str, Any],
    candidate_psd: dict[str, Any],
) -> dict[str, Any]:
    acutance = candidate_acutance["overall"]
    psd = candidate_psd["overall"]
    return {
        "curve_mae_mean": float(acutance["curve_mae_mean"]),
        "acutance_focus_preset_mae_mean": float(acutance["acutance_focus_preset_mae_mean"]),
        "overall_quality_loss_mae_mean": float(acutance["overall_quality_loss_mae_mean"]),
        "mtf_abs_signed_rel_mean": float(psd["mtf_abs_signed_rel_mean"]),
        "mtf_threshold_mae": {
            key: float(value) for key, value in psd["mtf_threshold_mae"].items()
        },
        "acutance_preset_mae": {
            key: float(value) for key, value in acutance["acutance_preset_mae"].items()
        },
        "quality_loss_preset_mae": {
            key: float(value) for key, value in acutance["quality_loss_preset_mae"].items()
        },
    }


def metric_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_focus_key = (
        "acutance_focus_preset_mae_mean"
        if "acutance_focus_preset_mae_mean" in baseline
        else "focus_preset_acutance_mae_mean"
    )
    return {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["acutance_focus_preset_mae_mean"]
            - baseline[baseline_focus_key]
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


def is_release_path(path: str) -> bool:
    return path.startswith(GOLDEN_REFERENCE_ROOTS)


def build_payload(
    repo_root: Path,
    *,
    issue124_summary_path: Path,
    issue126_discovery_path: Path,
    candidate_acutance_path: Path,
    candidate_psd_path: Path,
) -> dict[str, Any]:
    issue124 = load_json(resolve_path(repo_root, issue124_summary_path))
    issue126 = load_json(resolve_path(repo_root, issue126_discovery_path))
    candidate_acutance = select_single_profile(
        load_json(resolve_path(repo_root, candidate_acutance_path))
    )
    candidate_psd = select_single_profile(load_json(resolve_path(repo_root, candidate_psd_path)))
    baseline = issue124["candidate"]["metrics"]
    pr30 = issue124["baseline_pr30"]["metrics"]
    candidate = collect_candidate_metrics(
        candidate_acutance=candidate_acutance,
        candidate_psd=candidate_psd,
    )
    delta_vs_pr125 = metric_delta(candidate, baseline)
    delta_vs_pr30 = metric_delta(candidate, pr30)
    by_mixup_baseline = issue124["curve_tail_result"]["by_mixup_after"]
    by_mixup_candidate = candidate_acutance["by_mixup_curve_mae_mean"]
    by_mixup_delta = {
        key: float(by_mixup_candidate[key] - by_mixup_baseline[key])
        for key in by_mixup_candidate
    }
    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "result_kind": RESULT_KIND,
        "candidate": {
            "label": "issue128_ori_015_curve_shape_candidate",
            "profile_path": candidate_acutance["profile_path"],
            "curve_only_acutance_anchor_mixups": list(
                candidate_acutance["analysis_pipeline"]["curve_only_acutance_anchor_mixups"]
            ),
            "target_mixups": list(TARGET_MIXUPS),
            "deferred_mixups": list(DEFERRED_MIXUPS),
            "source_artifacts": [
                str(candidate_acutance_path),
                str(candidate_psd_path),
                str(issue124_summary_path),
                str(issue126_discovery_path),
            ],
            "metrics": candidate,
        },
        "baseline_pr125": {
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "profile_path": issue124["candidate"]["profile_path"],
            "metrics": baseline,
        },
        "baseline_pr30": issue124["baseline_pr30"],
        "readme_gate_summary": readme_gate_summary(candidate),
        "comparisons": {
            "candidate_vs_pr125": {"delta": delta_vs_pr125},
            "candidate_vs_pr30": {"delta": delta_vs_pr30},
        },
        "curve_shape_result": {
            "selected_slice_id": issue126["selected_next_slice"]["slice_id"],
            "candidate_boundary": (
                "Adds `0.15` to the existing issue #124 curve-only Acutance anchor mask; "
                "`0.25` and preset Acutance remain untouched."
            ),
            "by_mixup_baseline": {
                key: float(value) for key, value in sorted(by_mixup_baseline.items())
            },
            "by_mixup_candidate": {
                key: float(value) for key, value in sorted(by_mixup_candidate.items())
            },
            "by_mixup_delta": {key: float(value) for key, value in sorted(by_mixup_delta.items())},
            "target_mixups": list(TARGET_MIXUPS),
            "deferred_mixups": list(DEFERRED_MIXUPS),
        },
        "acceptance": {
            "curve_gate_pass": candidate["curve_mae_mean"] <= CURVE_GATE,
            "curve_improved_vs_pr125": delta_vs_pr125["curve_mae_mean"] < 0.0,
            "reported_mtf_preserved": (
                is_close(delta_vs_pr125["mtf_abs_signed_rel_mean"], 0.0)
                and all(
                    is_close(value, 0.0)
                    for value in delta_vs_pr125["mtf_threshold_mae"].values()
                )
            ),
            "focus_preset_acutance_preserved": is_close(
                delta_vs_pr125["focus_preset_acutance_mae_mean"],
                0.0,
            ),
            "overall_quality_loss_preserved": is_close(
                delta_vs_pr125["overall_quality_loss_mae_mean"],
                0.0,
            ),
            "small_print_acutance_preserved": is_close(
                delta_vs_pr125["acutance_preset_mae"][SMALL_PRINT_PRESET],
                0.0,
            ),
            "release_separation_preserved": True,
        },
        "next_result": {
            "summary": (
                "The bounded ori/0.15 curve-shape candidate is not promotable: it preserves "
                "reported-MTF, preset Acutance, overall Quality Loss, and release separation, "
                "but worsens the aggregate curve MAE because the current matched-ori curve "
                "shape moves `0.15` in the wrong direction."
            ),
            "recommended_follow_up": (
                "Do not continue broadening the issue #124 curve-only anchor mask. If PM "
                "splits another curve follow-up, it should require a per-mixup or shape-family "
                "variant that proves `0.15` improves before committing to a full benchmark; "
                "otherwise split the deferred Small Print Acutance preset-only miss."
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
            "discovery_issue": DISCOVERY_ISSUE,
            "discovery_pr": DISCOVERY_PR,
            "baseline_pr": BASELINE_PR,
        },
    }
    assert_storage_separation(payload)
    return payload


def assert_storage_separation(payload: dict[str, Any]) -> None:
    paths = [
        payload["candidate"]["profile_path"],
        *payload["candidate"]["source_artifacts"],
    ]
    for path in paths:
        if is_release_path(path):
            raise ValueError(f"candidate path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    candidate = payload["candidate"]
    metrics = candidate["metrics"]
    pr125 = payload["baseline_pr125"]["metrics"]
    delta = payload["comparisons"]["candidate_vs_pr125"]["delta"]
    gates = payload["readme_gate_summary"]["gates"]
    curve = payload["curve_shape_result"]
    return "\n".join(
        [
            "# Issue 128 Ori/0.15 Curve-Shape Summary",
            "",
            f"- Result: `{payload['result_kind']}`.",
            f"- Candidate profile: `{candidate['profile_path']}`",
            "- Scoped boundary: add `0.15` to the existing issue #124 curve-only Acutance "
            "anchor mask; keep `0.25`, preset Acutance, Quality Loss, and reported-MTF/readout untouched.",
            "",
            "## Metrics",
            "",
            "| Metric | PR #125 | Issue #128 | Delta | Gate |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(pr125['curve_mae_mean'])} | "
            f"{format_metric(metrics['curve_mae_mean'])} | "
            f"{format_metric(delta['curve_mae_mean'])} | "
            f"<= 0.020 ({'pass' if gates['curve_mae_mean']['pass'] else 'miss'}) |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(pr125['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(metrics['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(delta['focus_preset_acutance_mae_mean'])} | preserve |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(pr125['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(metrics['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(delta['overall_quality_loss_mae_mean'])} | preserve |",
            f"| mtf_abs_signed_rel_mean | {format_metric(pr125['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(metrics['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(delta['mtf_abs_signed_rel_mean'])} | preserve |",
            f"| Small Print Acutance | "
            f"{format_metric(pr125['acutance_preset_mae'][SMALL_PRINT_PRESET])} | "
            f"{format_metric(metrics['acutance_preset_mae'][SMALL_PRINT_PRESET])} | "
            f"{format_metric(delta['acutance_preset_mae'][SMALL_PRINT_PRESET])} | "
            f"<= 0.030 ({'pass' if gates['non_phone_acutance_preset_mae_max']['pass'] else 'miss'}) |",
            "",
            "## Curve Shape Result",
            "",
            "| Mixup | PR #125 | Issue #128 | Delta |",
            "| --- | ---: | ---: | ---: |",
            *[
                f"| {key} | {format_metric(curve['by_mixup_baseline'][key])} | "
                f"{format_metric(curve['by_mixup_candidate'][key])} | "
                f"{format_metric(curve['by_mixup_delta'][key])} |"
                for key in sorted(curve["by_mixup_candidate"])
            ],
            "",
            "The `ori` and `0.8` curve values stay at their issue #124 values, but `0.15` "
            "worsens from `0.02938` to `0.03546`. The aggregate curve MAE therefore "
            "moves away from the README gate.",
            "",
            "## Acceptance",
            "",
            f"- Curve gate pass: `{payload['acceptance']['curve_gate_pass']}`.",
            f"- Curve improved versus PR #125: `{payload['acceptance']['curve_improved_vs_pr125']}`.",
            f"- Reported-MTF preserved: `{payload['acceptance']['reported_mtf_preserved']}`.",
            f"- Focus-preset Acutance preserved: `{payload['acceptance']['focus_preset_acutance_preserved']}`.",
            f"- Overall Quality Loss preserved: `{payload['acceptance']['overall_quality_loss_preserved']}`.",
            f"- Small Print Acutance preserved: `{payload['acceptance']['small_print_acutance_preserved']}`.",
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
        issue124_summary_path=args.issue124_summary,
        issue126_discovery_path=args.issue126_discovery,
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
