from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE108_LABEL = "issue108_pr30_observed_bundle_candidate"
ISSUE114_LABEL = "issue114_computer_monitor_quality_loss_input_boundary_candidate"
CANDIDATE_LABEL = "issue116_small_print_quality_loss_input_boundary_candidate"
SUMMARY_KIND = "intrinsic_after_issue114_quality_loss_boundary_followup"
COMPUTER_MONITOR_QUALITY_LOSS = "Computer Monitor Quality Loss"
SMALL_PRINT_QUALITY_LOSS = "Small Print Quality Loss"
SELECTED_SLICE_ID = "issue114_small_print_quality_loss_preset_boundary"
ISSUE114_PROFILE_PATH = (
    "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
    "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_"
    "matched_ori_only_computer_monitor_pr30_input_profile.json"
)
CANDIDATE_PROFILE_PATH = (
    "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
    "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_"
    "matched_ori_only_computer_monitor_small_print_pr30_input_profile.json"
)
PR30_INPUT_PROFILE_PATH = (
    "algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
    "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_profile.json"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-116 Small Print Quality Loss boundary summary."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue114-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue111_quality_loss_boundary_benchmark.json"),
        help="Repo-relative issue-114 summary artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue116_small_print_quality_loss_boundary_acutance_benchmark.json"),
        help="Repo-relative issue-116 acutance/Quality Loss benchmark artifact path.",
    )
    parser.add_argument(
        "--psd-artifact",
        type=Path,
        default=Path("artifacts/issue116_small_print_quality_loss_boundary_psd_benchmark.json"),
        help="Repo-relative issue-116 PSD/MTF benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue114_quality_loss_boundary_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue114_quality_loss_boundary.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def select_profile(payload: dict[str, Any], profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(f"Profile {profile_path!r} not found. Available: {available}")


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
        "quality_loss_preset_mae": {
            key: float(
                candidate["quality_loss_preset_mae"][key]
                - baseline["quality_loss_preset_mae"][key]
            )
            for key in sorted(candidate["quality_loss_preset_mae"])
        },
        "acutance_preset_mae": {
            key: float(candidate["acutance_preset_mae"][key] - baseline["acutance_preset_mae"][key])
            for key in sorted(candidate["acutance_preset_mae"])
        },
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        },
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_conclusion(acceptance: dict[str, bool], candidate_vs_pr30: dict[str, Any]) -> dict[str, str]:
    if acceptance["all_issue116_gates_pass"]:
        if candidate_vs_pr30["overall_quality_loss_mae_mean"] <= 0.0:
            return {
                "status": "issue116_current_best_candidate",
                "summary": (
                    "The Small Print-only Quality Loss input boundary closes the remaining overall "
                    "Quality Loss delta while preserving issue-114's Computer Monitor improvement "
                    "and reported-MTF parity."
                ),
                "next_step": "Promote the candidate for review against the current PR #30 branch.",
            }
        return {
            "status": "issue116_positive_partial_result",
            "summary": (
                "The Small Print-only Quality Loss input boundary materially improves the largest "
                "remaining residual preset and overall Quality Loss versus issue #114, but a small "
                "residual still remains versus PR #30."
            ),
            "next_step": (
                "Keep this as the issue-116 bounded implementation record and split the next "
                "residual Quality Loss boundary from the checked-in candidate-vs-PR30 deltas."
            ),
        }
    return {
        "status": "issue116_bounded_negative_or_mixed_result",
        "summary": (
            "The Small Print-only Quality Loss input boundary did not satisfy every issue-116 gate, "
            "so the issue should close as a bounded tradeoff record rather than broadening scope."
        ),
        "next_step": "Use the failed gates to decide whether another bounded discovery pass is warranted.",
    }


