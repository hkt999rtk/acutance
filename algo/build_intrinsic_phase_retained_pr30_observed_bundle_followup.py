from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE102_LABEL = "issue102_readout_only_sensor_comp_candidate"
CANDIDATE_LABEL = "issue108_pr30_observed_bundle_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_pr30_observed_bundle_followup"
SELECTED_SLICE_ID = "issue102_topology_graft_pr30_observable_stack_onto_observed_branches"
QUALITY_LOSS_MATERIAL_IMPROVEMENT = 0.01
MTF20_MATERIAL_REGRESSION = 0.005
PR30_OBSERVED_BRANCH_BUNDLE = {
    "calibration_file": "algo/deadleaf_13b10_psd_calibration_anchored.json",
    "mtf_compensation_mode": "sensor_aperture_sinc",
    "sensor_fill_factor": 1.5,
    "texture_support_scale": True,
    "high_frequency_guard_start_cpp": 0.36,
}
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-108 PR30 observed-branch bundle follow-up summary."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--psd-artifact",
        type=Path,
        default=Path(
            "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_psd_benchmark.json"
        ),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path(
            "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json"
        ),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--issue102-summary",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"),
        help="Repo-relative issue-102 summary artifact path.",
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
        default=Path("artifacts/intrinsic_phase_retained_pr30_observed_bundle_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_pr30_observed_bundle_followup.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def select_profile(payload: dict[str, Any], expected_profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == expected_profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(
        f"Profile {expected_profile_path!r} not found in artifact. Available: {available}"
    )


