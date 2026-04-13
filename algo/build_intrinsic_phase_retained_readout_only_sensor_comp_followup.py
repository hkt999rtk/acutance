from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE93_LABEL = "issue93_downstream_matched_ori_only_candidate"
ISSUE97_LABEL = "issue97_reported_mtf_disconnect_candidate"
CANDIDATE_LABEL = "issue102_readout_only_sensor_comp_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_readout_only_sensor_comp_followup"
SELECTED_SLICE_ID = (
    "issue97_topology_add_readout_only_sensor_aperture_compensation"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-102 readout-only sensor compensation follow-up summary."
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
            "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_psd_benchmark.json"
        ),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path(
            "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_acutance_benchmark.json"
        ),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_readout_only_sensor_comp_followup.md"),
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
    if acceptance["all_issue102_gates_pass"]:
        if (
            candidate["overall_quality_loss_mae_mean"] <= current_best["overall_quality_loss_mae_mean"]
            and candidate["mtf_abs_signed_rel_mean"] <= current_best["mtf_abs_signed_rel_mean"]
            and candidate["mtf_threshold_mae"]["mtf20"] <= current_best["mtf_threshold_mae"]["mtf20"]
            and candidate["mtf_threshold_mae"]["mtf30"] <= current_best["mtf_threshold_mae"]["mtf30"]
            and candidate["mtf_threshold_mae"]["mtf50"] <= current_best["mtf_threshold_mae"]["mtf50"]
        ):
            return {
                "status": "issue102_acceptance_passed_and_current_best_candidate",
                "summary": (
                    "Adding readout-only sensor-aperture compensation preserves the issue-97 "
                    "curve, focus-preset Acutance, and downstream Quality Loss record while "
                    "improving the reported-MTF readout enough to clear the current-best PR #30 guardrails."
                ),
                "next_step": "Promote this branch for reviewer scrutiny against the current best branch.",
            }
        return {
            "status": "issue102_acceptance_passed_but_not_current_best",
            "summary": (
                "Adding readout-only sensor-aperture compensation preserves the issue-97 "
                "curve, focus-preset Acutance, and downstream Quality Loss record while "
                "improving the reported-MTF readout, but it still trails the current PR #30 branch overall."
            ),
            "next_step": (
                "Keep this branch as the bounded issue-102 implementation record and judge any "
                "later promotion against the remaining PR #30 gap."
            ),
        }
    return {
        "status": "issue102_readout_only_sensor_comp_failed",
        "summary": (
            "Adding readout-only sensor-aperture compensation did not improve the reported-MTF "
            "readout enough while preserving the issue-97 curve, focus-preset Acutance, and downstream "
            "Quality Loss record, so this bounded slice closes as a negative or mixed result."
        ),
        "next_step": (
            "Keep the result as the canonical issue-102 record and split the next bounded follow-up "
            "from the remaining reported-MTF/readout failure mode."
        ),
    }


