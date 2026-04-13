from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue89_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE81_LABEL = "issue81_quality_loss_isolation_candidate"
ISSUE85_LABEL = "issue85_readout_reconnect_quality_loss_isolation_candidate"
ISSUE89_LABEL = "issue89_matched_ori_graft_candidate"
SELECTED_SLICE_ID = (
    "phase_retained_intrinsic_quality_loss_only_matched_ori_graft_without_readout_correction"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-91 intrinsic post-issue89 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue87-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue85_next_slice_benchmark.json"),
        help="Repo-relative issue-87 discovery artifact path.",
    )
    parser.add_argument(
        "--issue81-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"),
        help="Repo-relative issue-81 summary artifact path.",
    )
    parser.add_argument(
        "--issue85-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"),
        help="Repo-relative issue-85 summary artifact path.",
    )
    parser.add_argument(
        "--issue89-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"),
        help="Repo-relative issue-89 summary artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue89_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue89_next_slice.md"),
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


def pipeline_delta(issue85: dict[str, Any], issue89: dict[str, Any]) -> dict[str, Any]:
    issue85_pipeline = issue85["analysis_pipeline"]
    issue89_pipeline = issue89["analysis_pipeline"]
    keys = sorted(set(issue85_pipeline) | set(issue89_pipeline))
    return {
        key: {
            ISSUE85_LABEL: issue85_pipeline.get(key),
            ISSUE89_LABEL: issue89_pipeline.get(key),
        }
        for key in keys
        if issue85_pipeline.get(key) != issue89_pipeline.get(key)
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(
    repo_root: Path,
    *,
    issue87_artifact_path: Path,
    issue81_artifact_path: Path,
    issue85_artifact_path: Path,
    issue89_artifact_path: Path,
) -> dict[str, Any]:
    issue87_artifact = load_json(resolve_path(repo_root, issue87_artifact_path))
    issue81_artifact = load_json(resolve_path(repo_root, issue81_artifact_path))
    issue85_artifact = load_json(resolve_path(repo_root, issue85_artifact_path))
    issue89_artifact = load_json(resolve_path(repo_root, issue89_artifact_path))

    comparison_records = {
        CURRENT_BEST_LABEL: issue89_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE81_LABEL: issue81_artifact["profiles"][ISSUE81_LABEL],
        ISSUE85_LABEL: issue89_artifact["profiles"][ISSUE85_LABEL],
        ISSUE89_LABEL: issue89_artifact["profiles"][ISSUE89_LABEL],
    }

    current_best = comparison_records[CURRENT_BEST_LABEL]
    issue81 = comparison_records[ISSUE81_LABEL]
    issue85 = comparison_records[ISSUE85_LABEL]
    issue89 = comparison_records[ISSUE89_LABEL]

    issue89_vs_issue85 = delta_map(issue89, issue85)
    issue89_vs_issue81 = delta_map(issue89, issue81)
    issue89_vs_current_best = delta_map(issue89, current_best)

    residual_tradeoff = {
        "issue89_preserves_issue85_main_path": {
            "curve_mae_mean": is_close(issue89["curve_mae_mean"], issue85["curve_mae_mean"]),
            "focus_preset_acutance_mae_mean": is_close(
                issue89["focus_preset_acutance_mae_mean"],
                issue85["focus_preset_acutance_mae_mean"],
            ),
        },
        "issue89_improves_quality_loss_vs_issue85": {
            "overall_quality_loss_mae_mean": issue89["overall_quality_loss_mae_mean"]
            < issue85["overall_quality_loss_mae_mean"],
            "delta": issue89_vs_issue85["overall_quality_loss_mae_mean"],
        },
        "issue89_regresses_readout_vs_issue85": {
            "mtf_abs_signed_rel_mean": issue89["mtf_abs_signed_rel_mean"]
            > issue85["mtf_abs_signed_rel_mean"],
            "mtf_threshold_mae": {
                key: issue89["mtf_threshold_mae"][key] > issue85["mtf_threshold_mae"][key]
                for key in ("mtf20", "mtf30", "mtf50")
            },
            "delta": {
                "mtf_abs_signed_rel_mean": issue89_vs_issue85["mtf_abs_signed_rel_mean"],
                "mtf_threshold_mae": issue89_vs_issue85["mtf_threshold_mae"],
            },
        },
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "keep only the isolated downstream matched-ori correction / anchor subfamily from issue-89",
            "decision": "advance",
            "technical_narrowing_point": (
                "issue89_proved_that_quality_loss_gain_and_readout_regression_live_on_different_"
                "sub_boundaries_inside_the_same_matched_ori_graft"
            ),
            "selected_summary": (
                "Keep issue #85's phase-retained intrinsic transfer, readout reconnect, and "
                "downstream Quality Loss isolation, but carry forward only issue #89's matched-ori "
                "correction / acutance-anchor on the isolated downstream Quality Loss branch. Do "
                "not reapply matched-ori reference correction to the reported-MTF/readout path."
            ),
            "repo_evidence": [
                "Issue #89 preserves issue #85's `curve_mae_mean` and `focus_preset_acutance_mae_mean` exactly, so the residual tradeoff does not require reopening the main intrinsic curve/acutance branch.",
                "Issue #89 still improves `overall_quality_loss_mae_mean` versus both issue #81 and issue #85 by `4.07311`, which means the matched-ori value that appeared in issue #89 is downstream and real rather than noise from the readout reconnect itself.",
                "Issue #89 simultaneously regresses `mtf_abs_signed_rel_mean` by `0.60778` versus issue #85, and all three threshold errors (`mtf20`, `mtf30`, `mtf50`) get worse. That points to the readout-side matched-ori reference correction on `compensated_mtf`, not to the isolated Quality Loss branch.",
                "The changed pipeline keys from issue #85 to issue #89 are entirely the matched-ori reference-correction and acutance-anchor families, so the next narrowing pass can stay bounded to those subfamilies instead of reopening intrinsic transfer, measured OECF, or registration choice.",
            ],
            "comparison_basis": {
                "issue87_selected_slice_id": issue87_artifact["selected_slice_id"],
                "issue89_vs_current_best_pr30": {
                    "delta": issue89_vs_current_best,
                },
                "issue89_vs_issue81": {
                    "delta": issue89_vs_issue81,
                },
                "issue89_vs_issue85": {
                    "delta": issue89_vs_issue85,
                    "main_path_preserved": residual_tradeoff["issue89_preserves_issue85_main_path"],
                    "quality_loss_improved": residual_tradeoff["issue89_improves_quality_loss_vs_issue85"],
                    "readout_regressed": residual_tradeoff["issue89_regresses_readout_vs_issue85"],
                },
            },
            "runtime_boundary_evidence": [
                {
                    "file_path": "algo/benchmark_parity_psd_mtf.py",
                    "line_range": "504-653, 684-689",
                    "observations": [
                        "For `readout_reconnect_quality_loss_isolation_matched_ori_graft`, the intrinsic branch is still connected into `compensated_mtf`, and `apply_readout_correction` becomes true only for this scope.",
                        "That branch applies `apply_reference_correction_curve(...)` directly to `compensated_mtf` using the matched-ori strength-curve settings.",
                        "`compute_mtf_metrics(...)` then reads thresholds from the corrected `compensated_mtf`, so this is the narrowest live boundary for the issue-89 readout regression.",
                    ],
                },
                {
                    "file_path": "algo/benchmark_parity_acutance_quality_loss.py",
                    "line_range": "843-862, 922-953, 1003-1008",
                    "observations": [
                        "For the issue-89 scope, the main `compensated_mtf_for_acutance` correction path is skipped, and the main curve/acutance path also skips `maybe_anchor_acutance_results(...)`.",
                        "The isolated downstream branch still applies matched-ori correction to `quality_loss_compensated_mtf_for_acutance`, and `quality_loss_acutance` still passes through `maybe_anchor_acutance_results(...)`.",
                        "`quality_loss_presets_from_acutance(...)` consumes only that isolated downstream branch, so the next bounded slice can preserve the issue-89 Quality Loss gain while leaving readout and the main acutance path unchanged.",
                    ],
                },
            ],
            "minimum_implementation_boundary": [
                "Keep issue #85's `readout_reconnect_quality_loss_isolation` topology and the existing phase-retained intrinsic transfer / registration path unchanged.",
                "Add one bounded scope or profile family that enables the issue-89 matched-ori correction curve only on `quality_loss_compensated_mtf_for_acutance` and keeps the downstream `matched_ori_acutance_reference_anchor` path active for `quality_loss_acutance` only.",
                "Do not apply matched-ori reference correction to `compensated_mtf`, and do not change the reported-MTF/readout threshold extraction path.",
                "Do not enable matched-ori correction or anchoring on the main `compensated_mtf_for_acutance` / curve / preset path.",
            ],
            "explicitly_do_not_change": [
                "Do not change intrinsic transfer mode, registration mode, or restart a wider intrinsic-family sweep.",
                "Do not reopen measured OECF or affine-registration variants.",
                "Do not reapply the full issue-89 readout+Quality-Loss graft to the readout path, and do not promote issue #89 as a main-line branch.",
                "Do not retune release-facing PR30 coefficients directly or write fitted outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The new bounded implementation keeps `curve_mae_mean` and `focus_preset_acutance_mae_mean` no worse than issue #85.",
                "The same implementation improves `overall_quality_loss_mae_mean` versus issue #85 while preserving downstream Quality Loss isolation.",
                "The same implementation keeps `mtf20` and `mtf_abs_signed_rel_mean` no worse than issue #85 because the readout path is no longer matched-ori corrected.",
                "All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on an issue-85-based profile that enables only the isolated downstream matched-ori correction / anchor path, then compare `overall_quality_loss_mae_mean` against issue #85 and issue #89.",
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the same scope to confirm `mtf20`, `mtf30`, `mtf50`, and `mtf_abs_signed_rel_mean` stay at or below issue #85 instead of replaying issue #89's regression.",
                "Add focused tests that prove `compensated_mtf` and the main acutance branch stay untouched while `quality_loss_compensated_mtf_for_acutance` and `quality_loss_acutance` still receive the bounded matched-ori subfamily.",
            ],
        },
        {
            "slice_id": "reapply_issue89_readout_and_quality_loss_graft_as_is",
            "label": "reapply the full issue-89 readout+Quality-Loss graft as-is",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #89 already established that the full graft materially improves Quality Loss but sharply regresses the readout path.",
                "Repeating the same combined boundary would not narrow the residual tradeoff any further.",
            ],
        },
        {
            "slice_id": "expand_matched_ori_into_main_acutance_branch",
            "label": "expand matched-ori correction / anchor into the main acutance branch",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #89 preserves issue #85's curve and focus-preset Acutance exactly while already skipping the main-branch matched-ori acutance correction / anchor path.",
                "That means the remaining tradeoff is not asking for more matched-ori churn on the main acutance branch.",
            ],
        },
        {
            "slice_id": "reopen_measured_oecf_family",
            "label": "reopen measured OECF",
            "decision": "exclude",
            "exclusion_reasons": [
                "Measured OECF already closed as a bounded negative in issue #77 / PR #78.",
                "Issue #91 is downstream of issue #89's matched-ori split result, and the remaining evidence is entirely inside the existing matched-ori boundary.",
            ],
        },
        {
            "slice_id": "rerun_affine_registration_intrinsic",
            "label": "rerun affine-registration intrinsic variant",
            "decision": "exclude",
            "exclusion_reasons": [
                "Affine registration was already dominated by the phase-correlation intrinsic path and remains out of scope for this narrowing pass.",
                "Issue #89 changed only matched-ori correction / anchor fields, so registration choice is not the live residual question.",
            ],
        },
        {
            "slice_id": "restart_unbounded_matched_ori_inventory",
            "label": "restart an unbounded matched-ori family search",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #91 is a developer-discovery narrowing pass, not a license to reopen the whole matched-ori family inventory.",
                "The repo already contains one implementable next slice with code-level evidence that splits the readout and downstream Quality Loss sub-boundaries.",
            ],
        },
    ]

    payload = {
        "issue": 91,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue87_summary_artifact": str(issue87_artifact_path),
            "issue87_selected_slice_id": issue87_artifact["selected_slice_id"],
            "issue89_summary_artifact": str(issue89_artifact_path),
            "issue89_conclusion_status": issue89_artifact["conclusion"]["status"],
        },
        "comparison_records": comparison_records,
        "residual_tradeoff_evidence": residual_tradeoff,
        "pipeline_delta_summary": pipeline_delta(issue85, issue89),
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue89_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep this issue's discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Do not touch release-facing configs until a later bounded implementation actually clears the current README-facing guardrails.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )
    records = payload["comparison_records"]
    tradeoff = payload["residual_tradeoff_evidence"]

    lines = [
        "# Intrinsic After Issue 89 Next Slice",
        "",
        "This note records the issue `#91` developer-discovery pass after issue `#89` / PR `#90` proved that the matched-ori graft contains a real downstream Quality Loss win and a separate readout-side regression.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        f"- Prior narrowing lineage: issue `#87` selected `{payload['source_artifacts']['issue87_selected_slice_id']}`, and issue `#89` implemented that combined graft successfully enough to expose the remaining sub-boundary split.",
        "- Remaining gap location: the residual tradeoff is no longer a whole matched-ori family question. It now sits between the readout-side reference correction on `compensated_mtf` and the isolated downstream Quality Loss correction / anchor path.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    descriptions = {
        CURRENT_BEST_LABEL: "Current best PR30 branch.",
        ISSUE81_LABEL: "Phase-retained intrinsic with downstream Quality Loss isolation only.",
        ISSUE85_LABEL: "Issue-81 plus readout reconnect; Quality Loss still unchanged from issue-81.",
        ISSUE89_LABEL: "Issue-85 plus matched-ori graft; Quality Loss improves, readout regresses.",
    }
    for key in (CURRENT_BEST_LABEL, ISSUE81_LABEL, ISSUE85_LABEL, ISSUE89_LABEL):
        record = records[key]
        mtf = record["mtf_threshold_mae"]
        lines.append(
            f"| {key} | "
            f"{format_metric(record['curve_mae_mean'])} | "
            f"{format_metric(record['focus_preset_acutance_mae_mean'])} | "
            f"{format_metric(record['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(mtf['mtf20'])} | "
            f"{format_metric(mtf['mtf30'])} | "
            f"{format_metric(mtf['mtf50'])} | "
            f"{format_metric(record['mtf_abs_signed_rel_mean'])} | "
            f"{descriptions[key]} |"
        )

    lines.extend(
        [
            "",
            "## Residual Tradeoff Evidence",
            "",
            f"- Issue #89 preserves issue #85 `curve_mae_mean`: `{tradeoff['issue89_preserves_issue85_main_path']['curve_mae_mean']}`",
            f"- Issue #89 preserves issue #85 `focus_preset_acutance_mae_mean`: `{tradeoff['issue89_preserves_issue85_main_path']['focus_preset_acutance_mae_mean']}`",
            f"- Issue #89 improves overall Quality Loss versus issue #85: `{tradeoff['issue89_improves_quality_loss_vs_issue85']['overall_quality_loss_mae_mean']}`",
            f"- Issue #89 overall Quality Loss delta versus issue #85: `{tradeoff['issue89_improves_quality_loss_vs_issue85']['delta']:.5f}`",
            f"- Issue #89 regresses `mtf_abs_signed_rel_mean` versus issue #85: `{tradeoff['issue89_regresses_readout_vs_issue85']['mtf_abs_signed_rel_mean']}`",
            f"- Issue #89 threshold regressions versus issue #85: `mtf20={tradeoff['issue89_regresses_readout_vs_issue85']['mtf_threshold_mae']['mtf20']}`, `mtf30={tradeoff['issue89_regresses_readout_vs_issue85']['mtf_threshold_mae']['mtf30']}`, `mtf50={tradeoff['issue89_regresses_readout_vs_issue85']['mtf_threshold_mae']['mtf50']}`",
            "",
            "## Pipeline Delta Between Issue 85 And Issue 89",
            "",
        ]
    )
    for key, values in payload["pipeline_delta_summary"].items():
        lines.append(
            f"- `{key}`: issue85={values[ISSUE85_LABEL]!r}, issue89={values[ISSUE89_LABEL]!r}"
        )

    lines.extend(
        [
            "",
            "## Why The Next Slice Is Smaller Than Issue 89",
            "",
        ]
    )
    for reason in selected["repo_evidence"]:
        lines.append(f"- {reason}")

    lines.extend(
        [
            "",
            "## Runtime Boundary Evidence",
            "",
        ]
    )
    for item in selected["runtime_boundary_evidence"]:
        lines.append(f"### `{item['file_path']}` ({item['line_range']})")
        lines.append("")
        for observation in item["observations"]:
            lines.append(f"- {observation}")
        lines.append("")

    lines.extend(
        [
            "## Implementation Boundary",
            "",
        ]
    )
    for entry in selected["minimum_implementation_boundary"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Explicit Non-Changes",
            "",
        ]
    )
    for entry in selected["explicitly_do_not_change"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Excluded Routes",
            "",
        ]
    )
    for row in payload["candidate_slices"]:
        if row["decision"] != "exclude":
            continue
        lines.append(f"### `{row['slice_id']}`")
        lines.append("")
        lines.append(f"- Route: {row['label']}")
        for reason in row["exclusion_reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    lines.extend(
        [
            "## Acceptance For The Next Implementation Issue",
            "",
        ]
    )
    for entry in selected["acceptance_criteria_for_next_issue"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Validation Plan For The Next Implementation Issue",
            "",
        ]
    )
    for entry in selected["validation_plan_for_next_issue"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Storage Separation",
            "",
            f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`",
            "- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`",
            "- Release config roots: `release/deadleaf_13b10_release/config/*.json`",
        ]
    )
    for rule in payload["storage_policy"]["rules"]:
        lines.append(f"- {rule}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_payload(
        args.repo_root,
        issue87_artifact_path=args.issue87_artifact,
        issue81_artifact_path=args.issue81_artifact,
        issue85_artifact_path=args.issue85_artifact,
        issue89_artifact_path=args.issue89_artifact,
    )
    output_json = resolve_path(args.repo_root, args.output_json)
    output_md = resolve_path(args.repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
