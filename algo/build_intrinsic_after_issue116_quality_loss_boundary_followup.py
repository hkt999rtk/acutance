from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from algo.build_intrinsic_after_issue114_quality_loss_boundary_followup import (
    COMPUTER_MONITOR_QUALITY_LOSS,
    CURRENT_BEST_LABEL,
    GOLDEN_REFERENCE_ROOTS,
    ISSUE108_LABEL,
    ISSUE114_LABEL,
    PR30_INPUT_PROFILE_PATH,
    SMALL_PRINT_QUALITY_LOSS,
    assert_storage_separation,
    delta_map,
    format_metric,
    load_json,
    resolve_path,
    select_profile,
)


ISSUE116_LABEL = "issue116_small_print_quality_loss_input_boundary_candidate"
CANDIDATE_LABEL = "issue118_large_print_quality_loss_input_boundary_candidate"
SUMMARY_KIND = "intrinsic_after_issue116_quality_loss_boundary_followup"
LARGE_PRINT_QUALITY_LOSS = "Large Print Quality Loss"
SELECTED_SLICE_ID = "issue116_large_print_quality_loss_preset_boundary"
ISSUE116_PROFILE_PATH = (
    "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
    "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_"
    "matched_ori_only_computer_monitor_small_print_pr30_input_profile.json"
)
CANDIDATE_PROFILE_PATH = (
    "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
    "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_"
    "matched_ori_only_computer_monitor_small_print_large_print_pr30_input_profile.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-118 Large Print Quality Loss boundary summary."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue116-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue114_quality_loss_boundary_benchmark.json"),
        help="Repo-relative issue-116 summary artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"),
        help="Repo-relative issue-118 acutance/Quality Loss benchmark artifact path.",
    )
    parser.add_argument(
        "--psd-artifact",
        type=Path,
        default=Path("artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"),
        help="Repo-relative issue-118 PSD/MTF benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue116_quality_loss_boundary.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def summarize_candidate(
    *,
    acutance_payload: dict[str, Any],
    psd_payload: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    acutance_profile = select_profile(acutance_payload, profile_path)
    psd_profile = select_profile(psd_payload, profile_path)
    acutance_overall = acutance_profile["overall"]
    psd_overall = psd_profile["overall"]
    return {
        "label": CANDIDATE_LABEL,
        "profile_path": profile_path,
        "analysis_pipeline": acutance_profile["analysis_pipeline"],
        "curve_mae_mean": float(acutance_overall["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            acutance_overall["acutance_focus_preset_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(acutance_overall["overall_quality_loss_mae_mean"]),
        "quality_loss_preset_mae": {
            key: float(value) for key, value in acutance_overall["quality_loss_preset_mae"].items()
        },
        "acutance_preset_mae": {
            key: float(value) for key, value in acutance_overall["acutance_preset_mae"].items()
        },
        "mtf_abs_signed_rel_mean": float(psd_overall["mtf_abs_signed_rel_mean"]),
        "mtf_threshold_mae": {
            key: float(value) for key, value in psd_overall["mtf_threshold_mae"].items()
        },
    }


def build_conclusion(acceptance: dict[str, bool], candidate_vs_pr30: dict[str, Any]) -> dict[str, str]:
    if acceptance["all_issue118_gates_pass"]:
        if candidate_vs_pr30["overall_quality_loss_mae_mean"] <= 0.0:
            return {
                "status": "issue118_current_best_candidate",
                "summary": (
                    "The Large Print-only Quality Loss input boundary closes the residual overall "
                    "Quality Loss delta while preserving issue-116's Computer Monitor and Small "
                    "Print improvements plus reported-MTF parity."
                ),
                "next_step": "Promote the candidate for review against the current PR #30 branch.",
            }
        return {
            "status": "issue118_positive_partial_result",
            "summary": (
                "The Large Print-only Quality Loss input boundary improves the largest remaining "
                "residual preset and overall Quality Loss versus issue #116, but a residual still "
                "remains versus PR #30."
            ),
            "next_step": (
                "Keep this as the issue-118 bounded implementation record and split the next "
                "residual Quality Loss boundary from the checked-in candidate-vs-PR30 deltas."
            ),
        }
    return {
        "status": "issue118_bounded_negative_or_mixed_result",
        "summary": (
            "The Large Print-only Quality Loss input boundary did not satisfy every issue-118 gate, "
            "so the issue should close as a bounded tradeoff record rather than broadening scope."
        ),
        "next_step": "Use the failed gates to decide whether another bounded discovery pass is warranted.",
    }


def build_payload(
    repo_root: Path,
    *,
    issue116_summary_path: Path,
    acutance_artifact_path: Path,
    psd_artifact_path: Path,
) -> dict[str, Any]:
    issue116_summary = load_json(resolve_path(repo_root, issue116_summary_path))
    acutance_payload = load_json(resolve_path(repo_root, acutance_artifact_path))
    psd_payload = load_json(resolve_path(repo_root, psd_artifact_path))

    summary_profiles = issue116_summary["profiles"]
    current_best = summary_profiles[CURRENT_BEST_LABEL]
    issue108 = summary_profiles[ISSUE108_LABEL]
    issue114 = summary_profiles[ISSUE114_LABEL]
    issue116 = summary_profiles[ISSUE116_LABEL]
    candidate = summarize_candidate(
        acutance_payload=acutance_payload,
        psd_payload=psd_payload,
        profile_path=CANDIDATE_PROFILE_PATH,
    )

    candidate_vs_issue116 = delta_map(candidate, issue116)
    candidate_vs_pr30 = delta_map(candidate, current_best)
    issue116_vs_pr30 = delta_map(issue116, current_best)

    unchanged_quality_loss_presets = {
        preset: delta == 0.0
        for preset, delta in candidate_vs_issue116["quality_loss_preset_mae"].items()
        if preset != LARGE_PRINT_QUALITY_LOSS
    }
    reported_mtf_equal_issue116 = {
        "mtf_abs_signed_rel_mean": candidate_vs_issue116["mtf_abs_signed_rel_mean"] == 0.0,
        "mtf20": candidate_vs_issue116["mtf_threshold_mae"]["mtf20"] == 0.0,
        "mtf30": candidate_vs_issue116["mtf_threshold_mae"]["mtf30"] == 0.0,
        "mtf50": candidate_vs_issue116["mtf_threshold_mae"]["mtf50"] == 0.0,
    }
    pipeline = candidate["analysis_pipeline"]
    expected_overrides = {
        COMPUTER_MONITOR_QUALITY_LOSS: PR30_INPUT_PROFILE_PATH,
        SMALL_PRINT_QUALITY_LOSS: PR30_INPUT_PROFILE_PATH,
        LARGE_PRINT_QUALITY_LOSS: PR30_INPUT_PROFILE_PATH,
    }
    acceptance = {
        "selected_slice_matches_issue118": SELECTED_SLICE_ID
        == "issue116_large_print_quality_loss_preset_boundary",
        "large_print_quality_loss_improved_vs_issue116": (
            candidate_vs_issue116["quality_loss_preset_mae"][LARGE_PRINT_QUALITY_LOSS] < -0.01
        ),
        "overall_quality_loss_improved_vs_issue116": (
            candidate_vs_issue116["overall_quality_loss_mae_mean"] < -0.01
        ),
        "computer_monitor_quality_loss_preserved_vs_issue116": (
            candidate_vs_issue116["quality_loss_preset_mae"][COMPUTER_MONITOR_QUALITY_LOSS] == 0.0
        ),
        "small_print_quality_loss_preserved_vs_issue116": (
            candidate_vs_issue116["quality_loss_preset_mae"][SMALL_PRINT_QUALITY_LOSS] == 0.0
        ),
        "curve_mae_non_worse_than_issue116": candidate_vs_issue116["curve_mae_mean"] <= 0.0,
        "focus_preset_acutance_non_worse_than_issue116": (
            candidate_vs_issue116["focus_preset_acutance_mae_mean"] <= 0.0
        ),
        "reported_mtf_equal_to_issue116": all(reported_mtf_equal_issue116.values()),
        "only_large_print_quality_loss_input_added": (
            pipeline.get("quality_loss_preset_input_profile_overrides") == expected_overrides
            and all(unchanged_quality_loss_presets.values())
        ),
        "quality_loss_coefficients_preserved": (
            pipeline["quality_loss_coefficients"]
            == issue116["analysis_pipeline"]["quality_loss_coefficients"]
            == current_best["analysis_pipeline"]["quality_loss_coefficients"]
            and pipeline["quality_loss_om_ceiling"]
            == issue116["analysis_pipeline"]["quality_loss_om_ceiling"]
            == current_best["analysis_pipeline"]["quality_loss_om_ceiling"]
            and pipeline["quality_loss_preset_overrides"]
            == issue116["analysis_pipeline"]["quality_loss_preset_overrides"]
            == current_best["analysis_pipeline"]["quality_loss_preset_overrides"]
        ),
    }
    acceptance["all_issue118_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 118,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "dataset_root": acutance_payload["dataset_root"],
        "profiles": {
            CURRENT_BEST_LABEL: current_best,
            ISSUE108_LABEL: issue108,
            ISSUE114_LABEL: issue114,
            ISSUE116_LABEL: issue116,
            CANDIDATE_LABEL: candidate,
        },
        "comparisons": {
            "issue116_vs_current_best_pr30": {"delta": issue116_vs_pr30},
            "candidate_vs_issue116": {"delta": candidate_vs_issue116},
            "candidate_vs_current_best_pr30": {"delta": candidate_vs_pr30},
        },
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_source": {
                "issue": 118,
                "selected_slice_id": SELECTED_SLICE_ID,
            },
            "basis_profile_path": ISSUE116_PROFILE_PATH,
            "candidate_profile_path": CANDIDATE_PROFILE_PATH,
            "quality_loss_preset_input_profile_overrides": pipeline[
                "quality_loss_preset_input_profile_overrides"
            ],
            "reported_mtf_equal_to_issue116": reported_mtf_equal_issue116,
            "unchanged_non_target_quality_loss_presets": unchanged_quality_loss_presets,
            "change": (
                "Keep issue-116's Computer Monitor and Small Print Quality Loss input overrides "
                "and add only `Large Print Quality Loss` to the PR #30-compatible acutance-only/"
                "noise-share anchor input."
            ),
        },
        "conclusion": build_conclusion(acceptance, candidate_vs_pr30),
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                CANDIDATE_PROFILE_PATH,
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json",
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json",
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json",
            ],
            "rules": [
                "Keep issue-118 fitted outputs under `algo/` and `artifacts/` only.",
                "Do not write fitted profiles, transfer tables, or generated outputs under golden/reference roots.",
                "Do not touch release-facing configs in this issue.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    profiles = payload["profiles"]
    current_best = profiles[CURRENT_BEST_LABEL]
    issue116 = profiles[ISSUE116_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    candidate_vs_issue116 = payload["comparisons"]["candidate_vs_issue116"]["delta"]
    candidate_vs_pr30 = payload["comparisons"]["candidate_vs_current_best_pr30"]["delta"]

    lines = [
        "# Intrinsic After Issue 116 Quality Loss Boundary",
        "",
        "Issue `#118` implements the bounded slice after issue `#116`: isolate only the `Large Print Quality Loss` preset-family input boundary while preserving the Computer Monitor and Small Print improvements plus reported-MTF parity.",
        "",
        "## Scope",
        "",
        f"- Basis issue `#116` profile: `{ISSUE116_PROFILE_PATH}`",
        f"- Candidate profile: `{CANDIDATE_PROFILE_PATH}`",
        "- Targeted added override: `Large Print Quality Loss` uses the PR `#30` acutance-only / noise-share anchor input.",
        "- Existing issue-114 `Computer Monitor Quality Loss` and issue-116 `Small Print Quality Loss` overrides are preserved.",
        "- Other Quality Loss presets stay on the issue-116 path.",
        "- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` are unchanged.",
        "",
        "## Result",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | Computer Monitor QL | Small Print QL | Large Print QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {CURRENT_BEST_LABEL} | {format_metric(current_best['curve_mae_mean'])} | {format_metric(current_best['focus_preset_acutance_mae_mean'])} | {format_metric(current_best['overall_quality_loss_mae_mean'])} | {format_metric(current_best['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(current_best['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(current_best['quality_loss_preset_mae'][LARGE_PRINT_QUALITY_LOSS])} | {format_metric(current_best['mtf_threshold_mae']['mtf20'])} | {format_metric(current_best['mtf_threshold_mae']['mtf30'])} | {format_metric(current_best['mtf_threshold_mae']['mtf50'])} | {format_metric(current_best['mtf_abs_signed_rel_mean'])} |",
        f"| {ISSUE116_LABEL} | {format_metric(issue116['curve_mae_mean'])} | {format_metric(issue116['focus_preset_acutance_mae_mean'])} | {format_metric(issue116['overall_quality_loss_mae_mean'])} | {format_metric(issue116['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(issue116['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(issue116['quality_loss_preset_mae'][LARGE_PRINT_QUALITY_LOSS])} | {format_metric(issue116['mtf_threshold_mae']['mtf20'])} | {format_metric(issue116['mtf_threshold_mae']['mtf30'])} | {format_metric(issue116['mtf_threshold_mae']['mtf50'])} | {format_metric(issue116['mtf_abs_signed_rel_mean'])} |",
        f"| {CANDIDATE_LABEL} | {format_metric(candidate['curve_mae_mean'])} | {format_metric(candidate['focus_preset_acutance_mae_mean'])} | {format_metric(candidate['overall_quality_loss_mae_mean'])} | {format_metric(candidate['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(candidate['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(candidate['quality_loss_preset_mae'][LARGE_PRINT_QUALITY_LOSS])} | {format_metric(candidate['mtf_threshold_mae']['mtf20'])} | {format_metric(candidate['mtf_threshold_mae']['mtf30'])} | {format_metric(candidate['mtf_threshold_mae']['mtf50'])} | {format_metric(candidate['mtf_abs_signed_rel_mean'])} |",
        "",
        "## Deltas",
        "",
        f"- Candidate versus issue `#116`: `Large Print Quality Loss = {candidate_vs_issue116['quality_loss_preset_mae'][LARGE_PRINT_QUALITY_LOSS]:+.5f}`, `overall_quality_loss_mae_mean = {candidate_vs_issue116['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Candidate versus PR `#30`: `Large Print Quality Loss = {candidate_vs_pr30['quality_loss_preset_mae'][LARGE_PRINT_QUALITY_LOSS]:+.5f}`, `overall_quality_loss_mae_mean = {candidate_vs_pr30['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Computer Monitor Quality Loss delta versus issue `#116`: `{candidate_vs_issue116['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS]:+.5f}`.",
        f"- Small Print Quality Loss delta versus issue `#116`: `{candidate_vs_issue116['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS]:+.5f}`.",
        f"- Reported-MTF equality versus issue `#116`: `{payload['acceptance']['reported_mtf_equal_to_issue116']}`.",
        f"- Non-target Quality Loss presets unchanged versus issue `#116`: `{all(payload['implementation_change']['unchanged_non_target_quality_loss_presets'].values())}`.",
        "",
        "## Acceptance",
        "",
    ]
    for key, value in payload["acceptance"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Status: `{payload['conclusion']['status']}`",
            f"- Summary: {payload['conclusion']['summary']}",
            f"- Next step: {payload['conclusion']['next_step']}",
            "",
            "## Storage Separation",
            "",
            f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`, `{GOLDEN_REFERENCE_ROOTS[2]}`",
            "- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.",
            "- No release-facing config is promoted in this issue.",
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
        issue116_summary_path=args.issue116_summary,
        acutance_artifact_path=args.acutance_artifact,
        psd_artifact_path=args.psd_artifact,
    )
    write_text(
        resolve_path(repo_root, args.output_json),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    write_text(resolve_path(repo_root, args.output_md), render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
