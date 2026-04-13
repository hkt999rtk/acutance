from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue102_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE93_LABEL = "issue93_downstream_matched_ori_only_candidate"
ISSUE97_LABEL = "issue97_reported_mtf_disconnect_candidate"
ISSUE102_LABEL = "issue102_readout_only_sensor_comp_candidate"
SELECTED_SLICE_ID = "issue102_topology_graft_pr30_observable_stack_onto_observed_branches"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-105 intrinsic post-issue102 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue99-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue97_next_slice_benchmark.json"),
        help="Repo-relative issue-99 discovery artifact path.",
    )
    parser.add_argument(
        "--issue102-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"),
        help="Repo-relative issue-102 summary artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue102_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue102_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def is_close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)


def delta_map(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["focus_preset_acutance_mae_mean"]
            - baseline["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            candidate["overall_quality_loss_mae_mean"] - baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        },
    }


def pipeline_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    candidate_pipeline = candidate["analysis_pipeline"]
    baseline_pipeline = baseline["analysis_pipeline"]
    keys = [
        "calibration_file",
        "high_frequency_guard_start_cpp",
        "intrinsic_full_reference_mode",
        "intrinsic_full_reference_scope",
        "intrinsic_full_reference_transfer_mode",
        "matched_ori_anchor_mode",
        "mtf_compensation_mode",
        "readout_mtf_compensation_mode",
        "sensor_fill_factor",
        "readout_sensor_fill_factor",
        "texture_support_scale",
    ]
    return {
        key: {
            ISSUE102_LABEL: candidate_pipeline.get(key),
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
    issue99_artifact_path: Path,
    issue102_artifact_path: Path,
) -> dict[str, Any]:
    issue99_artifact = load_json(resolve_path(repo_root, issue99_artifact_path))
    issue102_artifact = load_json(resolve_path(repo_root, issue102_artifact_path))

    comparison_records = {
        CURRENT_BEST_LABEL: issue102_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE93_LABEL: issue102_artifact["profiles"][ISSUE93_LABEL],
        ISSUE97_LABEL: issue102_artifact["profiles"][ISSUE97_LABEL],
        ISSUE102_LABEL: issue102_artifact["profiles"][ISSUE102_LABEL],
    }
    current_best = comparison_records[CURRENT_BEST_LABEL]
    issue93 = comparison_records[ISSUE93_LABEL]
    issue97 = comparison_records[ISSUE97_LABEL]
    issue102 = comparison_records[ISSUE102_LABEL]

    issue102_vs_issue97 = delta_map(issue102, issue97)
    issue102_vs_issue93 = delta_map(issue102, issue93)
    issue102_vs_current_best = delta_map(issue102, current_best)

    residual_gap_evidence = {
        "issue102_preserves_issue97_core_record": {
            "curve_mae_mean": is_close(issue102["curve_mae_mean"], issue97["curve_mae_mean"]),
            "focus_preset_acutance_mae_mean": is_close(
                issue102["focus_preset_acutance_mae_mean"],
                issue97["focus_preset_acutance_mae_mean"],
            ),
            "overall_quality_loss_mae_mean": is_close(
                issue102["overall_quality_loss_mae_mean"],
                issue97["overall_quality_loss_mae_mean"],
            ),
            "delta": {
                "curve_mae_mean": issue102_vs_issue97["curve_mae_mean"],
                "focus_preset_acutance_mae_mean": issue102_vs_issue97[
                    "focus_preset_acutance_mae_mean"
                ],
                "overall_quality_loss_mae_mean": issue102_vs_issue97[
                    "overall_quality_loss_mae_mean"
                ],
            },
        },
        "issue102_readout_improves_but_does_not_close_pr30_gap": {
            "mtf_abs_signed_rel_improved_vs_issue97": (
                issue102["mtf_abs_signed_rel_mean"] < issue97["mtf_abs_signed_rel_mean"]
            ),
            "mtf20_beats_current_best_pr30": (
                issue102["mtf_threshold_mae"]["mtf20"] < current_best["mtf_threshold_mae"]["mtf20"]
            ),
            "mtf30_still_worse_than_current_best_pr30": (
                issue102["mtf_threshold_mae"]["mtf30"] > current_best["mtf_threshold_mae"]["mtf30"]
            ),
            "mtf50_still_worse_than_current_best_pr30": (
                issue102["mtf_threshold_mae"]["mtf50"] > current_best["mtf_threshold_mae"]["mtf50"]
            ),
            "mtf_abs_signed_rel_still_worse_than_current_best_pr30": (
                issue102["mtf_abs_signed_rel_mean"] > current_best["mtf_abs_signed_rel_mean"]
            ),
            "delta_vs_issue97": {
                "mtf20": issue102_vs_issue97["mtf_threshold_mae"]["mtf20"],
                "mtf30": issue102_vs_issue97["mtf_threshold_mae"]["mtf30"],
                "mtf50": issue102_vs_issue97["mtf_threshold_mae"]["mtf50"],
                "mtf_abs_signed_rel_mean": issue102_vs_issue97["mtf_abs_signed_rel_mean"],
            },
            "delta_vs_current_best_pr30": {
                "mtf20": issue102_vs_current_best["mtf_threshold_mae"]["mtf20"],
                "mtf30": issue102_vs_current_best["mtf_threshold_mae"]["mtf30"],
                "mtf50": issue102_vs_current_best["mtf_threshold_mae"]["mtf50"],
                "mtf_abs_signed_rel_mean": issue102_vs_current_best["mtf_abs_signed_rel_mean"],
            },
        },
        "issue93_issue97_issue102_quality_loss_record_is_invariant": {
            "issue93_equals_issue97": is_close(
                issue93["overall_quality_loss_mae_mean"],
                issue97["overall_quality_loss_mae_mean"],
            ),
            "issue97_equals_issue102": is_close(
                issue97["overall_quality_loss_mae_mean"],
                issue102["overall_quality_loss_mae_mean"],
            ),
            "issue93_equals_issue102": is_close(
                issue93["overall_quality_loss_mae_mean"],
                issue102["overall_quality_loss_mae_mean"],
            ),
            "delta_issue102_vs_current_best_pr30": issue102_vs_current_best[
                "overall_quality_loss_mae_mean"
            ],
        },
        "issue102_keeps_intrinsic_main_branch_better_than_pr30": {
            "curve_mae_mean_better_than_current_best_pr30": (
                issue102["curve_mae_mean"] < current_best["curve_mae_mean"]
            ),
            "focus_preset_acutance_mae_mean_better_than_current_best_pr30": (
                issue102["focus_preset_acutance_mae_mean"]
                < current_best["focus_preset_acutance_mae_mean"]
            ),
            "delta_vs_current_best_pr30": {
                "curve_mae_mean": issue102_vs_current_best["curve_mae_mean"],
                "focus_preset_acutance_mae_mean": issue102_vs_current_best[
                    "focus_preset_acutance_mae_mean"
                ],
            },
        },
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "keep the issue-102 intrinsic main branch but graft the PR30 observable-stack bundle onto the observed reported-MTF and downstream Quality Loss branches",
            "decision": "advance",
            "selected_summary": (
                "Keep issue #102's intrinsic main-acutance branch and readout-only sensor-aperture "
                "compensation record intact, but move the observed-branch consumers that still lag "
                "PR #30 onto one bounded PR30-style observable-stack bundle: anchored calibration, "
                "`texture_support_scale`, and `high_frequency_guard_start_cpp=0.36` for the "
                "reported-MTF/readout path and the downstream Quality Loss branch only."
            ),
            "repo_evidence": [
                "Issue #102 preserves issue #97 exactly on `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean`, so the issue-97 intrinsic main branch is no longer the unstable part of the stack.",
                "Issue #102 improves every tracked readout metric versus issue #97, which proves the single-knob readout compensation boundary was real, but the branch still trails PR #30 on `mtf_abs_signed_rel_mean`, `mtf30`, and `mtf50`.",
                "Issue #102's `mtf20` already beats PR #30 while `mtf30` and `mtf50` still lag, so the remaining readout gap is no longer a uniform amplitude miss. It now looks like an upstream observable-shape / high-frequency-tail boundary.",
                "The downstream Quality Loss record is invariant across issue #93, issue #97, and issue #102 at `overall_quality_loss_mae_mean = 3.94743`, while PR #30 is much lower at `1.22150`. That proves the residual large gap does not live in the issue-102 readout-only compensation change and still sits on the observed/downstream branch family.",
                "Compared with PR #30, issue #102 still differs on the observed-branch observable-stack knobs `calibration_file`, `texture_support_scale`, and `high_frequency_guard_start_cpp`, while the intrinsic-topology differences are the same knobs that currently preserve issue-102's stronger curve and focus-preset Acutance record."
            ],
            "comparison_basis": {
                "pr30_issue102_delta": issue102_vs_current_best,
                "pr98_issue97_vs_current_best_pr30": issue102_artifact["comparisons"][
                    "candidate_vs_current_best_pr30"
                ],
                "pr100_selected_slice_id": issue99_artifact["selected_slice_id"],
                "pr100_selected_summary": issue99_artifact["selected_summary"],
                "pr103_issue102_vs_issue97": issue102_artifact["comparisons"][
                    "candidate_vs_issue97"
                ],
                "pr104_result": (
                    "PR #104 repaired issue-102 summary-artifact provenance only and did not change "
                    "the benchmark result, so the post-issue102 narrowing should use the same "
                    "metrics published by PR #103."
                ),
            },
            "minimum_implementation_boundary": [
                "Keep issue #102's intrinsic main-acutance branch, `intrinsic_full_reference_scope`, and readout-only sensor-aperture compensation (`sensor_aperture_sinc`) unchanged.",
                "Introduce one observed-branch bundle for the reported-MTF/readout path and the downstream Quality Loss branch that uses PR #30's anchored calibration file, `texture_support_scale=True`, and `high_frequency_guard_start_cpp=0.36`.",
                "Do not move the main acutance branch back to PR #30's non-intrinsic topology, and do not promote release-facing PR30 configs directly."
            ],
            "explicitly_do_not_change": [
                "Do not drop the issue-102 intrinsic main branch back to PR #30's non-intrinsic observable stack.",
                "Do not reopen broader observable-stack, matched-ori, or intrinsic family search outside the bounded observed-branch bundle.",
                "Do not retune only the readout-only sensor-aperture compensation again as a single-knob follow-up.",
                "Do not write new fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`."
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-102-based profile that keeps readout-only sensor-aperture compensation but adds the PR30 observable-stack bundle on the observed readout branch, then compare `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` against issue #102 and PR #30.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same bounded scope to confirm `curve_mae_mean` and `focus_preset_acutance_mae_mean` stay no worse than issue #102 while `overall_quality_loss_mae_mean` improves materially.",
                "Add focused tests that prove anchored calibration, `texture_support_scale`, and `high_frequency_guard_start_cpp` affect only the observed reported-MTF / downstream Quality Loss consumers and not the issue-102 intrinsic main-acutance branch."
            ],
        },
        {
            "slice_id": "retune_readout_only_sensor_aperture_compensation_again",
            "label": "keep tuning only the readout-only sensor-aperture compensation parameters",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #102 already improved every tracked readout metric versus issue #97 and even beat PR #30 on `mtf20`, so the remaining readout gap is no longer the same single-knob amplitude problem.",
                "Overall Quality Loss never moved across issue #93, issue #97, and issue #102, so another readout-only compensation retune would not address the largest residual PR30 gap."
            ],
        },
        {
            "slice_id": "drop_intrinsic_main_branch_and_rejoin_whole_pr30_stack",
            "label": "discard the issue-102 intrinsic main branch and move the whole stack back toward PR #30",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #102 still beats PR #30 on `curve_mae_mean` and `focus_preset_acutance_mae_mean`, so collapsing the whole topology back toward PR #30 would throw away the strongest part of the current bounded record.",
                "Issue #105 is supposed to leave one direct bounded implementation slice, not reopen the full observable-stack replacement path."
            ],
        },
        {
            "slice_id": "restart_broader_observable_stack_or_intrinsic_family_search",
            "label": "restart broader observable-stack, matched-ori, or intrinsic family search",
            "decision": "exclude",
            "exclusion_reasons": [
                "The remaining issue-102 residuals are already localized: the intrinsic main branch is stable, the readout-only compensation boundary is proven, and the unchanged downstream Quality Loss record points at the observed-branch bundle.",
                "Issue #105 is a developer-discovery narrowing pass and must hand engineering one direct next implementation issue rather than another unbounded search."
            ],
        },
    ]

    payload = {
        "issue": 105,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "comparison_records": comparison_records,
        "residual_gap_evidence": residual_gap_evidence,
        "pipeline_delta_summary": pipeline_delta(issue102, current_best),
        "candidate_slices": candidate_slices,
        "source_artifacts": {
            "issue99_artifact": str(issue99_artifact_path),
            "issue102_artifact": str(issue102_artifact_path),
            "comparison_basis_refs": ["pr-30", "pr-98", "pr-100", "pr-103", "pr-104"],
        },
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue102_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep issue-105 discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write fitted profiles, transfer tables, or generated outputs under the golden/reference roots.",
                "Do not touch release-facing configs in this issue.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    records = payload["comparison_records"]
    current_best = records[CURRENT_BEST_LABEL]
    issue97 = records[ISSUE97_LABEL]
    issue102 = records[ISSUE102_LABEL]
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )

    lines = [
        "# Intrinsic After Issue 102 Next Slice",
        "",
        "This note records the issue `#105` developer-discovery pass after issue `#102` / PR `#103` / PR `#104` proved that readout-only sensor-aperture compensation is a real bounded improvement but still leaves a residual gap versus PR `#30`.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        "- Prior narrowing lineage: issue `#99` / PR `#100` / PR `#101` selected the readout-only compensation slice, and issue `#102` / PR `#103` / PR `#104` completed it cleanly enough to expose the next remaining boundary.",
        "- Remaining gap location: after issue `#102`, the intrinsic main branch and the readout-only compensation boundary are both bounded. The large residual gap now sits on the observed-branch observable stack that still feeds reported-MTF and downstream Quality Loss differently from PR `#30`.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {CURRENT_BEST_LABEL} | {format_metric(current_best['curve_mae_mean'])} | {format_metric(current_best['focus_preset_acutance_mae_mean'])} | {format_metric(current_best['overall_quality_loss_mae_mean'])} | {format_metric(current_best['mtf_threshold_mae']['mtf20'])} | {format_metric(current_best['mtf_threshold_mae']['mtf30'])} | {format_metric(current_best['mtf_threshold_mae']['mtf50'])} | {format_metric(current_best['mtf_abs_signed_rel_mean'])} | Current best PR30 branch. |",
        f"| {ISSUE97_LABEL} | {format_metric(issue97['curve_mae_mean'])} | {format_metric(issue97['focus_preset_acutance_mae_mean'])} | {format_metric(issue97['overall_quality_loss_mae_mean'])} | {format_metric(issue97['mtf_threshold_mae']['mtf20'])} | {format_metric(issue97['mtf_threshold_mae']['mtf30'])} | {format_metric(issue97['mtf_threshold_mae']['mtf50'])} | {format_metric(issue97['mtf_abs_signed_rel_mean'])} | Issue-97 mixed-negative disconnect result from PR #98. |",
        f"| {ISSUE102_LABEL} | {format_metric(issue102['curve_mae_mean'])} | {format_metric(issue102['focus_preset_acutance_mae_mean'])} | {format_metric(issue102['overall_quality_loss_mae_mean'])} | {format_metric(issue102['mtf_threshold_mae']['mtf20'])} | {format_metric(issue102['mtf_threshold_mae']['mtf30'])} | {format_metric(issue102['mtf_threshold_mae']['mtf50'])} | {format_metric(issue102['mtf_abs_signed_rel_mean'])} | Issue-102 bounded positive result from PR #103/#104. |",
        "",
        "## Residual Gap Evidence",
        "",
        f"- Issue #102 preserves issue #97 `curve_mae_mean`: `{payload['residual_gap_evidence']['issue102_preserves_issue97_core_record']['curve_mae_mean']}`",
        f"- Issue #102 preserves issue #97 `focus_preset_acutance_mae_mean`: `{payload['residual_gap_evidence']['issue102_preserves_issue97_core_record']['focus_preset_acutance_mae_mean']}`",
        f"- Issue #102 preserves issue #97 `overall_quality_loss_mae_mean`: `{payload['residual_gap_evidence']['issue102_preserves_issue97_core_record']['overall_quality_loss_mae_mean']}`",
        f"- Issue #102 improves `mtf_abs_signed_rel_mean` versus issue #97: `{payload['residual_gap_evidence']['issue102_readout_improves_but_does_not_close_pr30_gap']['mtf_abs_signed_rel_improved_vs_issue97']}`",
        f"- Issue #102 still trails PR #30 on `mtf30`: `{payload['residual_gap_evidence']['issue102_readout_improves_but_does_not_close_pr30_gap']['mtf30_still_worse_than_current_best_pr30']}`",
        f"- Issue #102 still trails PR #30 on `mtf50`: `{payload['residual_gap_evidence']['issue102_readout_improves_but_does_not_close_pr30_gap']['mtf50_still_worse_than_current_best_pr30']}`",
        f"- Issue #102 still trails PR #30 on `mtf_abs_signed_rel_mean`: `{payload['residual_gap_evidence']['issue102_readout_improves_but_does_not_close_pr30_gap']['mtf_abs_signed_rel_still_worse_than_current_best_pr30']}`",
        f"- Issue #102 already beats PR #30 on `mtf20`: `{payload['residual_gap_evidence']['issue102_readout_improves_but_does_not_close_pr30_gap']['mtf20_beats_current_best_pr30']}`",
        f"- Issue #93 / #97 / #102 keep the same downstream Quality Loss record: `{payload['residual_gap_evidence']['issue93_issue97_issue102_quality_loss_record_is_invariant']['issue93_equals_issue102']}`",
        "",
        "## Pipeline Delta Summary",
        "",
    ]
    for key, delta in payload["pipeline_delta_summary"].items():
        lines.append(
            f"- `{key}`: issue102={delta[ISSUE102_LABEL]!r}, pr30={delta[CURRENT_BEST_LABEL]!r}"
        )
    lines.extend(
        [
            "",
            "## Why The Next Slice Is The Observed-Branch PR30 Observable Stack",
            "",
            "- Issue #102 proved the readout-only sensor-aperture compensation boundary and already improved all tracked readout metrics versus issue #97, so another single-knob readout retune is no longer the highest-signal follow-up.",
            "- `overall_quality_loss_mae_mean` never changed across issue `#93`, issue `#97`, and issue `#102`, which means the residual large PR30 gap still sits on the downstream observed-branch family rather than the issue-102 intrinsic main branch.",
            "- The remaining pipeline deltas that can hit both reported-MTF and downstream Quality Loss without discarding the issue-102 intrinsic main branch are PR30's anchored calibration, `texture_support_scale`, and `high_frequency_guard_start_cpp` on the observed branch.",
            "- PR #104 changed only summary-artifact provenance, so the post-issue102 narrowing should treat PR #103 and PR #104 as the same benchmark record.",
            "",
            "## Selected Implementation Boundary",
            "",
        ]
    )
    for row in selected["minimum_implementation_boundary"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Explicit Non-Changes", ""])
    for row in selected["explicitly_do_not_change"]:
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
            f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`",
            "- Discovery outputs for this issue stay under `docs/` and `artifacts/` only.",
            "- Do not write new fitted profiles, transfer tables, or benchmark outputs under the golden/reference roots or release-facing config roots.",
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
        issue99_artifact_path=args.issue99_artifact,
        issue102_artifact_path=args.issue102_artifact,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