def summarize_profile(
    *,
    label: str,
    psd_payload: dict[str, Any],
    acutance_payload: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    psd_profile = select_profile(psd_payload, profile_path)
    acutance_profile = select_profile(acutance_payload, profile_path)
    psd_overall = psd_profile["overall"]
    acutance_overall = acutance_profile["overall"]
    analysis_pipeline = dict(acutance_profile["analysis_pipeline"])
    for key, value in psd_profile["analysis_pipeline"].items():
        if key.startswith("readout_") or key in PR30_OBSERVED_BRANCH_BUNDLE:
            analysis_pipeline[key] = value
    return {
        "label": label,
        "profile_path": profile_path,
        "analysis_pipeline": analysis_pipeline,
        "curve_mae_mean": float(acutance_overall["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(acutance_overall["acutance_focus_preset_mae_mean"]),
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


def build_conclusion(
    *,
    acceptance: dict[str, bool],
    candidate: dict[str, Any],
    current_best: dict[str, Any],
) -> dict[str, str]:
    if acceptance["all_issue108_gates_pass"]:
        if (
            candidate["overall_quality_loss_mae_mean"] <= current_best["overall_quality_loss_mae_mean"]
            and candidate["mtf_abs_signed_rel_mean"] <= current_best["mtf_abs_signed_rel_mean"]
            and candidate["mtf_threshold_mae"]["mtf20"] <= current_best["mtf_threshold_mae"]["mtf20"]
            and candidate["mtf_threshold_mae"]["mtf30"] <= current_best["mtf_threshold_mae"]["mtf30"]
            and candidate["mtf_threshold_mae"]["mtf50"] <= current_best["mtf_threshold_mae"]["mtf50"]
        ):
            return {
                "status": "issue108_acceptance_passed_and_current_best_candidate",
                "summary": (
                    "The PR30 observed-branch bundle preserves the issue-102 intrinsic main branch, "
                    "materially improves downstream Quality Loss, and closes the tracked reported-MTF "
                    "readout gaps enough to beat or match the current PR #30 branch on guarded outputs."
                ),
                "next_step": "Promote this branch for review against the current best PR #30 branch.",
            }
        return {
            "status": "issue108_acceptance_passed_but_not_current_best",
            "summary": (
                "The PR30 observed-branch bundle clears the issue-108 gates against issue #102, "
                "but at least one guarded output still trails the current PR #30 branch."
            ),
            "next_step": (
                "Keep this as the bounded issue-108 implementation record and split any remaining "
                "gap from the measured candidate-vs-PR30 deltas."
            ),
        }
    return {
        "status": "issue108_pr30_observed_bundle_failed_or_mixed",
        "summary": (
            "The selected PR30 observed-branch bundle did not satisfy every issue-108 gate, so this "
            "bounded slice records the measured tradeoff instead of broadening the search."
        ),
        "next_step": (
            "Use the failed gate list and candidate-vs-PR30 deltas to decide the next bounded "
            "developer-discovery slice."
        ),
    }


def build_payload(
    repo_root: Path,
    *,
    psd_artifact_path: Path,
    acutance_artifact_path: Path,
    issue102_summary_path: Path,
    issue105_summary_path: Path,
) -> dict[str, Any]:
    psd_payload = load_json(resolve_path(repo_root, psd_artifact_path))
    acutance_payload = load_json(resolve_path(repo_root, acutance_artifact_path))
    issue102_summary = load_json(resolve_path(repo_root, issue102_summary_path))
    issue105_summary = load_json(resolve_path(repo_root, issue105_summary_path))

    candidate_profile_path = (
        "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
        "reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_profile.json"
    )
    profiles = {
        CURRENT_BEST_LABEL: issue102_summary["profiles"][CURRENT_BEST_LABEL],
        ISSUE102_LABEL: issue102_summary["profiles"][ISSUE102_LABEL],
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path=candidate_profile_path,
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue102 = profiles[ISSUE102_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    candidate_vs_issue102 = delta_map(candidate, issue102)
    candidate_vs_current_best = delta_map(candidate, current_best)

    acceptance = {
        "curve_mae_non_worse_than_issue102": (
            candidate["curve_mae_mean"] <= issue102["curve_mae_mean"]
        ),
        "focus_preset_acutance_non_worse_than_issue102": (
            candidate["focus_preset_acutance_mae_mean"]
            <= issue102["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_materially_improved_vs_issue102": (
            issue102["overall_quality_loss_mae_mean"]
            - candidate["overall_quality_loss_mae_mean"]
            >= QUALITY_LOSS_MATERIAL_IMPROVEMENT
        ),
        "mtf_abs_signed_rel_improved_vs_issue102": (
            candidate["mtf_abs_signed_rel_mean"] < issue102["mtf_abs_signed_rel_mean"]
        ),
        "mtf20_not_materially_regressed_vs_issue102": (
            candidate["mtf_threshold_mae"]["mtf20"]
            <= issue102["mtf_threshold_mae"]["mtf20"] + MTF20_MATERIAL_REGRESSION
        ),
        "mtf30_improved_vs_issue102": (
            candidate["mtf_threshold_mae"]["mtf30"] < issue102["mtf_threshold_mae"]["mtf30"]
        ),
        "mtf50_improved_vs_issue102": (
            candidate["mtf_threshold_mae"]["mtf50"] < issue102["mtf_threshold_mae"]["mtf50"]
        ),
    }
    acceptance["all_issue108_gates_pass"] = all(acceptance.values())

    pipeline = candidate["analysis_pipeline"]
    bundle_matches = {
        key: pipeline.get(key) == expected
        for key, expected in PR30_OBSERVED_BRANCH_BUNDLE.items()
    }
    payload = {
        "issue": 108,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": {
            "candidate_vs_issue102": {
                "delta": candidate_vs_issue102,
            },
            "candidate_vs_current_best_pr30": {
                "delta": candidate_vs_current_best,
            },
        },
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": SELECTED_SLICE_ID,
            "selected_slice_source": {
                "issue": 105,
                "selected_slice_id": issue105_summary["selected_slice_id"],
                "selected_pr30_observed_branch_bundle_keys": issue105_summary[
                    "selected_pr30_observed_branch_bundle_keys"
                ],
            },
            "scope_name": (
                "reported_mtf_disconnect_pr30_observed_bundle_"
                "quality_loss_isolation_downstream_matched_ori_only"
            ),
            "basis_profile_path": issue102["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "selected_pr30_observed_branch_bundle": PR30_OBSERVED_BRANCH_BUNDLE,
            "candidate_bundle_matches": bundle_matches,
            "change": (
                "Keep the issue-102 intrinsic main-acutance branch and readout-only sensor-aperture "
                "compensation record, but graft the full PR #30 observed-branch bundle onto the "
                "reported-MTF/readout path and downstream Quality Loss branch."
            ),
        },
        "conclusion": build_conclusion(
            acceptance=acceptance,
            candidate=candidate,
            current_best=current_best,
        ),
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                candidate_profile_path,
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_psd_benchmark.json",
                "artifacts/issue108_intrinsic_phase_retained_pr30_observed_bundle_acutance_benchmark.json",
                "artifacts/intrinsic_phase_retained_pr30_observed_bundle_benchmark.json",
            ],
            "rules": [
                "Keep issue-108 fitted outputs under `algo/` and `artifacts/` only.",
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
    issue102 = profiles[ISSUE102_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    comparison_issue102 = payload["comparisons"]["candidate_vs_issue102"]
    comparison_current_best = payload["comparisons"]["candidate_vs_current_best_pr30"]
    bundle = payload["implementation_change"]["selected_pr30_observed_branch_bundle"]

    lines = [
        "# Intrinsic Phase-Retained PR30 Observed-Branch Bundle Follow-up",
        "",
        "Issue `#108` implements the bounded slice selected by issue `#105` / PR `#107`: keep the issue-102 intrinsic topology, but graft the PR `#30` observed-branch bundle onto the reported-MTF/readout path and downstream Quality Loss branch only.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only`",
        f"- Basis issue `#102` profile: `{issue102['profile_path']}`",
        f"- Candidate profile: `{candidate['profile_path']}`",
        "- The main acutance branch stays on the issue-102 intrinsic branch; release-facing PR30 configs are not promoted.",
        "",
        "Selected PR30 observed-branch bundle:",
        "",
        *[f"- `{key} = {value}`" for key, value in bundle.items()],
        "",
        "## Result",
        "",
        "Current PR `#30` branch:",
        "",
        f"- `curve_mae_mean = {current_best['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {current_best['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {current_best['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {current_best['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf30 = {current_best['mtf_threshold_mae']['mtf30']:.5f}`",
        f"- `mtf50 = {current_best['mtf_threshold_mae']['mtf50']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {current_best['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#102` baseline:",
        "",
        f"- `curve_mae_mean = {issue102['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue102['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue102['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {issue102['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf30 = {issue102['mtf_threshold_mae']['mtf30']:.5f}`",
        f"- `mtf50 = {issue102['mtf_threshold_mae']['mtf50']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue102['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#108` PR30 observed-branch bundle candidate:",
        "",
        f"- `curve_mae_mean = {candidate['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {candidate['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {candidate['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {candidate['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf30 = {candidate['mtf_threshold_mae']['mtf30']:.5f}`",
        f"- `mtf50 = {candidate['mtf_threshold_mae']['mtf50']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {candidate['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "## Comparison",
        "",
        f"- Versus issue `#102`, `curve_mae_mean` changes by `{comparison_issue102['delta']['curve_mae_mean']:+.5f}` and `focus_preset_acutance_mae_mean` changes by `{comparison_issue102['delta']['focus_preset_acutance_mae_mean']:+.5f}`.",
        f"- Versus issue `#102`, `overall_quality_loss_mae_mean` changes by `{comparison_issue102['delta']['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Versus issue `#102`, `mtf20` changes by `{comparison_issue102['delta']['mtf_threshold_mae']['mtf20']:+.5f}`, `mtf30` by `{comparison_issue102['delta']['mtf_threshold_mae']['mtf30']:+.5f}`, `mtf50` by `{comparison_issue102['delta']['mtf_threshold_mae']['mtf50']:+.5f}`, and `mtf_abs_signed_rel_mean` by `{comparison_issue102['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        f"- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `{comparison_current_best['delta']['overall_quality_loss_mae_mean']:+.5f}` and `mtf_abs_signed_rel_mean` changes by `{comparison_current_best['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#102`: `{payload['acceptance']['curve_mae_non_worse_than_issue102']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#102`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue102']}`",
        f"- `overall_quality_loss_mae_mean` materially improves versus issue `#102`: `{payload['acceptance']['overall_quality_loss_materially_improved_vs_issue102']}`",
        f"- `mtf_abs_signed_rel_mean` improves versus issue `#102`: `{payload['acceptance']['mtf_abs_signed_rel_improved_vs_issue102']}`",
        f"- `mtf20` does not materially regress versus issue `#102`: `{payload['acceptance']['mtf20_not_materially_regressed_vs_issue102']}`",
        f"- `mtf30` improves versus issue `#102`: `{payload['acceptance']['mtf30_improved_vs_issue102']}`",
        f"- `mtf50` improves versus issue `#102`: `{payload['acceptance']['mtf50_improved_vs_issue102']}`",
        f"- All issue-108 gates pass: `{payload['acceptance']['all_issue108_gates_pass']}`",
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
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(
        repo_root,
        psd_artifact_path=args.psd_artifact,
        acutance_artifact_path=args.acutance_artifact,
        issue102_summary_path=args.issue102_summary,
        issue105_summary_path=args.issue105_summary,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
