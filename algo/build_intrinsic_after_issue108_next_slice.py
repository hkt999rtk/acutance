from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue108_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE102_LABEL = "issue102_readout_only_sensor_comp_candidate"
ISSUE108_LABEL = "issue108_pr30_observed_bundle_candidate"
SELECTED_SLICE_ID = "issue108_computer_monitor_quality_loss_preset_boundary"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-111 post-issue108 Quality Loss next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue108-summary",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_pr30_observed_bundle_benchmark.json"),
        help="Repo-relative issue-108 summary artifact path.",
    )
    parser.add_argument(
        "--issue108-acutance-artifact",
        type=Path,
        default=Path(
            "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
        ),
        help="Repo-relative issue-108 acutance/Quality Loss raw benchmark artifact path.",
    )
    parser.add_argument(
        "--issue105-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        help="Repo-relative issue-105 selected-slice artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue108_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue108_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def delta_map(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, float]:
    return {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["focus_preset_acutance_mae_mean"]
            - baseline["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            candidate["overall_quality_loss_mae_mean"]
            - baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf20": float(candidate["mtf_threshold_mae"]["mtf20"] - baseline["mtf_threshold_mae"]["mtf20"]),
        "mtf30": float(candidate["mtf_threshold_mae"]["mtf30"] - baseline["mtf_threshold_mae"]["mtf30"]),
        "mtf50": float(candidate["mtf_threshold_mae"]["mtf50"] - baseline["mtf_threshold_mae"]["mtf50"]),
    }


def quality_loss_preset_deltas(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_values = candidate["quality_loss_preset_mae"]
    baseline_values = baseline["quality_loss_preset_mae"]
    preset_count = len(candidate_values)
    rows = []
    for preset_name in sorted(candidate_values):
        delta = float(candidate_values[preset_name] - baseline_values[preset_name])
        rows.append(
            {
                "preset": preset_name,
                "issue108": float(candidate_values[preset_name]),
                "current_best_pr30": float(baseline_values[preset_name]),
                "delta": delta,
                "mean_contribution": float(delta / preset_count),
                "direction": "worse_than_pr30" if delta > 0.0 else "better_than_or_equal_pr30",
            }
        )
    return sorted(rows, key=lambda row: row["delta"], reverse=True)


def acutance_preset_deltas(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_values = candidate["acutance_preset_mae"]
    baseline_values = baseline["acutance_preset_mae"]
    return [
        {
            "preset": preset_name,
            "issue108": float(candidate_values[preset_name]),
            "current_best_pr30": float(baseline_values[preset_name]),
            "delta": float(candidate_values[preset_name] - baseline_values[preset_name]),
        }
        for preset_name in sorted(candidate_values)
    ]


def by_mixup_quality_loss_deltas(raw_acutance_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    current_best = raw_acutance_artifact["profiles"][0]["by_mixup_quality_loss_mae_mean"]
    issue108 = raw_acutance_artifact["profiles"][2]["by_mixup_quality_loss_mae_mean"]
    rows = [
        {
            "mixup": mixup,
            "issue108": float(issue108[mixup]),
            "current_best_pr30": float(current_best[mixup]),
            "delta": float(issue108[mixup] - current_best[mixup]),
        }
        for mixup in sorted(issue108)
    ]
    return sorted(rows, key=lambda row: row["delta"], reverse=True)


def quality_loss_coefficients_equal(candidate: dict[str, Any], baseline: dict[str, Any]) -> bool:
    candidate_pipeline = candidate["analysis_pipeline"]
    baseline_pipeline = baseline["analysis_pipeline"]
    return (
        candidate_pipeline["quality_loss_coefficients"]
        == baseline_pipeline["quality_loss_coefficients"]
        and candidate_pipeline["quality_loss_om_ceiling"]
        == baseline_pipeline["quality_loss_om_ceiling"]
        and candidate_pipeline["quality_loss_preset_overrides"]
        == baseline_pipeline["quality_loss_preset_overrides"]
    )


def differing_pipeline_keys(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    candidate_pipeline = candidate["analysis_pipeline"]
    baseline_pipeline = baseline["analysis_pipeline"]
    keys = (
        "acutance_noise_scale_mode",
        "intrinsic_full_reference_mode",
        "intrinsic_full_reference_scope",
        "intrinsic_full_reference_transfer_mode",
        "matched_ori_anchor_mode",
        "readout_mtf_compensation_mode",
        "readout_sensor_fill_factor",
    )
    return {
        key: {
            ISSUE108_LABEL: candidate_pipeline.get(key),
            CURRENT_BEST_LABEL: baseline_pipeline.get(key),
        }
        for key in keys
        if candidate_pipeline.get(key) != baseline_pipeline.get(key)
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(
    repo_root: Path,
    *,
    issue108_summary_path: Path,
    issue108_acutance_artifact_path: Path,
    issue105_summary_path: Path,
) -> dict[str, Any]:
    issue108_summary = load_json(resolve_path(repo_root, issue108_summary_path))
    raw_acutance_artifact = load_json(resolve_path(repo_root, issue108_acutance_artifact_path))
    issue105_summary = load_json(resolve_path(repo_root, issue105_summary_path))

    profiles = issue108_summary["profiles"]
    current_best = profiles[CURRENT_BEST_LABEL]
    issue102 = profiles[ISSUE102_LABEL]
    issue108 = profiles[ISSUE108_LABEL]

    issue108_vs_pr30 = delta_map(issue108, current_best)
    issue108_vs_issue102 = delta_map(issue108, issue102)
    preset_deltas = quality_loss_preset_deltas(issue108, current_best)
    positive_preset_contribution = float(
        sum(row["mean_contribution"] for row in preset_deltas if row["mean_contribution"] > 0.0)
    )
    top_preset = preset_deltas[0]

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "decision": "advance",
            "label": "isolate the Computer Monitor Quality Loss preset-family downstream input boundary",
            "adoption_reason": (
                "Computer Monitor Quality Loss is the largest positive preset delta after issue #108 "
                "and contributes most of the net residual mean gap by itself."
            ),
            "selected_summary": (
                "Keep issue #108 reported-MTF parity, the issue #102 intrinsic main-acutance gains, "
                "and the existing PR #30 Quality Loss coefficients/ceilings. The next bounded "
                "implementation should isolate only the Computer Monitor downstream Quality Loss "
                "preset-family input branch, comparing an issue-108 Quality Loss input against a "
                "PR #30-compatible acutance-only/noise-share anchor input for that preset before "
                "changing any other preset family."
            ),
            "repo_evidence": [
                "Issue #108 matches PR #30 on `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50`, so the residual is not a reported-MTF/readout retune problem.",
                "Issue #108 keeps `curve_mae_mean` and `focus_preset_acutance_mae_mean` better than PR #30, so the issue #102 intrinsic main-acutance branch should not be discarded.",
                "Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` already match PR #30 exactly, so a coefficient/ceiling retune would ignore the checked-in evidence.",
                "Computer Monitor Quality Loss delta is `+0.66202`, contributing `+0.13240` to the `+0.18513` overall mean delta; fixing only this preset would shrink most of the residual net gap.",
                "Computer Monitor Acutance MAE is already better than PR #30 while Computer Monitor Quality Loss MAE is worse, which localizes the problem to the downstream Quality Loss input/mapping boundary rather than a general preset-acutance miss.",
                "UHDTV Quality Loss is already better than PR #30, so a blanket downstream Quality Loss branch swap risks regressing an already-positive preset family.",
            ],
            "minimum_implementation_boundary": [
                "Do not change reported-MTF/readout metrics or their issue-108 PR30 observed-branch bundle.",
                "Do not change the issue #102 intrinsic main-acutance branch used for curve and focus-preset Acutance.",
                "Do not change Quality Loss coefficients, preset overrides, or `quality_loss_om_ceiling`.",
                "Add only enough branch selection or instrumentation to route the Computer Monitor Quality Loss preset-family input through a PR #30-compatible downstream acutance/noise-anchor input while keeping the other Quality Loss presets on the issue-108 path for comparison.",
            ],
            "validation_plan_for_next_issue": [
                "Run the focused acutance/Quality Loss benchmark comparing PR #30, issue #108, and the Computer Monitor-only candidate.",
                "Require `Computer Monitor Quality Loss` MAE to improve materially versus issue #108 while `overall_quality_loss_mae_mean` also improves.",
                "Require `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` to remain equal to issue #108 / PR #30.",
                "Require `curve_mae_mean` and `focus_preset_acutance_mae_mean` to remain no worse than issue #108.",
            ],
        },
        {
            "slice_id": "retune_quality_loss_coefficients_or_om_ceiling",
            "decision": "exclude",
            "label": "retune Quality Loss coefficients or ceilings",
            "exclusion_reasons": [
                "Issue #108 and PR #30 already use identical global coefficients, identical preset overrides, and identical `quality_loss_om_ceiling`.",
                "The residual therefore comes from the Quality Loss input branch, not from a missing fitted coefficient record.",
            ],
        },
        {
            "slice_id": "retune_reported_mtf_readout_again",
            "decision": "exclude",
            "label": "retune reported-MTF/readout after issue #108",
            "exclusion_reasons": [
                "Issue #108 already matches PR #30 on `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50`.",
                "Changing the reported-MTF branch would violate the issue-111 constraint to preserve issue-108 reported-MTF parity.",
            ],
        },
        {
            "slice_id": "phone_preset_only_search",
            "decision": "exclude",
            "label": "reopen a Phone-only Quality Loss search",
            "exclusion_reasons": [
                "Phone Quality Loss contributes only `+0.01901` to the residual mean gap, far less than the Computer Monitor contribution.",
                "Issue #111 explicitly excludes reopening Phone-preset-only searches.",
            ],
        },
        {
            "slice_id": "uhdtv_quality_loss_preset_family",
            "decision": "exclude",
            "label": "target UHDTV Quality Loss first",
            "exclusion_reasons": [
                "UHDTV Quality Loss is already better than PR #30 by `-0.18394`, so targeting it first would risk damaging an existing win.",
            ],
        },
        {
            "slice_id": "restart_broad_intrinsic_or_observable_stack_search",
            "decision": "exclude",
            "label": "restart broad intrinsic, matched-ori, or observable-stack search",
            "exclusion_reasons": [
                "The post-issue108 residual is already localized to downstream Quality Loss deltas after reported-MTF parity closed.",
                "The issue-111 handoff asks for one bounded slice from measured issue-108 deltas, not a broad family search.",
            ],
        },
    ]

    payload = {
        "issue": 111,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue108_summary": str(issue108_summary_path),
            "issue108_acutance_artifact": str(issue108_acutance_artifact_path),
            "issue105_summary": str(issue105_summary_path),
            "comparison_basis_refs": ["pr-30", "issue-102", "issue-105", "issue-108", "pr-109"],
            "issue105_selected_slice_id": issue105_summary["selected_slice_id"],
        },
        "comparison_records": {
            CURRENT_BEST_LABEL: current_best,
            ISSUE102_LABEL: issue102,
            ISSUE108_LABEL: issue108,
        },
        "residual_quality_loss_boundaries": {
            "issue108_vs_current_best_pr30": issue108_vs_pr30,
            "issue108_vs_issue102": issue108_vs_issue102,
            "quality_loss_preset_deltas": preset_deltas,
            "acutance_preset_deltas": acutance_preset_deltas(issue108, current_best),
            "by_mixup_quality_loss_deltas": by_mixup_quality_loss_deltas(raw_acutance_artifact),
            "positive_preset_mean_contribution": positive_preset_contribution,
            "top_positive_preset": top_preset,
            "top_positive_preset_net_gap_share": float(
                top_preset["mean_contribution"]
                / issue108_vs_pr30["overall_quality_loss_mae_mean"]
            ),
            "top_positive_preset_positive_contribution_share": float(
                top_preset["mean_contribution"] / positive_preset_contribution
            ),
        },
        "boundary_evidence": {
            "reported_mtf_parity_with_pr30": {
                "mtf_abs_signed_rel_mean": issue108_vs_pr30["mtf_abs_signed_rel_mean"] == 0.0,
                "mtf20": issue108_vs_pr30["mtf20"] == 0.0,
                "mtf30": issue108_vs_pr30["mtf30"] == 0.0,
                "mtf50": issue108_vs_pr30["mtf50"] == 0.0,
            },
            "issue102_intrinsic_gains_preserved_vs_pr30": {
                "curve_mae_mean": issue108_vs_pr30["curve_mae_mean"] < 0.0,
                "focus_preset_acutance_mae_mean": (
                    issue108_vs_pr30["focus_preset_acutance_mae_mean"] < 0.0
                ),
            },
            "quality_loss_coefficients_and_ceilings_match_pr30": quality_loss_coefficients_equal(
                issue108,
                current_best,
            ),
            "remaining_pipeline_deltas_vs_pr30": differing_pipeline_keys(issue108, current_best),
        },
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue108_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep issue-111 discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write fitted profiles, transfer tables, or generated outputs under golden/reference roots.",
                "Do not touch release-facing configs in this issue.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    records = payload["comparison_records"]
    current_best = records[CURRENT_BEST_LABEL]
    issue108 = records[ISSUE108_LABEL]
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )
    residual = payload["residual_quality_loss_boundaries"]
    top_preset = residual["top_positive_preset"]

    lines = [
        "# Intrinsic After Issue 108 Next Slice",
        "",
        "This note records the Issue `#111` developer-discovery pass after issue `#108` / PR `#109` grafted the PR `#30` observed-branch bundle onto the issue-102 topology.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        "- Prior narrowing lineage: issue `#105` / PR `#106` / PR `#107` selected the PR30 observed-branch bundle, and issue `#108` / PR `#109` implemented it while preserving issue #102 curve/focus gains.",
        "- Remaining gap location: reported-MTF is now equal to PR `#30`, Quality Loss coefficients are equal to PR `#30`, and the largest residual is the Computer Monitor Quality Loss preset-family input boundary.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {CURRENT_BEST_LABEL} | {format_metric(current_best['curve_mae_mean'])} | {format_metric(current_best['focus_preset_acutance_mae_mean'])} | {format_metric(current_best['overall_quality_loss_mae_mean'])} | {format_metric(current_best['mtf_threshold_mae']['mtf20'])} | {format_metric(current_best['mtf_threshold_mae']['mtf30'])} | {format_metric(current_best['mtf_threshold_mae']['mtf50'])} | {format_metric(current_best['mtf_abs_signed_rel_mean'])} | Current best PR30 branch. |",
        f"| {ISSUE108_LABEL} | {format_metric(issue108['curve_mae_mean'])} | {format_metric(issue108['focus_preset_acutance_mae_mean'])} | {format_metric(issue108['overall_quality_loss_mae_mean'])} | {format_metric(issue108['mtf_threshold_mae']['mtf20'])} | {format_metric(issue108['mtf_threshold_mae']['mtf30'])} | {format_metric(issue108['mtf_threshold_mae']['mtf50'])} | {format_metric(issue108['mtf_abs_signed_rel_mean'])} | Issue-108 bounded implementation from PR #109. |",
        "",
        "## Residual Quality Loss Preset Deltas",
        "",
        "| Preset | PR30 QL MAE | Issue108 QL MAE | Delta | Mean contribution |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in residual["quality_loss_preset_deltas"]:
        lines.append(
            f"| {row['preset']} | {format_metric(row['current_best_pr30'])} | {format_metric(row['issue108'])} | {row['delta']:+.5f} | {row['mean_contribution']:+.5f} |"
        )
    lines.extend(
        [
            "",
            "## Residual Evidence",
            "",
            f"- Overall Quality Loss gap after issue #108: `{residual['issue108_vs_current_best_pr30']['overall_quality_loss_mae_mean']:+.5f}`.",
            f"- Top positive preset delta: `{top_preset['preset']}` at `{top_preset['delta']:+.5f}`, contributing `{top_preset['mean_contribution']:+.5f}` to the mean gap.",
            f"- Top preset share of the net residual gap: `{residual['top_positive_preset_net_gap_share']:.2%}`.",
            f"- Reported-MTF parity with PR #30: `{all(payload['boundary_evidence']['reported_mtf_parity_with_pr30'].values())}`.",
            f"- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` match PR #30: `{payload['boundary_evidence']['quality_loss_coefficients_and_ceilings_match_pr30']}`.",
            f"- Issue #108 keeps curve/focus better than PR #30: `{all(payload['boundary_evidence']['issue102_intrinsic_gains_preserved_vs_pr30'].values())}`.",
            "- Computer Monitor Acutance MAE is already better than PR #30, but Computer Monitor Quality Loss MAE is worse. That separates the residual from a generic preset-acutance failure and points at the downstream Quality Loss input/mapping branch.",
            "- UHDTV Quality Loss is already better than PR #30, so a blanket Quality Loss branch swap is not the next minimum slice.",
            "",
            "## Remaining Pipeline Deltas",
            "",
        ]
    )
    for key, delta in payload["boundary_evidence"]["remaining_pipeline_deltas_vs_pr30"].items():
        lines.append(
            f"- `{key}`: issue108={delta[ISSUE108_LABEL]!r}, pr30={delta[CURRENT_BEST_LABEL]!r}"
        )
    lines.extend(["", "## Selected Implementation Boundary", ""])
    for row in selected["minimum_implementation_boundary"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Excluded Routes", ""])
    for row in payload["candidate_slices"]:
        if row["decision"] == "exclude":
            lines.append(f"### `{row['slice_id']}`")
            lines.append("")
            lines.append(f"- Route: {row['label']}")
            for reason in row["exclusion_reasons"]:
                lines.append(f"- {reason}")
            lines.append("")
    lines.extend(["## Validation Plan For The Next Implementation Issue", ""])
    for row in selected["validation_plan_for_next_issue"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Storage Separation",
            "",
            f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`, `{GOLDEN_REFERENCE_ROOTS[2]}`",
            "- Discovery outputs for this issue stay under `docs/` and `artifacts/` only.",
            "- Do not write new fitted profiles, transfer tables, benchmark outputs, or release-facing configs under those roots.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(
        repo_root,
        issue108_summary_path=args.issue108_summary,
        issue108_acutance_artifact_path=args.issue108_acutance_artifact,
        issue105_summary_path=args.issue105_summary,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