def build_payload(
    repo_root: Path,
    *,
    psd_artifact_path: Path,
    acutance_artifact_path: Path,
) -> dict[str, Any]:
    psd_payload = load_json(resolve_output(psd_artifact_path, repo_root))
    acutance_payload = load_json(resolve_output(acutance_artifact_path, repo_root))
    issue93_summary = load_json(
        resolve_output(
            Path("artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"),
            repo_root,
        )
    )
    issue97_summary = load_json(
        resolve_output(
            Path("artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"),
            repo_root,
        )
    )
    issue99_summary = load_json(
        resolve_output(Path("artifacts/intrinsic_after_issue97_next_slice_benchmark.json"), repo_root)
    )

    candidate_profile_path = (
        "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
        "reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only_profile.json"
    )

    profiles = {
        CURRENT_BEST_LABEL: issue93_summary["profiles"][CURRENT_BEST_LABEL],
        ISSUE93_LABEL: issue93_summary["profiles"][ISSUE93_LABEL],
        ISSUE97_LABEL: issue97_summary["profiles"]["issue97_reported_mtf_disconnect_candidate"],
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path=candidate_profile_path,
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue93 = profiles[ISSUE93_LABEL]
    issue97 = profiles[ISSUE97_LABEL]
    candidate = profiles[CANDIDATE_LABEL]

    comparisons = {
        "candidate_vs_issue97": {
            "delta": delta_map(candidate, issue97),
            "curve_mae_non_worse_than_issue97": candidate["curve_mae_mean"] <= issue97["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue97": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue97["focus_preset_acutance_mae_mean"]
            ),
            "overall_quality_loss_non_worse_than_issue97": (
                candidate["overall_quality_loss_mae_mean"] <= issue97["overall_quality_loss_mae_mean"]
            ),
            "mtf_abs_signed_rel_improved_vs_issue97": (
                candidate["mtf_abs_signed_rel_mean"] < issue97["mtf_abs_signed_rel_mean"]
            ),
            "mtf20_non_worse_than_issue97": (
                candidate["mtf_threshold_mae"]["mtf20"] <= issue97["mtf_threshold_mae"]["mtf20"]
            ),
            "mtf30_improved_vs_issue97": (
                candidate["mtf_threshold_mae"]["mtf30"] < issue97["mtf_threshold_mae"]["mtf30"]
            ),
            "mtf50_improved_vs_issue97": (
                candidate["mtf_threshold_mae"]["mtf50"] < issue97["mtf_threshold_mae"]["mtf50"]
            ),
        },
        "candidate_vs_issue93": {
            "delta": delta_map(candidate, issue93),
        },
        "candidate_vs_current_best_pr30": {
            "delta": delta_map(candidate, current_best),
        },
    }
    acceptance = {
        "curve_mae_non_worse_than_issue97": comparisons["candidate_vs_issue97"][
            "curve_mae_non_worse_than_issue97"
        ],
        "focus_preset_acutance_non_worse_than_issue97": comparisons["candidate_vs_issue97"][
            "focus_preset_acutance_non_worse_than_issue97"
        ],
        "overall_quality_loss_non_worse_than_issue97": comparisons["candidate_vs_issue97"][
            "overall_quality_loss_non_worse_than_issue97"
        ],
        "mtf_abs_signed_rel_improved_vs_issue97": comparisons["candidate_vs_issue97"][
            "mtf_abs_signed_rel_improved_vs_issue97"
        ],
        "mtf20_non_worse_than_issue97": comparisons["candidate_vs_issue97"][
            "mtf20_non_worse_than_issue97"
        ],
        "mtf30_improved_vs_issue97": comparisons["candidate_vs_issue97"][
            "mtf30_improved_vs_issue97"
        ],
        "mtf50_improved_vs_issue97": comparisons["candidate_vs_issue97"][
            "mtf50_improved_vs_issue97"
        ],
    }
    acceptance["all_issue102_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 102,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": issue99_summary["selected_slice_id"],
            "scope_name": (
                "reported_mtf_disconnect_readout_only_sensor_comp_"
                "quality_loss_isolation_downstream_matched_ori_only"
            ),
            "basis_profile_path": issue97["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "change": (
                "Keep the issue-97 topology and downstream-only matched-ori Quality Loss branch, "
                "but add readout-only `sensor_aperture_sinc` compensation with `sensor_fill_factor=1.5` "
                "on the reported-MTF threshold-extraction path."
            ),
            "scope_difference": {
                "reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only": (
                    "Issue-97 topology: reported-MTF thresholds stay on the observed calibrated/compensated "
                    "branch while the main acutance branch and downstream-only matched-ori Quality Loss "
                    "branch remain on the issue-93 topology."
                ),
                "reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only": (
                    "The issue-97 topology stays intact, but the reported-MTF/readout branch adds "
                    "readout-only `sensor_aperture_sinc` compensation with PR #30's fill-factor setting."
                ),
            },
        },
        "conclusion": build_conclusion(
            acceptance=acceptance,
            candidate=candidate,
            current_best=current_best,
        ),
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only_profile.json",
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_psd_benchmark.json",
                "artifacts/issue102_intrinsic_phase_retained_readout_only_sensor_comp_acutance_benchmark.json",
                "artifacts/intrinsic_phase_retained_readout_only_sensor_comp_benchmark.json",
            ],
            "rules": [
                "Keep issue-102 fitted outputs under `algo/` and `artifacts/` only.",
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
    issue93 = profiles[ISSUE93_LABEL]
    issue97 = profiles[ISSUE97_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    comparison_issue97 = payload["comparisons"]["candidate_vs_issue97"]
    comparison_current_best = payload["comparisons"]["candidate_vs_current_best_pr30"]

    lines = [
        "# Intrinsic Phase-Retained Readout-Only Sensor Compensation Follow-up",
        "",
        "Issue `#102` implements the bounded slice selected in issue `#99` / PR `#100` / PR `#101`: keep the issue-97 topology and downstream-only matched-ori Quality Loss branch, but add readout-only `sensor_aperture_sinc` compensation on the reported-MTF threshold-extraction path.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only`",
        f"- Basis profile: `{issue97['profile_path']}`",
        f"- Candidate profile: `{candidate['profile_path']}`",
        "- Difference from issue `#97`: the main acutance branch and downstream Quality Loss branch stay unchanged, but reported-MTF threshold extraction adds readout-only `sensor_aperture_sinc` compensation with `sensor_fill_factor = 1.5`.",
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
        "Issue `#93` baseline:",
        "",
        f"- `curve_mae_mean = {issue93['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue93['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue93['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {issue93['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf30 = {issue93['mtf_threshold_mae']['mtf30']:.5f}`",
        f"- `mtf50 = {issue93['mtf_threshold_mae']['mtf50']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue93['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#97` baseline:",
        "",
        f"- `curve_mae_mean = {issue97['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue97['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue97['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {issue97['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf30 = {issue97['mtf_threshold_mae']['mtf30']:.5f}`",
        f"- `mtf50 = {issue97['mtf_threshold_mae']['mtf50']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue97['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#102` readout-only sensor compensation candidate:",
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
        f"- Versus issue `#97`, `curve_mae_mean` changes by `{comparison_issue97['delta']['curve_mae_mean']:+.5f}` and `focus_preset_acutance_mae_mean` changes by `{comparison_issue97['delta']['focus_preset_acutance_mae_mean']:+.5f}`.",
        f"- Versus issue `#97`, `overall_quality_loss_mae_mean` changes by `{comparison_issue97['delta']['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Versus issue `#97`, `mtf20` changes by `{comparison_issue97['delta']['mtf_threshold_mae']['mtf20']:+.5f}`, `mtf30` by `{comparison_issue97['delta']['mtf_threshold_mae']['mtf30']:+.5f}`, `mtf50` by `{comparison_issue97['delta']['mtf_threshold_mae']['mtf50']:+.5f}`, and `mtf_abs_signed_rel_mean` by `{comparison_issue97['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        f"- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `{comparison_current_best['delta']['overall_quality_loss_mae_mean']:+.5f}` and `mtf_abs_signed_rel_mean` changes by `{comparison_current_best['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#97`: `{payload['acceptance']['curve_mae_non_worse_than_issue97']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#97`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue97']}`",
        f"- `overall_quality_loss_mae_mean` no worse than issue `#97`: `{payload['acceptance']['overall_quality_loss_non_worse_than_issue97']}`",
        f"- `mtf_abs_signed_rel_mean` improves versus issue `#97`: `{payload['acceptance']['mtf_abs_signed_rel_improved_vs_issue97']}`",
        f"- `mtf20` no worse than issue `#97`: `{payload['acceptance']['mtf20_non_worse_than_issue97']}`",
        f"- `mtf30` improves versus issue `#97`: `{payload['acceptance']['mtf30_improved_vs_issue97']}`",
        f"- `mtf50` improves versus issue `#97`: `{payload['acceptance']['mtf50_improved_vs_issue97']}`",
        f"- All issue-102 gates pass: `{payload['acceptance']['all_issue102_gates_pass']}`",
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
