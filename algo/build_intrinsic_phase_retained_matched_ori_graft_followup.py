from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE85_LABEL = "issue85_readout_reconnect_quality_loss_isolation_candidate"
CANDIDATE_LABEL = "issue89_matched_ori_graft_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_matched_ori_graft_followup"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-89 phase-retained matched-ori graft summary."
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
        default=Path("artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_matched_ori_graft_followup.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_output(path: Path, repo_root: Path) -> Path:
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
    return {
        "label": label,
        "profile_path": profile_path,
        "analysis_pipeline": acutance_profile["analysis_pipeline"],
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
        "mtf_band_mae": {
            key: float(value["mae_mean"]) for key, value in psd_overall["mtf_bands"].items()
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
            candidate["overall_quality_loss_mae_mean"]
            - baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        },
    }


def closer_to_target(candidate: float, baseline: float, target: float) -> bool:
    return abs(candidate - target) < abs(baseline - target)


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(
    repo_root: Path,
    *,
    psd_artifact_path: Path,
    acutance_artifact_path: Path,
) -> dict[str, Any]:
    psd_payload = load_json(resolve_output(psd_artifact_path, repo_root))
    acutance_payload = load_json(resolve_output(acutance_artifact_path, repo_root))
    issue85_summary = load_json(
        resolve_output(Path("artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"), repo_root)
    )
    issue87_summary = load_json(
        resolve_output(Path("artifacts/intrinsic_after_issue85_next_slice_benchmark.json"), repo_root)
    )
    current_best_psd = load_json(
        resolve_output(Path("artifacts/issue77_measured_oecf_psd_benchmark.json"), repo_root)
    )
    current_best_acutance = load_json(
        resolve_output(Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"), repo_root)
    )

    candidate_profile_path = (
        "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
        "readout_reconnect_quality_loss_isolation_matched_ori_graft_profile.json"
    )

    profiles = {
        CURRENT_BEST_LABEL: summarize_profile(
            label=CURRENT_BEST_LABEL,
            psd_payload=current_best_psd,
            acutance_payload=current_best_acutance,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json",
        ),
        ISSUE85_LABEL: issue85_summary["profiles"][ISSUE85_LABEL],
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path=candidate_profile_path,
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue85 = profiles[ISSUE85_LABEL]
    candidate = profiles[CANDIDATE_LABEL]

    threshold_closer = {
        key: closer_to_target(
            candidate["mtf_threshold_mae"][key],
            issue85["mtf_threshold_mae"][key],
            current_best["mtf_threshold_mae"][key],
        )
        for key in ("mtf20", "mtf30", "mtf50")
    }
    comparisons = {
        "candidate_vs_issue85": {
            "delta": delta_map(candidate, issue85),
            "curve_mae_non_worse_than_issue85": candidate["curve_mae_mean"] <= issue85["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue85": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue85["focus_preset_acutance_mae_mean"]
            ),
            "overall_quality_loss_improved_vs_issue85": (
                candidate["overall_quality_loss_mae_mean"]
                < issue85["overall_quality_loss_mae_mean"]
            ),
            "mtf20_closer_to_current_best_pr30": threshold_closer["mtf20"],
            "mtf_thresholds_closer_to_current_best_pr30": threshold_closer,
            "mtf_abs_signed_rel_no_worse_distance_to_current_best_pr30": (
                abs(candidate["mtf_abs_signed_rel_mean"] - current_best["mtf_abs_signed_rel_mean"])
                <= abs(issue85["mtf_abs_signed_rel_mean"] - current_best["mtf_abs_signed_rel_mean"])
            ),
        },
        "candidate_vs_current_best_pr30": {
            "delta": delta_map(candidate, current_best),
        },
    }
    acceptance = {
        "curve_mae_non_worse_than_issue85": comparisons["candidate_vs_issue85"][
            "curve_mae_non_worse_than_issue85"
        ],
        "focus_preset_acutance_non_worse_than_issue85": comparisons["candidate_vs_issue85"][
            "focus_preset_acutance_non_worse_than_issue85"
        ],
        "overall_quality_loss_improved_vs_issue85": comparisons["candidate_vs_issue85"][
            "overall_quality_loss_improved_vs_issue85"
        ],
        "mtf20_closer_to_current_best_pr30": comparisons["candidate_vs_issue85"][
            "mtf20_closer_to_current_best_pr30"
        ],
        "mtf_abs_signed_rel_no_worse_distance_to_current_best_pr30": comparisons[
            "candidate_vs_issue85"
        ]["mtf_abs_signed_rel_no_worse_distance_to_current_best_pr30"],
    }
    acceptance["all_issue89_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 89,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": issue87_summary["selected_slice_id"],
            "scope_name": "readout_reconnect_quality_loss_isolation_matched_ori_graft",
            "basis_profile_path": issue85["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "change": (
                "Keep the issue-85 split topology, preserve the main intrinsic curve/acutance "
                "branch, and graft PR30's matched-ori correction / acutance-anchor family onto "
                "the readout path plus the isolated downstream Quality Loss branch."
            ),
            "scope_difference": {
                "readout_reconnect_quality_loss_isolation": (
                    "Phase-retained intrinsic feeds the readout path and the main acutance path, "
                    "while downstream Quality Loss stays on the non-intrinsic branch."
                ),
                "readout_reconnect_quality_loss_isolation_matched_ori_graft": (
                    "The main intrinsic curve/acutance path stays unchanged, but the readout path "
                    "and the isolated downstream Quality Loss branch also receive PR30's "
                    "matched-ori correction / acutance-anchor family."
                ),
            },
        },
        "conclusion": {
            "status": "issue89_quality_loss_improved_but_readout_regressed",
            "summary": (
                "The bounded graft preserves issue #85's curve and focus-preset Acutance gains "
                "exactly and materially improves overall Quality Loss, but it dramatically "
                "over-corrects the reported-MTF/readout path. `mtf20`, `mtf30`, `mtf50`, and "
                "`mtf_abs_signed_rel_mean` all regress sharply versus issue #85, so the slice is "
                "not promotable."
            ),
            "next_step": (
                "Keep this branch as the canonical issue-89 implementation record and hand the "
                "residual readout-vs-quality-loss tradeoff back to PM for the next bounded split."
            ),
        },
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_matched_ori_graft_profile.json",
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_psd_benchmark.json",
                "artifacts/issue89_intrinsic_phase_retained_matched_ori_graft_acutance_benchmark.json",
                "artifacts/intrinsic_phase_retained_matched_ori_graft_benchmark.json",
            ],
            "rules": [
                "Keep issue-89 fitted outputs under `algo/` and `artifacts/` only.",
                "Do not write fitted profiles, transfer tables, or generated outputs under the golden/reference roots.",
                "Do not touch release-facing configs in this issue.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    profiles = payload["profiles"]
    current_best = profiles[CURRENT_BEST_LABEL]
    issue85 = profiles[ISSUE85_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    comparison = payload["comparisons"]["candidate_vs_issue85"]

    lines = [
        "# Intrinsic Phase-Retained Matched-Ori Graft Follow-up",
        "",
        "Issue `#89` implements the bounded slice selected in issue `#87` / PR `#88`: graft PR30's matched-ori downstream correction / acutance-anchor family onto the issue-85 split topology.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `readout_reconnect_quality_loss_isolation_matched_ori_graft`",
        f"- Basis profile: `{issue85['profile_path']}`",
        f"- Candidate profile: `{candidate['profile_path']}`",
        "- Difference from `readout_reconnect_quality_loss_isolation`: the main intrinsic curve/acutance path stays untouched, while the readout path and isolated downstream Quality Loss branch receive the bounded matched-ori graft.",
        "",
        "## Result",
        "",
        "Current PR `#30` branch:",
        "",
        f"- `curve_mae_mean = {current_best['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {current_best['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {current_best['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {current_best['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#85` readout-reconnected baseline:",
        "",
        f"- `curve_mae_mean = {issue85['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue85['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue85['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue85['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#89` matched-ori graft candidate:",
        "",
        f"- `curve_mae_mean = {candidate['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {candidate['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {candidate['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {candidate['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "## Comparison",
        "",
        f"- Versus issue `#85`, `curve_mae_mean` changes by `{comparison['delta']['curve_mae_mean']:+.5f}` and `focus_preset_acutance_mae_mean` changes by `{comparison['delta']['focus_preset_acutance_mae_mean']:+.5f}`.",
        f"- Versus issue `#85`, `overall_quality_loss_mae_mean` changes by `{comparison['delta']['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Versus issue `#85`, `mtf_abs_signed_rel_mean` changes by `{comparison['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        f"- Thresholds closer to PR `#30` than issue `#85`: `mtf20={comparison['mtf_thresholds_closer_to_current_best_pr30']['mtf20']}`, `mtf30={comparison['mtf_thresholds_closer_to_current_best_pr30']['mtf30']}`, `mtf50={comparison['mtf_thresholds_closer_to_current_best_pr30']['mtf50']}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#85`: `{payload['acceptance']['curve_mae_non_worse_than_issue85']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#85`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue85']}`",
        f"- `overall_quality_loss_mae_mean` improves versus issue `#85`: `{payload['acceptance']['overall_quality_loss_improved_vs_issue85']}`",
        f"- `mtf20` closer to PR `#30` than issue `#85`: `{payload['acceptance']['mtf20_closer_to_current_best_pr30']}`",
        f"- `mtf_abs_signed_rel_mean` preserves issue-85 distance to PR `#30`: `{payload['acceptance']['mtf_abs_signed_rel_no_worse_distance_to_current_best_pr30']}`",
        f"- All issue-89 gates pass: `{payload['acceptance']['all_issue89_gates_pass']}`",
        "",
        "## Conclusion",
        "",
        f"- Status: `{payload['conclusion']['status']}`",
        f"- Summary: {payload['conclusion']['summary']}",
        f"- Next step: {payload['conclusion']['next_step']}",
        "",
        "## Storage Separation",
        "",
        f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`",
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
    )
    output_json = resolve_output(args.output_json, repo_root)
    output_md = resolve_output(args.output_md, repo_root)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