def build_payload(
    repo_root: Path,
    *,
    issue114_summary_path: Path,
    acutance_artifact_path: Path,
    psd_artifact_path: Path,
) -> dict[str, Any]:
    issue114_summary = load_json(resolve_path(repo_root, issue114_summary_path))
    acutance_payload = load_json(resolve_path(repo_root, acutance_artifact_path))
    psd_payload = load_json(resolve_path(repo_root, psd_artifact_path))

    summary_profiles = issue114_summary["profiles"]
    current_best = summary_profiles[CURRENT_BEST_LABEL]
    issue108 = summary_profiles[ISSUE108_LABEL]
    issue114 = summary_profiles[ISSUE114_LABEL]
    candidate = summarize_candidate(
        acutance_payload=acutance_payload,
        psd_payload=psd_payload,
        profile_path=CANDIDATE_PROFILE_PATH,
    )

    candidate_vs_issue114 = delta_map(candidate, issue114)
    candidate_vs_pr30 = delta_map(candidate, current_best)
    issue114_vs_pr30 = delta_map(issue114, current_best)

    unchanged_quality_loss_presets = {
        preset: delta == 0.0
        for preset, delta in candidate_vs_issue114["quality_loss_preset_mae"].items()
        if preset != SMALL_PRINT_QUALITY_LOSS
    }
    reported_mtf_equal_issue114 = {
        "mtf_abs_signed_rel_mean": candidate_vs_issue114["mtf_abs_signed_rel_mean"] == 0.0,
        "mtf20": candidate_vs_issue114["mtf_threshold_mae"]["mtf20"] == 0.0,
        "mtf30": candidate_vs_issue114["mtf_threshold_mae"]["mtf30"] == 0.0,
        "mtf50": candidate_vs_issue114["mtf_threshold_mae"]["mtf50"] == 0.0,
    }
    pipeline = candidate["analysis_pipeline"]
    expected_overrides = {
        COMPUTER_MONITOR_QUALITY_LOSS: PR30_INPUT_PROFILE_PATH,
        SMALL_PRINT_QUALITY_LOSS: PR30_INPUT_PROFILE_PATH,
    }
    acceptance = {
        "selected_slice_matches_issue116": SELECTED_SLICE_ID
        == "issue114_small_print_quality_loss_preset_boundary",
        "small_print_quality_loss_improved_vs_issue114": (
            candidate_vs_issue114["quality_loss_preset_mae"][SMALL_PRINT_QUALITY_LOSS] < -0.01
        ),
        "overall_quality_loss_improved_vs_issue114": (
            candidate_vs_issue114["overall_quality_loss_mae_mean"] < -0.01
        ),
        "computer_monitor_quality_loss_preserved_vs_issue114": (
            candidate_vs_issue114["quality_loss_preset_mae"][COMPUTER_MONITOR_QUALITY_LOSS] == 0.0
        ),
        "curve_mae_non_worse_than_issue114": candidate_vs_issue114["curve_mae_mean"] <= 0.0,
        "focus_preset_acutance_non_worse_than_issue114": (
            candidate_vs_issue114["focus_preset_acutance_mae_mean"] <= 0.0
        ),
        "reported_mtf_equal_to_issue114": all(reported_mtf_equal_issue114.values()),
        "only_small_print_quality_loss_input_added": (
            pipeline.get("quality_loss_preset_input_profile_overrides") == expected_overrides
            and all(unchanged_quality_loss_presets.values())
        ),
        "quality_loss_coefficients_preserved": (
            pipeline["quality_loss_coefficients"]
            == issue114["analysis_pipeline"]["quality_loss_coefficients"]
            == current_best["analysis_pipeline"]["quality_loss_coefficients"]
            and pipeline["quality_loss_om_ceiling"]
            == issue114["analysis_pipeline"]["quality_loss_om_ceiling"]
            == current_best["analysis_pipeline"]["quality_loss_om_ceiling"]
            and pipeline["quality_loss_preset_overrides"]
            == issue114["analysis_pipeline"]["quality_loss_preset_overrides"]
            == current_best["analysis_pipeline"]["quality_loss_preset_overrides"]
        ),
    }
    acceptance["all_issue116_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 116,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "dataset_root": acutance_payload["dataset_root"],
        "profiles": {
            CURRENT_BEST_LABEL: current_best,
            ISSUE108_LABEL: issue108,
            ISSUE114_LABEL: issue114,
            CANDIDATE_LABEL: candidate,
        },
        "comparisons": {
            "issue114_vs_current_best_pr30": {"delta": issue114_vs_pr30},
            "candidate_vs_issue114": {"delta": candidate_vs_issue114},
            "candidate_vs_current_best_pr30": {"delta": candidate_vs_pr30},
        },
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_source": {
                "issue": 116,
                "selected_slice_id": SELECTED_SLICE_ID,
            },
            "basis_profile_path": ISSUE114_PROFILE_PATH,
            "candidate_profile_path": CANDIDATE_PROFILE_PATH,
            "quality_loss_preset_input_profile_overrides": pipeline[
                "quality_loss_preset_input_profile_overrides"
            ],
            "reported_mtf_equal_to_issue114": reported_mtf_equal_issue114,
            "unchanged_non_target_quality_loss_presets": unchanged_quality_loss_presets,
            "change": (
                "Keep issue-114's Computer Monitor Quality Loss input override and add only "
                "`Small Print Quality Loss` to the PR #30-compatible acutance-only/noise-share "
                "anchor input."
            ),
        },
        "conclusion": build_conclusion(acceptance, candidate_vs_pr30),
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                CANDIDATE_PROFILE_PATH,
                "artifacts/issue116_small_print_quality_loss_boundary_acutance_benchmark.json",
                "artifacts/issue116_small_print_quality_loss_boundary_psd_benchmark.json",
                "artifacts/intrinsic_after_issue114_quality_loss_boundary_benchmark.json",
            ],
            "rules": [
                "Keep issue-116 fitted outputs under `algo/` and `artifacts/` only.",
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
    issue114 = profiles[ISSUE114_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    candidate_vs_issue114 = payload["comparisons"]["candidate_vs_issue114"]["delta"]
    candidate_vs_pr30 = payload["comparisons"]["candidate_vs_current_best_pr30"]["delta"]

    lines = [
        "# Intrinsic After Issue 114 Quality Loss Boundary",
        "",
        "Issue `#116` implements the bounded slice after issue `#114`: isolate only the `Small Print Quality Loss` preset-family input boundary while preserving the Computer Monitor improvement and reported-MTF parity.",
        "",
        "## Scope",
        "",
        f"- Basis issue `#114` profile: `{ISSUE114_PROFILE_PATH}`",
        f"- Candidate profile: `{CANDIDATE_PROFILE_PATH}`",
        "- Targeted added override: `Small Print Quality Loss` uses the PR `#30` acutance-only / noise-share anchor input.",
        "- Existing issue-114 `Computer Monitor Quality Loss` override is preserved.",
        "- Other Quality Loss presets stay on the issue-114 path.",
        "- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` are unchanged.",
        "",
        "## Result",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | Computer Monitor QL | Small Print QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| {CURRENT_BEST_LABEL} | {format_metric(current_best['curve_mae_mean'])} | {format_metric(current_best['focus_preset_acutance_mae_mean'])} | {format_metric(current_best['overall_quality_loss_mae_mean'])} | {format_metric(current_best['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(current_best['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(current_best['mtf_threshold_mae']['mtf20'])} | {format_metric(current_best['mtf_threshold_mae']['mtf30'])} | {format_metric(current_best['mtf_threshold_mae']['mtf50'])} | {format_metric(current_best['mtf_abs_signed_rel_mean'])} |",
        f"| {ISSUE114_LABEL} | {format_metric(issue114['curve_mae_mean'])} | {format_metric(issue114['focus_preset_acutance_mae_mean'])} | {format_metric(issue114['overall_quality_loss_mae_mean'])} | {format_metric(issue114['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(issue114['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(issue114['mtf_threshold_mae']['mtf20'])} | {format_metric(issue114['mtf_threshold_mae']['mtf30'])} | {format_metric(issue114['mtf_threshold_mae']['mtf50'])} | {format_metric(issue114['mtf_abs_signed_rel_mean'])} |",
        f"| {CANDIDATE_LABEL} | {format_metric(candidate['curve_mae_mean'])} | {format_metric(candidate['focus_preset_acutance_mae_mean'])} | {format_metric(candidate['overall_quality_loss_mae_mean'])} | {format_metric(candidate['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS])} | {format_metric(candidate['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS])} | {format_metric(candidate['mtf_threshold_mae']['mtf20'])} | {format_metric(candidate['mtf_threshold_mae']['mtf30'])} | {format_metric(candidate['mtf_threshold_mae']['mtf50'])} | {format_metric(candidate['mtf_abs_signed_rel_mean'])} |",
        "",
        "## Deltas",
        "",
        f"- Candidate versus issue `#114`: `Small Print Quality Loss = {candidate_vs_issue114['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS]:+.5f}`, `overall_quality_loss_mae_mean = {candidate_vs_issue114['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Candidate versus PR `#30`: `Small Print Quality Loss = {candidate_vs_pr30['quality_loss_preset_mae'][SMALL_PRINT_QUALITY_LOSS]:+.5f}`, `overall_quality_loss_mae_mean = {candidate_vs_pr30['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Computer Monitor Quality Loss delta versus issue `#114`: `{candidate_vs_issue114['quality_loss_preset_mae'][COMPUTER_MONITOR_QUALITY_LOSS]:+.5f}`.",
        f"- Reported-MTF equality versus issue `#114`: `{payload['acceptance']['reported_mtf_equal_to_issue114']}`.",
        f"- Non-target Quality Loss presets unchanged versus issue `#114`: `{all(payload['implementation_change']['unchanged_non_target_quality_loss_presets'].values())}`.",
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
        issue114_summary_path=args.issue114_summary,
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
