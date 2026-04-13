from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE47_LABEL = "issue47_phase_retained_replace_all"
ISSUE81_LABEL = "issue81_quality_loss_isolation_candidate"
CANDIDATE_LABEL = "issue85_readout_reconnect_quality_loss_isolation_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_readout_reconnect_followup"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-85 phase-retained readout reconnect summary."
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
        default=Path("artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_readout_reconnect_followup.md"),
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
    issue81_summary = load_json(
        resolve_output(Path("artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"), repo_root)
    )
    historical_psd = load_json(
        resolve_output(Path("artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json"), repo_root)
    )
    historical_acutance = load_json(
        resolve_output(Path("artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json"), repo_root)
    )
    current_best_psd = load_json(
        resolve_output(Path("artifacts/issue77_measured_oecf_psd_benchmark.json"), repo_root)
    )
    current_best_acutance = load_json(
        resolve_output(Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"), repo_root)
    )

    profiles = {
        CURRENT_BEST_LABEL: summarize_profile(
            label=CURRENT_BEST_LABEL,
            psd_payload=current_best_psd,
            acutance_payload=current_best_acutance,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json",
        ),
        ISSUE47_LABEL: summarize_profile(
            label=ISSUE47_LABEL,
            psd_payload=historical_psd,
            acutance_payload=historical_acutance,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json",
        ),
        ISSUE81_LABEL: issue81_summary["profiles"][ISSUE81_LABEL],
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json",
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue47 = profiles[ISSUE47_LABEL]
    issue81 = profiles[ISSUE81_LABEL]
    candidate = profiles[CANDIDATE_LABEL]

    threshold_closer = {
        key: closer_to_target(
            candidate["mtf_threshold_mae"][key],
            issue81["mtf_threshold_mae"][key],
            current_best["mtf_threshold_mae"][key],
        )
        for key in ("mtf20", "mtf30", "mtf50")
    }
    threshold_closer_count = sum(1 for value in threshold_closer.values() if value)
    comparisons = {
        "candidate_vs_issue81": {
            "delta": delta_map(candidate, issue81),
            "curve_mae_non_worse_than_issue81": candidate["curve_mae_mean"] <= issue81["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue81": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue81["focus_preset_acutance_mae_mean"]
            ),
            "overall_quality_loss_non_worse_than_issue81": (
                candidate["overall_quality_loss_mae_mean"]
                <= issue81["overall_quality_loss_mae_mean"]
            ),
            "mtf_abs_signed_rel_closer_to_current_best_pr30": closer_to_target(
                candidate["mtf_abs_signed_rel_mean"],
                issue81["mtf_abs_signed_rel_mean"],
                current_best["mtf_abs_signed_rel_mean"],
            ),
            "mtf_thresholds_closer_to_current_best_pr30": threshold_closer,
            "mtf_thresholds_closer_count": threshold_closer_count,
        },
        "candidate_vs_issue47": {
            "delta": delta_map(candidate, issue47),
        },
        "candidate_vs_current_best_pr30": {
            "delta": delta_map(candidate, current_best),
        },
    }
    acceptance = {
        "curve_mae_non_worse_than_issue81": comparisons["candidate_vs_issue81"][
            "curve_mae_non_worse_than_issue81"
        ],
        "focus_preset_acutance_non_worse_than_issue81": comparisons["candidate_vs_issue81"][
            "focus_preset_acutance_non_worse_than_issue81"
        ],
        "overall_quality_loss_non_worse_than_issue81": comparisons["candidate_vs_issue81"][
            "overall_quality_loss_non_worse_than_issue81"
        ],
        "mtf_abs_signed_rel_closer_to_current_best_pr30": comparisons["candidate_vs_issue81"][
            "mtf_abs_signed_rel_closer_to_current_best_pr30"
        ],
        "at_least_two_thresholds_closer_to_current_best_pr30": threshold_closer_count >= 2,
    }
    acceptance["all_issue85_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 85,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": "phase_retained_intrinsic_readout_reconnect_with_quality_loss_isolation",
            "scope_name": "readout_reconnect_quality_loss_isolation",
            "basis_profile_path": issue81["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "change": (
                "Reconnect the phase-retained intrinsic branch to the reported-MTF/readout path "
                "while keeping the downstream Quality Loss path on the non-intrinsic branch."
            ),
            "scope_difference": {
                "quality_loss_isolation": (
                    "Intrinsic transfer remains active for the curve / preset path only; "
                    "reported-MTF/readout metrics stay on `compensated_mtf`."
                ),
                "readout_reconnect_quality_loss_isolation": (
                    "Intrinsic transfer feeds both the reported-MTF/readout path and the "
                    "curve / preset path, while downstream Quality Loss remains isolated."
                ),
            },
        },
        "conclusion": {
            "status": (
                "issue85_acceptance_passed_but_not_current_best"
                if acceptance["all_issue85_gates_pass"]
                else "bounded_negative"
            ),
            "summary": (
                "The new scope reconnects the phase-retained intrinsic branch to the reported-MTF/readout "
                "path while keeping downstream Quality Loss isolated. It is intended to improve the "
                "post-issue81 readout gap without giving back the issue-81 curve / focus / Quality Loss gains."
            ),
            "next_step": (
                "Keep this scope as the new bounded intrinsic implementation record and judge promotion "
                "against the current PR #30 branch from the resulting readout and Quality Loss tradeoff."
            ),
        },
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                str(psd_artifact_path),
                str(acutance_artifact_path),
                "artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json",
                "docs/intrinsic_phase_retained_readout_reconnect_followup.md",
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    current_best = payload["profiles"][CURRENT_BEST_LABEL]
    issue47 = payload["profiles"][ISSUE47_LABEL]
    issue81 = payload["profiles"][ISSUE81_LABEL]
    candidate = payload["profiles"][CANDIDATE_LABEL]
    threshold_closer = payload["comparisons"]["candidate_vs_issue81"][
        "mtf_thresholds_closer_to_current_best_pr30"
    ]
    lines = [
        "# Intrinsic Phase-Retained Readout Reconnect Follow-up",
        "",
        "Issue `#85` implements the bounded slice selected in issue `#83` / PR `#84`: reconnect the phase-retained intrinsic branch to the reported-MTF/readout path while keeping downstream Quality Loss isolated.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `readout_reconnect_quality_loss_isolation`",
        f"- Basis profile: `{issue81['profile_path']}`",
        f"- Candidate profile: `{candidate['profile_path']}`",
        "- Difference from `quality_loss_isolation`: reported-MTF/readout metrics now consume the intrinsic branch as well.",
        "- Difference from `replace_all`: downstream Quality Loss remains on the non-intrinsic branch.",
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
        "Issue `#47` phase-retained intrinsic baseline:",
        "",
        f"- `curve_mae_mean = {issue47['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue47['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue47['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue47['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#81` quality-loss-isolated candidate:",
        "",
        f"- `curve_mae_mean = {issue81['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue81['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue81['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue81['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#85` readout-reconnected candidate:",
        "",
        f"- `curve_mae_mean = {candidate['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {candidate['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {candidate['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {candidate['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "## Comparison",
        "",
        f"- Versus issue `#81`, `curve_mae_mean` changes by `{payload['comparisons']['candidate_vs_issue81']['delta']['curve_mae_mean']:+.5f}` and `focus_preset_acutance_mae_mean` changes by `{payload['comparisons']['candidate_vs_issue81']['delta']['focus_preset_acutance_mae_mean']:+.5f}`.",
        f"- Versus issue `#81`, `overall_quality_loss_mae_mean` changes by `{payload['comparisons']['candidate_vs_issue81']['delta']['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Versus issue `#81`, `mtf_abs_signed_rel_mean` changes by `{payload['comparisons']['candidate_vs_issue81']['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        f"- Thresholds closer to PR `#30` than issue `#81`: `mtf20={threshold_closer['mtf20']}`, `mtf30={threshold_closer['mtf30']}`, `mtf50={threshold_closer['mtf50']}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#81`: `{payload['acceptance']['curve_mae_non_worse_than_issue81']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#81`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue81']}`",
        f"- `overall_quality_loss_mae_mean` no worse than issue `#81`: `{payload['acceptance']['overall_quality_loss_non_worse_than_issue81']}`",
        f"- `mtf_abs_signed_rel_mean` closer to PR `#30` than issue `#81`: `{payload['acceptance']['mtf_abs_signed_rel_closer_to_current_best_pr30']}`",
        f"- At least two threshold errors closer to PR `#30` than issue `#81`: `{payload['acceptance']['at_least_two_thresholds_closer_to_current_best_pr30']}`",
        f"- All issue-85 gates pass: `{payload['acceptance']['all_issue85_gates_pass']}`",
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
