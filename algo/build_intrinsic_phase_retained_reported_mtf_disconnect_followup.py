from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE93_LABEL = "issue93_downstream_matched_ori_only_candidate"
CANDIDATE_LABEL = "issue97_reported_mtf_disconnect_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_reported_mtf_disconnect_followup"
SELECTED_SLICE_ID = (
    "issue93_topology_keep_downstream_quality_loss_branch_but_disconnect_reported_mtf_from_intrinsic_reconnect"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-97 reported-MTF disconnect follow-up summary."
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
        default=Path("artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_reported_mtf_disconnect_followup.md"),
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
    if acceptance["all_issue97_gates_pass"]:
        if (
            candidate["overall_quality_loss_mae_mean"] <= current_best["overall_quality_loss_mae_mean"]
            and candidate["mtf_abs_signed_rel_mean"] <= current_best["mtf_abs_signed_rel_mean"]
            and candidate["mtf_threshold_mae"]["mtf20"] <= current_best["mtf_threshold_mae"]["mtf20"]
        ):
            return {
                "status": "issue97_acceptance_passed_and_current_best_candidate",
                "summary": (
                    "The reported-MTF disconnect preserves the issue-93 acutance and Quality Loss "
                    "record while improving the readout metrics enough to clear the current-best "
                    "PR #30 guardrails."
                ),
                "next_step": "Promote this branch for reviewer scrutiny against the current best branch.",
            }
        return {
            "status": "issue97_acceptance_passed_but_not_current_best",
            "summary": (
                "The reported-MTF disconnect preserves the issue-93 acutance and Quality Loss "
                "record while improving the readout metrics, but it still trails the current "
                "PR #30 branch overall."
            ),
            "next_step": (
                "Keep this branch as the bounded issue-97 implementation record and judge any "
                "later promotion against the remaining PR #30 gap."
            ),
        }
    return {
        "status": "issue97_reported_mtf_disconnect_failed",
        "summary": (
            "Disconnecting reported-MTF thresholds from the intrinsic reconnect did not improve "
            "the readout metrics enough while preserving the issue-93 acutance and Quality Loss "
            "record, so this bounded slice closes as a negative or mixed result."
        ),
        "next_step": (
            "Keep the result as the canonical issue-97 record and split the next bounded follow-up "
            "from the remaining failure mode."
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
        resolve_output(Path("artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"), repo_root)
    )
    issue95_summary = load_json(
        resolve_output(Path("artifacts/intrinsic_after_issue93_next_slice_benchmark.json"), repo_root)
    )

    candidate_profile_path = (
        "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_"
        "reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json"
    )

    profiles = {
        CURRENT_BEST_LABEL: issue93_summary["profiles"][CURRENT_BEST_LABEL],
        ISSUE93_LABEL: issue93_summary["profiles"][ISSUE93_LABEL],
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path=candidate_profile_path,
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue93 = profiles[ISSUE93_LABEL]
    candidate = profiles[CANDIDATE_LABEL]

    comparisons = {
        "candidate_vs_issue93": {
            "delta": delta_map(candidate, issue93),
            "curve_mae_non_worse_than_issue93": candidate["curve_mae_mean"] <= issue93["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue93": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue93["focus_preset_acutance_mae_mean"]
            ),
            "overall_quality_loss_non_worse_than_issue93": (
                candidate["overall_quality_loss_mae_mean"] <= issue93["overall_quality_loss_mae_mean"]
            ),
            "mtf20_improved_vs_issue93": (
                candidate["mtf_threshold_mae"]["mtf20"] < issue93["mtf_threshold_mae"]["mtf20"]
            ),
            "mtf_abs_signed_rel_improved_vs_issue93": (
                candidate["mtf_abs_signed_rel_mean"] < issue93["mtf_abs_signed_rel_mean"]
            ),
        },
        "candidate_vs_current_best_pr30": {
            "delta": delta_map(candidate, current_best),
        },
    }
    acceptance = {
        "curve_mae_non_worse_than_issue93": comparisons["candidate_vs_issue93"][
            "curve_mae_non_worse_than_issue93"
        ],
        "focus_preset_acutance_non_worse_than_issue93": comparisons["candidate_vs_issue93"][
            "focus_preset_acutance_non_worse_than_issue93"
        ],
        "overall_quality_loss_non_worse_than_issue93": comparisons["candidate_vs_issue93"][
            "overall_quality_loss_non_worse_than_issue93"
        ],
        "mtf20_improved_vs_issue93": comparisons["candidate_vs_issue93"][
            "mtf20_improved_vs_issue93"
        ],
        "mtf_abs_signed_rel_improved_vs_issue93": comparisons["candidate_vs_issue93"][
            "mtf_abs_signed_rel_improved_vs_issue93"
        ],
    }
    acceptance["all_issue97_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 97,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": issue95_summary["selected_slice_id"],
            "scope_name": "reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only",
            "basis_profile_path": issue93["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "change": (
                "Keep the issue-93 downstream-only matched-ori Quality Loss branch and intrinsic "
                "main-acutance branch, but disconnect reported-MTF threshold extraction from the "
                "intrinsic reconnect path."
            ),
            "scope_difference": {
                "readout_reconnect_quality_loss_isolation_downstream_matched_ori_only": (
                    "Issue-93 topology: reported-MTF thresholds and the main acutance branch both "
                    "use the intrinsic reconnect, while the downstream Quality Loss branch stays isolated."
                ),
                "reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only": (
                    "Reported-MTF thresholds stay on the observed calibrated/compensated branch, "
                    "while the main acutance branch and downstream-only matched-ori Quality Loss "
                    "branch remain on the issue-93 topology."
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
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json",
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json",
                "artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_acutance_benchmark.json",
                "artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json",
            ],
            "rules": [
                "Keep issue-97 fitted outputs under `algo/` and `artifacts/` only.",
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
    candidate = profiles[CANDIDATE_LABEL]
    comparison_issue93 = payload["comparisons"]["candidate_vs_issue93"]
    comparison_current_best = payload["comparisons"]["candidate_vs_current_best_pr30"]

    lines = [
        "# Intrinsic Phase-Retained Reported-MTF Disconnect Follow-up",
        "",
        "Issue `#97` implements the bounded slice selected in issue `#95` / PR `#96`: keep the issue-93 downstream-only matched-ori Quality Loss branch, but disconnect reported-MTF thresholds from the intrinsic reconnect path.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only`",
        f"- Basis profile: `{issue93['profile_path']}`",
        f"- Candidate profile: `{candidate['profile_path']}`",
        "- Difference from issue `#93`: the main acutance branch and downstream Quality Loss branch stay on the issue-93 topology, but reported-MTF threshold extraction returns to the observed calibrated/compensated branch.",
        "",
        "## Result",
        "",
        "Current PR `#30` branch:",
        "",
        f"- `curve_mae_mean = {current_best['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {current_best['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {current_best['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {current_best['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {current_best['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#93` baseline:",
        "",
        f"- `curve_mae_mean = {issue93['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {issue93['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {issue93['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {issue93['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {issue93['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "Issue `#97` reported-MTF disconnect candidate:",
        "",
        f"- `curve_mae_mean = {candidate['curve_mae_mean']:.5f}`",
        f"- `focus_preset_acutance_mae_mean = {candidate['focus_preset_acutance_mae_mean']:.5f}`",
        f"- `overall_quality_loss_mae_mean = {candidate['overall_quality_loss_mae_mean']:.5f}`",
        f"- `mtf20 = {candidate['mtf_threshold_mae']['mtf20']:.5f}`",
        f"- `mtf_abs_signed_rel_mean = {candidate['mtf_abs_signed_rel_mean']:.5f}`",
        "",
        "## Comparison",
        "",
        f"- Versus issue `#93`, `curve_mae_mean` changes by `{comparison_issue93['delta']['curve_mae_mean']:+.5f}` and `focus_preset_acutance_mae_mean` changes by `{comparison_issue93['delta']['focus_preset_acutance_mae_mean']:+.5f}`.",
        f"- Versus issue `#93`, `overall_quality_loss_mae_mean` changes by `{comparison_issue93['delta']['overall_quality_loss_mae_mean']:+.5f}`.",
        f"- Versus issue `#93`, `mtf20` changes by `{comparison_issue93['delta']['mtf_threshold_mae']['mtf20']:+.5f}` and `mtf_abs_signed_rel_mean` changes by `{comparison_issue93['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        f"- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `{comparison_current_best['delta']['overall_quality_loss_mae_mean']:+.5f}` and `mtf_abs_signed_rel_mean` changes by `{comparison_current_best['delta']['mtf_abs_signed_rel_mean']:+.5f}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#93`: `{payload['acceptance']['curve_mae_non_worse_than_issue93']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#93`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue93']}`",
        f"- `overall_quality_loss_mae_mean` no worse than issue `#93`: `{payload['acceptance']['overall_quality_loss_non_worse_than_issue93']}`",
        f"- `mtf20` improves versus issue `#93`: `{payload['acceptance']['mtf20_improved_vs_issue93']}`",
        f"- `mtf_abs_signed_rel_mean` improves versus issue `#93`: `{payload['acceptance']['mtf_abs_signed_rel_improved_vs_issue93']}`",
        f"- All issue-97 gates pass: `{payload['acceptance']['all_issue97_gates_pass']}`",
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
