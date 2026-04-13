from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue93_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE85_LABEL = "issue85_readout_reconnect_quality_loss_isolation_candidate"
ISSUE89_LABEL = "issue89_matched_ori_graft_candidate"
ISSUE93_LABEL = "issue93_downstream_matched_ori_only_candidate"
SELECTED_SLICE_ID = (
    "issue93_topology_keep_downstream_quality_loss_branch_but_disconnect_reported_mtf_from_intrinsic_reconnect"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-95 intrinsic post-issue93 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue91-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue89_next_slice_benchmark.json"),
        help="Repo-relative issue-91 discovery artifact path.",
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
        "--issue93-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"),
        help="Repo-relative issue-93 summary artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue93_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue93_next_slice.md"),
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
    keys = sorted(set(candidate_pipeline) | set(baseline_pipeline))
    return {
        key: {
            ISSUE93_LABEL: candidate_pipeline.get(key),
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
    issue91_artifact_path: Path,
    issue85_artifact_path: Path,
    issue89_artifact_path: Path,
    issue93_artifact_path: Path,
) -> dict[str, Any]:
    issue91_artifact = load_json(resolve_path(repo_root, issue91_artifact_path))
    issue85_artifact = load_json(resolve_path(repo_root, issue85_artifact_path))
    issue89_artifact = load_json(resolve_path(repo_root, issue89_artifact_path))
    issue93_artifact = load_json(resolve_path(repo_root, issue93_artifact_path))

    comparison_records = {
        CURRENT_BEST_LABEL: issue93_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE85_LABEL: issue93_artifact["profiles"][ISSUE85_LABEL],
        ISSUE89_LABEL: issue93_artifact["profiles"][ISSUE89_LABEL],
        ISSUE93_LABEL: issue93_artifact["profiles"][ISSUE93_LABEL],
    }

    current_best = comparison_records[CURRENT_BEST_LABEL]
    issue85 = comparison_records[ISSUE85_LABEL]
    issue89 = comparison_records[ISSUE89_LABEL]
    issue93 = comparison_records[ISSUE93_LABEL]

    issue93_vs_current_best = delta_map(issue93, current_best)
    issue93_vs_issue85 = delta_map(issue93, issue85)
    issue93_vs_issue89 = delta_map(issue93, issue89)

    residual_gap = {
        "issue93_preserves_issue89_quality_loss": {
            "overall_quality_loss_mae_mean": is_close(
                issue93["overall_quality_loss_mae_mean"], issue89["overall_quality_loss_mae_mean"]
            ),
            "delta": issue93_vs_issue89["overall_quality_loss_mae_mean"],
        },
        "issue93_recovers_issue89_readout": {
            "mtf_abs_signed_rel_mean": issue93["mtf_abs_signed_rel_mean"]
            < issue89["mtf_abs_signed_rel_mean"],
            "mtf_threshold_mae": {
                key: issue93["mtf_threshold_mae"][key] < issue89["mtf_threshold_mae"][key]
                for key in ("mtf20", "mtf30", "mtf50")
            },
            "delta": {
                "mtf_abs_signed_rel_mean": issue93_vs_issue89["mtf_abs_signed_rel_mean"],
                "mtf_threshold_mae": issue93_vs_issue89["mtf_threshold_mae"],
            },
        },
        "issue93_preserves_issue85_readout": {
            "mtf_abs_signed_rel_mean": is_close(
                issue93["mtf_abs_signed_rel_mean"], issue85["mtf_abs_signed_rel_mean"]
            ),
            "mtf_threshold_mae": {
                key: is_close(issue93["mtf_threshold_mae"][key], issue85["mtf_threshold_mae"][key])
                for key in ("mtf20", "mtf30", "mtf50")
            },
            "delta": {
                "mtf_abs_signed_rel_mean": issue93_vs_issue85["mtf_abs_signed_rel_mean"],
                "mtf_threshold_mae": issue93_vs_issue85["mtf_threshold_mae"],
            },
        },
        "issue93_still_trails_pr30": {
            "overall_quality_loss_mae_mean": issue93["overall_quality_loss_mae_mean"]
            > current_best["overall_quality_loss_mae_mean"],
            "mtf_abs_signed_rel_mean": issue93["mtf_abs_signed_rel_mean"]
            > current_best["mtf_abs_signed_rel_mean"],
            "mtf20": issue93["mtf_threshold_mae"]["mtf20"]
            > current_best["mtf_threshold_mae"]["mtf20"],
            "delta": issue93_vs_current_best,
        },
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "keep issue-93's downstream Quality Loss branch and disconnect reported-MTF thresholds from the intrinsic reconnect",
            "decision": "advance",
            "technical_narrowing_point": (
                "issue93_proved_that_the_downstream_quality_loss_gain_is_already_separate_from_"
                "the_intrinsic_readout_reconnect_so_the_next_minimum_slice_is_the_reported_mtf_"
                "assignment_boundary"
            ),
            "selected_summary": (
                "Keep issue #93's phase-retained intrinsic curve/main-acutance branch and "
                "downstream-only matched-ori Quality Loss branch unchanged, but stop feeding "
                "reported-MTF thresholds from the intrinsic reconnect path. Leave "
                "`compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` "
                "on the issue-93 topology, while reported-MTF extraction stays on the observed "
                "calibrated/compensated branch."
            ),
            "repo_evidence": [
                "Issue #93 preserves issue #89's `overall_quality_loss_mae_mean` exactly while recovering the entire readout regression, so the current Quality Loss gain and the current readout behavior are already on separate runtime branches.",
                "Issue #93 also preserves issue #85's `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` exactly, which means the remaining readout gap versus PR #30 is inherited from the issue-85 reconnect boundary rather than from the downstream-only matched-ori split.",
                "In `algo/benchmark_parity_psd_mtf.py`, the issue-93 scope still overwrites `compensated_mtf` with `intrinsic_mtf` before `compute_mtf_metrics(...)` reads thresholds, so one assignment now defines the whole reported-MTF branch.",
                "In `algo/benchmark_parity_acutance_quality_loss.py`, the downstream Quality Loss branch is already independent: `quality_loss_compensated_mtf_for_acutance` stays on the observed compensated stack and still receives the issue-93 downstream matched-ori correction / anchor path. That means a readout-only reconnect change can preserve the current issue-93 Quality Loss gain.",
                "The remaining Quality Loss gap to PR #30 still lives in a broader observable-stack family (`calibration_file`, `acutance_noise_scale_mode`, `high_frequency_guard_start_cpp`, `texture_support_scale`, `mtf_compensation_mode`, `sensor_fill_factor`). That family is larger than one boundary, so it is not the next smallest slice.",
            ],
            "comparison_basis": {
                "issue91_selected_slice_id": issue91_artifact["selected_slice_id"],
                "issue93_vs_current_best_pr30": {
                    "delta": issue93_vs_current_best,
                },
                "issue93_vs_issue85": {
                    "delta": issue93_vs_issue85,
                    "readout_preserved": residual_gap["issue93_preserves_issue85_readout"],
                },
                "issue93_vs_issue89": {
                    "delta": issue93_vs_issue89,
                    "quality_loss_preserved": residual_gap["issue93_preserves_issue89_quality_loss"],
                    "readout_recovered": residual_gap["issue93_recovers_issue89_readout"],
                },
            },
            "runtime_boundary_evidence": [
                {
                    "file_path": "algo/benchmark_parity_psd_mtf.py",
                    "line_range": "500-512, 675-679",
                    "observations": [
                        "For issue-93-class scopes, the PSD driver assigns `compensated_mtf = intrinsic_mtf` inside the intrinsic reconnect block.",
                        "`compute_mtf_metrics(...)` later consumes that `compensated_mtf` directly, so the reported-MTF thresholds are currently locked to the intrinsic reconnect path.",
                        "A bounded next slice can stop only this assignment while leaving the intrinsic main-acutance branch intact.",
                    ],
                },
                {
                    "file_path": "algo/benchmark_parity_acutance_quality_loss.py",
                    "line_range": "676-677, 740-746, 864-968",
                    "observations": [
                        "The Quality Loss driver creates `quality_loss_compensated_mtf_for_acutance` as a separate observed-stack copy before the intrinsic reconnect runs.",
                        "For issue-93-class scopes, the intrinsic reconnect updates only `compensated_mtf_for_acutance`; the downstream Quality Loss copy stays on its own branch unless the scope is `replace_all`.",
                        "The downstream branch still receives matched-ori correction and anchoring later, so a readout-only reconnect change can preserve issue #93's current downstream Quality Loss behavior.",
                    ],
                },
            ],
            "minimum_implementation_boundary": [
                "Keep issue #93's `readout_reconnect_quality_loss_isolation_downstream_matched_ori_only` topology, intrinsic transfer mode, registration mode, and downstream matched-ori Quality Loss subfamily unchanged.",
                "Add one bounded scope or profile family that leaves `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the issue-93 branches, but no longer overwrites `compensated_mtf` with `intrinsic_mtf` before reported-MTF threshold extraction.",
                "Use the observed calibrated/compensated readout stack for `compute_mtf_metrics(...)` only; do not retune release-facing coefficients, calibration families, or the downstream Quality Loss observable stack yet.",
            ],
            "explicitly_do_not_change": [
                "Do not reopen the intrinsic transfer family, measured OECF family, or affine-registration variants.",
                "Do not reapply matched-ori correction to the reported-MTF/readout path.",
                "Do not touch issue #93's downstream-only matched-ori Quality Loss branch or promote issue #93 directly as a main-line branch.",
                "Do not rewrite release-facing PR30 configs or write fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The new bounded implementation keeps `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` no worse than issue #93.",
                "The same implementation improves `mtf20` and `mtf_abs_signed_rel_mean` versus issue #93 by moving the reported-MTF readout path toward the PR #30 side.",
                "The implementation keeps the downstream-only matched-ori Quality Loss branch isolated from the reported-MTF path.",
                "All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-93-based profile that disconnects only the reported-MTF readout path from the intrinsic reconnect, then compare `mtf20` and `mtf_abs_signed_rel_mean` against issue #93 and PR #30.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same scope to confirm `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` stay at or below issue #93.",
                "Add focused tests that prove `compensated_mtf` stays on the observed calibrated/compensated path while `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` remain on the existing issue-93 branches.",
            ],
        },
        {
            "slice_id": "bundle_pr30_observable_stack_into_issue93_now",
            "label": "bundle PR30's entire observable stack into issue-93 now",
            "decision": "exclude",
            "exclusion_reasons": [
                "The remaining Quality Loss gap does point at a broader observable-stack family, but that family still contains multiple live knobs instead of one minimum boundary.",
                "Issue #95 is a narrowing pass, so it should not jump directly into a multi-knob calibration / noise-share / texture-support / compensation bundle before the readout reconnect boundary is isolated.",
            ],
        },
        {
            "slice_id": "reopen_issue89_full_matched_ori_graft",
            "label": "reopen the full issue-89 readout+Quality-Loss matched-ori graft",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #93 already proved that the safe matched-ori value is the downstream-only subfamily, and the full issue-89 graft reintroduces the known readout regression.",
                "Replaying the same combined matched-ori boundary would not shrink the residual PR30 gap any further.",
            ],
        },
        {
            "slice_id": "restart_intrinsic_or_measured_oecf_family_search",
            "label": "restart the intrinsic family or measured-OECF search",
            "decision": "exclude",
            "exclusion_reasons": [
                "The current residual gap is downstream of issue #93's already-bounded topology and does not justify reopening whole-family search.",
                "Measured OECF closed as a bounded negative in issue #77 / PR #78, and affine-registration intrinsic was already excluded earlier in the chain.",
            ],
        },
    ]

    payload = {
        "issue": 95,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue91_summary_artifact": str(issue91_artifact_path),
            "issue91_selected_slice_id": issue91_artifact["selected_slice_id"],
            "issue93_summary_artifact": str(issue93_artifact_path),
            "issue93_conclusion_status": issue93_artifact["conclusion"]["status"],
        },
        "comparison_records": comparison_records,
        "residual_gap_evidence": residual_gap,
        "pipeline_delta_summary": pipeline_delta(issue93, current_best),
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue93_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep this issue's discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Do not touch release-facing configs until a later bounded implementation clears the current README-facing guardrails.",
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
    residual = payload["residual_gap_evidence"]

    lines = [
        "# Intrinsic After Issue 93 Next Slice",
        "",
        "This note records the issue `#95` developer-discovery pass after issue `#93` / PR `#94` proved that the downstream-only matched-ori branch is a safe bounded improvement but still leaves a residual PR `#30` gap.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        f"- Prior narrowing lineage: issue `#91` selected `{payload['source_artifacts']['issue91_selected_slice_id']}`, and issue `#93` implemented that downstream-only matched-ori branch successfully enough to expose the next live boundary.",
        "- Remaining gap location: after issue #93, the safe downstream Quality Loss gain is already isolated. The next minimum slice is the reported-MTF reconnect boundary itself, while the remaining Quality Loss gap stays on a broader downstream observable-stack family for later work.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    descriptions = {
        CURRENT_BEST_LABEL: "Current best PR30 branch.",
        ISSUE85_LABEL: "Issue-81 plus readout reconnect; readout thresholds now follow the intrinsic reconnect path.",
        ISSUE89_LABEL: "Issue-85 plus matched-ori graft; Quality Loss improves, readout regresses sharply.",
        ISSUE93_LABEL: "Issue-85 readout path plus issue-89 downstream-only Quality Loss gain.",
    }
    for key in (CURRENT_BEST_LABEL, ISSUE85_LABEL, ISSUE89_LABEL, ISSUE93_LABEL):
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
            "## Residual Gap Evidence",
            "",
            f"- Issue #93 preserves issue #89 `overall_quality_loss_mae_mean`: `{residual['issue93_preserves_issue89_quality_loss']['overall_quality_loss_mae_mean']}`",
            f"- Issue #93 Quality Loss delta versus issue #89: `{residual['issue93_preserves_issue89_quality_loss']['delta']:.5f}`",
            f"- Issue #93 recovers issue #89 `mtf_abs_signed_rel_mean`: `{residual['issue93_recovers_issue89_readout']['mtf_abs_signed_rel_mean']}`",
            f"- Issue #93 threshold recoveries versus issue #89: `mtf20={residual['issue93_recovers_issue89_readout']['mtf_threshold_mae']['mtf20']}`, `mtf30={residual['issue93_recovers_issue89_readout']['mtf_threshold_mae']['mtf30']}`, `mtf50={residual['issue93_recovers_issue89_readout']['mtf_threshold_mae']['mtf50']}`",
            f"- Issue #93 preserves issue #85 `mtf_abs_signed_rel_mean`: `{residual['issue93_preserves_issue85_readout']['mtf_abs_signed_rel_mean']}`",
            f"- Issue #93 threshold equality versus issue #85: `mtf20={residual['issue93_preserves_issue85_readout']['mtf_threshold_mae']['mtf20']}`, `mtf30={residual['issue93_preserves_issue85_readout']['mtf_threshold_mae']['mtf30']}`, `mtf50={residual['issue93_preserves_issue85_readout']['mtf_threshold_mae']['mtf50']}`",
            f"- Issue #93 still trails PR #30 on overall Quality Loss: `{residual['issue93_still_trails_pr30']['overall_quality_loss_mae_mean']}`",
            f"- Issue #93 still trails PR #30 on `mtf20`: `{residual['issue93_still_trails_pr30']['mtf20']}`",
            f"- Issue #93 still trails PR #30 on `mtf_abs_signed_rel_mean`: `{residual['issue93_still_trails_pr30']['mtf_abs_signed_rel_mean']}`",
            "",
            "## Pipeline Delta Between Issue 93 And PR30",
            "",
        ]
    )
    for key, values in payload["pipeline_delta_summary"].items():
        lines.append(
            f"- `{key}`: issue93={values[ISSUE93_LABEL]!r}, pr30={values[CURRENT_BEST_LABEL]!r}"
        )

    lines.extend(
        [
            "",
            "## Why The Next Slice Is The Readout Reconnect Boundary",
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
        issue91_artifact_path=args.issue91_artifact,
        issue85_artifact_path=args.issue85_artifact,
        issue89_artifact_path=args.issue89_artifact,
        issue93_artifact_path=args.issue93_artifact,
    )
    output_json = resolve_path(args.repo_root, args.output_json)
    output_md = resolve_path(args.repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
