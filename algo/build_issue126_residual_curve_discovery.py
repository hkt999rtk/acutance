from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 126
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 124
CURRENT_BEST_PR = 125
BASELINE_PR = 30
SUMMARY_KIND = "issue126_residual_curve_discovery"
SELECTED_DISCOVERY_ID = "issue124_residual_curve_ori_015_025_discovery"
SELECTED_SLICE_ID = "issue124_residual_curve_ori_015_curve_only_shape_boundary"
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
    parser = argparse.ArgumentParser(description="Build issue-126 residual curve discovery.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue124-summary",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue126_residual_curve_discovery.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue126_residual_curve_discovery.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_gate(value: float, threshold: float) -> dict[str, Any]:
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
        key: value
        for key, value in metrics["acutance_preset_mae"].items()
        if key != PHONE_PRESET
    }
    worst_preset, worst_value = max(non_phone.items(), key=lambda item: item[1])
    gates = {
        "curve_mae_mean": metric_gate(metrics["curve_mae_mean"], CURVE_GATE),
        "focus_preset_acutance_mae_mean": metric_gate(
            metrics["acutance_focus_preset_mae_mean"],
            FOCUS_PRESET_GATE,
        ),
        "overall_quality_loss_mae_mean": metric_gate(
            metrics["overall_quality_loss_mae_mean"],
            QUALITY_LOSS_GATE,
        ),
        "non_phone_acutance_preset_mae_max": {
            **metric_gate(worst_value, NON_PHONE_ACUTANCE_GATE),
            "worst_preset": worst_preset,
            "by_preset": {key: float(value) for key, value in sorted(non_phone.items())},
        },
        PHONE_PRESET: metric_gate(metrics["acutance_preset_mae"][PHONE_PRESET], 0.050),
    }
    return {
        "all_readme_gates_pass": all(row["pass"] for row in gates.values()),
        "failed_gates": [key for key, row in gates.items() if not row["pass"]],
        "gates": gates,
    }


def compute_residual_curve_evidence(issue124: dict[str, Any]) -> dict[str, Any]:
    before = issue124["curve_tail_result"]["by_mixup_before"]
    after = issue124["curve_tail_result"]["by_mixup_after"]
    issue122_by_mixup = load_json(
        Path(__file__).resolve().parents[1]
        / "artifacts/intrinsic_after_issue120_next_slice_benchmark.json"
    )["residual_curve_evidence"]["by_mixup"]
    weighted_curve = sum(
        float(after[mixup]) * float(issue122_by_mixup[mixup]["record_fraction"])
        for mixup in after
    )
    rows: dict[str, dict[str, Any]] = {}
    positive_excess_total = 0.0
    for mixup in sorted(after, key=lambda item: (item == "ori", float(item) if item != "ori" else 9.9)):
        record_fraction = float(issue122_by_mixup[mixup]["record_fraction"])
        value = float(after[mixup])
        excess = max(0.0, value - CURVE_GATE)
        weighted_excess = excess * record_fraction
        positive_excess_total += weighted_excess
        rows[mixup] = {
            "before_issue124_curve_mae": float(before[mixup]),
            "after_issue124_curve_mae": value,
            "delta_from_issue124": float(value - float(before[mixup])),
            "record_count": int(issue122_by_mixup[mixup]["record_count"]),
            "record_fraction": record_fraction,
            "weighted_contribution_to_curve_mae": float(value * record_fraction),
            "passes_curve_gate_if_viewed_alone": value <= CURVE_GATE,
            "excess_above_curve_gate": excess,
            "weighted_excess_above_curve_gate": weighted_excess,
        }
    for row in rows.values():
        row["positive_excess_share"] = (
            float(row["weighted_excess_above_curve_gate"] / positive_excess_total)
            if positive_excess_total
            else 0.0
        )
    ranked = sorted(
        rows,
        key=lambda mixup: rows[mixup]["weighted_excess_above_curve_gate"],
        reverse=True,
    )
    selected = []
    cumulative_reduction_to_gate = 0.0
    for mixup in ranked:
        if rows[mixup]["weighted_excess_above_curve_gate"] <= 0:
            continue
        selected.append(mixup)
        cumulative_reduction_to_gate += rows[mixup]["weighted_excess_above_curve_gate"]
        if weighted_curve - cumulative_reduction_to_gate <= CURVE_GATE:
            break
    residual_after_selected_to_gate = weighted_curve - cumulative_reduction_to_gate
    return {
        "weighted_curve_mae": float(weighted_curve),
        "curve_gate": CURVE_GATE,
        "delta_to_curve_gate": float(weighted_curve - CURVE_GATE),
        "by_mixup": rows,
        "positive_excess_total": float(positive_excess_total),
        "ranked_positive_excess_mixups": [
            mixup for mixup in ranked if rows[mixup]["weighted_excess_above_curve_gate"] > 0
        ],
        "selected_minimum_gate_clear_mixups": selected,
        "selected_if_reduced_to_gate_curve_mae": float(residual_after_selected_to_gate),
        "ori_only_if_reduced_to_gate_curve_mae": float(
            weighted_curve - rows["ori"]["weighted_excess_above_curve_gate"]
        ),
        "ori_and_025_if_reduced_to_gate_curve_mae": float(
            weighted_curve
            - rows["ori"]["weighted_excess_above_curve_gate"]
            - rows["0.25"]["weighted_excess_above_curve_gate"]
        ),
        "ori_and_015_if_reduced_to_gate_curve_mae": float(
            weighted_curve
            - rows["ori"]["weighted_excess_above_curve_gate"]
            - rows["0.15"]["weighted_excess_above_curve_gate"]
        ),
    }


def is_release_path(path: str) -> bool:
    return path.startswith(GOLDEN_REFERENCE_ROOTS)


def build_payload(repo_root: Path, *, issue124_summary_path: Path) -> dict[str, Any]:
    issue124 = load_json(resolve_path(repo_root, issue124_summary_path))
    current = issue124["candidate"]
    current_metrics = current["metrics"]
    gate_summary = readme_gate_summary(current_metrics)
    residual = compute_residual_curve_evidence(issue124)
    selected_mixups = residual["selected_minimum_gate_clear_mixups"]
    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "selected_discovery_id": SELECTED_DISCOVERY_ID,
        "current_best": {
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "profile_path": current["profile_path"],
            "metrics": current_metrics,
            "source_artifacts": [str(issue124_summary_path), *current["source_artifacts"]],
        },
        "readme_gate_status": gate_summary,
        "comparisons": {
            "current_best_vs_pr119": issue124["comparisons"]["candidate_vs_pr119"],
            "current_best_vs_pr30": issue124["comparisons"]["candidate_vs_pr30"],
        },
        "residual_curve_evidence": residual,
        "selected_next_slice": {
            "slice_id": SELECTED_SLICE_ID,
            "selected": True,
            "selected_summary": (
                "Keep issue #124 curve-only isolation, but split the next implementation "
                "around residual curve-shape tuning for `ori` and `0.15`. Those two "
                "mixups are the smallest residual pair whose above-gate weighted excess "
                "can clear the README curve gate if each is reduced to the gate."
            ),
            "target_mixups": selected_mixups,
            "explicitly_deferred_mixups": [
                mixup
                for mixup in residual["ranked_positive_excess_mixups"]
                if mixup not in selected_mixups
            ],
            "minimum_implementation_boundary": [
                "Start from the issue #124 / PR #125 candidate profile.",
                "Preserve `curve_only_acutance_anchor_mixups` isolation and do not touch preset Acutance.",
                "Add or tune only curve-side matched-ori Acutance correction shape for the selected residual mixups.",
                "Do not change reported-MTF compensation/readout settings or Quality Loss preset input overrides.",
                "Keep release-facing configs and golden/reference data untouched.",
            ],
            "repo_evidence": [
                "`ori`, `0.15`, and `0.25` are the only mixups still above the curve gate after PR #125.",
                "`ori` alone cannot clear the aggregate curve gate if reduced only to the per-mixup gate.",
                "`ori + 0.25` still cannot clear the aggregate curve gate under the same bound.",
                "`ori + 0.15` is the smallest weighted residual pair that can clear the curve gate under the same bound.",
                "PR #125 already proved curve-only isolation can move curve MAE while preserving reported-MTF, preset Acutance, overall Quality Loss, and release separation.",
            ],
            "expected_preservation": {
                "reported_mtf_parity": "preserve",
                "focus_preset_acutance_mae_mean": "preserve",
                "overall_quality_loss_mae_mean": "preserve",
                "small_print_acutance": "preserve",
                "release_separation": "preserve",
            },
            "validation_plan": [
                "Regenerate Acutance/Quality Loss benchmark artifact for the candidate profile.",
                "Regenerate PSD/MTF benchmark artifact to prove reported-MTF remains unchanged.",
                "Compare README gates and PR #125 deltas in a checked-in summary.",
                "Require `curve_mae_mean <= 0.020` for promotion; otherwise record a bounded negative or split the residual `0.25` curve miss.",
                "Require focus-preset Acutance, overall Quality Loss, Small Print Acutance, and reported-MTF metrics to match PR #125 unless the result is explicitly non-promotable.",
            ],
        },
        "stop_curve_work_option": {
            "selected": False,
            "reason": (
                "Do not stop curve work yet: the residual curve miss is still larger than "
                "the deferred Small Print Acutance miss, and existing curve-only isolation "
                "has already produced a protected-branch-preserving improvement."
            ),
            "deferred_issue": "Small Print Acutance preset-only boundary",
        },
        "acceptance": {
            "identifies_next_bounded_slice": True,
            "next_handoff_is_not_umbrella": True,
            "records_pr125_deltas": True,
            "release_separation_preserved": not any(
                is_release_path(path) for path in current["source_artifacts"]
            ),
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "Discovery uses checked-in benchmark summaries and does not promote fitted outputs.",
                "The next slice must keep candidate profiles in `algo/` or artifacts/docs only.",
                "No release-facing config or golden/reference data root is modified by this discovery.",
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
    paths = [
        payload["current_best"]["profile_path"],
        *payload["current_best"]["source_artifacts"],
    ]
    for path in paths:
        if is_release_path(path):
            raise ValueError(f"discovery source path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_best"]
    metrics = current["metrics"]
    gates = payload["readme_gate_status"]["gates"]
    residual = payload["residual_curve_evidence"]
    selected = payload["selected_next_slice"]
    return "\n".join(
        [
            "# Issue 126 Residual Curve Discovery",
            "",
            f"- Selected discovery: `{payload['selected_discovery_id']}`.",
            f"- Current best: issue `#{current['issue']}` / PR `#{current['pr']}`.",
            f"- Current profile: `{current['profile_path']}`",
            "- Scope: post-issue124 curve residual only; do not broaden into Small Print "
            "Acutance preset work inside this slice.",
            "",
            "## README Gate Status",
            "",
            "| Gate | Value | Threshold | Delta | Status |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(metrics['curve_mae_mean'])} | "
            f"{format_metric(gates['curve_mae_mean']['threshold'])} | "
            f"{format_metric(gates['curve_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['curve_mae_mean']['pass'] else 'miss'} |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(metrics['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['threshold'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['focus_preset_acutance_mae_mean']['pass'] else 'miss'} |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(metrics['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['threshold'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['overall_quality_loss_mae_mean']['pass'] else 'miss'} |",
            f"| non-phone Acutance max ({gates['non_phone_acutance_preset_mae_max']['worst_preset']}) | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['value'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['threshold'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['delta_to_gate'])} | "
            f"{'pass' if gates['non_phone_acutance_preset_mae_max']['pass'] else 'miss'} |",
            "",
            "## Residual Curve Evidence",
            "",
            "| Mixup | Curve MAE | Weighted contribution | Above-gate contribution | Positive excess share | Gate |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
            *[
                f"| {mixup} | {format_metric(row['after_issue124_curve_mae'])} | "
                f"{format_metric(row['weighted_contribution_to_curve_mae'])} | "
                f"{format_metric(row['weighted_excess_above_curve_gate'])} | "
                f"{row['positive_excess_share']:.3f} | "
                f"{'pass' if row['passes_curve_gate_if_viewed_alone'] else 'miss'} |"
                for mixup, row in residual["by_mixup"].items()
            ],
            "",
            f"- Weighted curve MAE remains `{format_metric(residual['weighted_curve_mae'])}`, "
            f"delta `{residual['delta_to_curve_gate']:+.5f}` to the README curve gate.",
            f"- Positive above-gate pressure ranks as: "
            f"`{', '.join(residual['ranked_positive_excess_mixups'])}`.",
            f"- If `ori` alone were reduced to the gate, aggregate curve MAE would still be "
            f"`{format_metric(residual['ori_only_if_reduced_to_gate_curve_mae'])}`.",
            f"- If `ori + 0.25` were reduced to the gate, aggregate curve MAE would still be "
            f"`{format_metric(residual['ori_and_025_if_reduced_to_gate_curve_mae'])}`.",
            f"- If `ori + 0.15` were reduced to the gate, aggregate curve MAE would be "
            f"`{format_metric(residual['ori_and_015_if_reduced_to_gate_curve_mae'])}`.",
            "",
            "## Selected Next Slice",
            "",
            f"- Slice ID: `{selected['slice_id']}`.",
            f"- Target mixups: `{', '.join(selected['target_mixups'])}`.",
            f"- Deferred residual mixups: `{', '.join(selected['explicitly_deferred_mixups'])}`.",
            f"- Summary: {selected['selected_summary']}",
            "",
            "Minimum boundary:",
            "",
            *[f"- {item}" for item in selected["minimum_implementation_boundary"]],
            "",
            "Validation plan:",
            "",
            *[f"- {item}" for item in selected["validation_plan"]],
            "",
            "## Stop-Curve Option",
            "",
            payload["stop_curve_work_option"]["reason"],
            "",
            "## Release Separation",
            "",
            "This is canonical-target discovery only. It uses checked-in artifacts and does "
            "not promote fitted outputs into golden/reference roots or release configs.",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = args.repo_root
    payload = build_payload(repo_root, issue124_summary_path=args.issue124_summary)
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
