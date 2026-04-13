from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE34_LABEL = "issue34_intrinsic_full_reference"
ISSUE47_LABEL = "issue47_phase_retained_replace_all"
CANDIDATE_LABEL = "issue81_quality_loss_isolation_candidate"
SUMMARY_KIND = "intrinsic_phase_retained_quality_loss_isolation_followup"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-81 phase-retained quality-loss isolation summary."
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
        default=Path("artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_phase_retained_quality_loss_isolation_followup.md"),
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
    psd_artifact = resolve_output(psd_artifact_path, repo_root)
    acutance_artifact = resolve_output(acutance_artifact_path, repo_root)
    psd_payload = load_json(psd_artifact)
    acutance_payload = load_json(acutance_artifact)
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
        ISSUE34_LABEL: summarize_profile(
            label=ISSUE34_LABEL,
            psd_payload=historical_psd,
            acutance_payload=historical_acutance,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json",
        ),
        ISSUE47_LABEL: summarize_profile(
            label=ISSUE47_LABEL,
            psd_payload=historical_psd,
            acutance_payload=historical_acutance,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json",
        ),
        CANDIDATE_LABEL: summarize_profile(
            label=CANDIDATE_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json",
        ),
    }

    current_best = profiles[CURRENT_BEST_LABEL]
    issue34 = profiles[ISSUE34_LABEL]
    issue47 = profiles[ISSUE47_LABEL]
    candidate = profiles[CANDIDATE_LABEL]
    comparisons = {
        "candidate_vs_issue47": {
            "delta": delta_map(candidate, issue47),
            "curve_mae_non_worse_than_issue47": candidate["curve_mae_mean"] <= issue47["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue47": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue47["focus_preset_acutance_mae_mean"]
            ),
            "overall_quality_loss_improved": (
                candidate["overall_quality_loss_mae_mean"]
                < issue47["overall_quality_loss_mae_mean"]
            ),
        },
        "candidate_vs_issue34": {
            "delta": delta_map(candidate, issue34),
            "curve_mae_non_worse_than_issue34": candidate["curve_mae_mean"] <= issue34["curve_mae_mean"],
            "focus_preset_acutance_non_worse_than_issue34": (
                candidate["focus_preset_acutance_mae_mean"]
                <= issue34["focus_preset_acutance_mae_mean"]
            ),
        },
        "candidate_vs_current_best_pr30": {
            "delta": delta_map(candidate, current_best),
        },
    }
    acceptance = {
        "curve_mae_non_worse_than_issue34": comparisons["candidate_vs_issue34"][
            "curve_mae_non_worse_than_issue34"
        ],
        "focus_preset_acutance_non_worse_than_issue34": comparisons["candidate_vs_issue34"][
            "focus_preset_acutance_non_worse_than_issue34"
        ],
        "overall_quality_loss_improved_vs_issue47": comparisons["candidate_vs_issue47"][
            "overall_quality_loss_improved"
        ],
    }
    acceptance["all_issue81_gates_pass"] = all(acceptance.values())

    payload = {
        "issue": 81,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "profiles": profiles,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "implementation_change": {
            "selected_slice_id": "phase_retained_intrinsic_quality_loss_isolation",
            "scope_name": "quality_loss_isolation",
            "basis_profile_path": issue47["profile_path"],
            "candidate_profile_path": candidate["profile_path"],
            "change": (
                "Keep the phase-retained intrinsic transfer active for PSD and Acutance evaluation, "
                "but route Quality Loss through the non-intrinsic compensated MTF path."
            ),
            "scope_difference": {
                "replace_all": (
                    "Intrinsic transfer feeds both reported PSD/MTF and downstream Quality Loss."
                ),
                "acutance_only": (
                    "Intrinsic transfer is limited to the acutance-side path under the older naming."
                ),
                "quality_loss_isolation": (
                    "Intrinsic transfer remains active for PSD and Acutance evaluation, while "
                    "Quality Loss is isolated to the non-intrinsic compensated MTF path."
                ),
            },
        },
        "conclusion": {
            "status": (
                "issue81_acceptance_passed_but_not_current_best"
                if acceptance["all_issue81_gates_pass"]
                else "bounded_negative"
            ),
            "summary": (
                "The new scope is a real improvement over the old phase-retained replace_all path: "
                "it preserves the intrinsic curve / focus-preset Acutance gains while materially "
                "reducing overall Quality Loss. It still remains worse than the current PR #30 "
                "main line on overall Quality Loss and MTF-threshold readouts."
            ),
            "next_step": (
                "Keep this scope as the new bounded intrinsic record and evaluate whether a later "
                "follow-up can reduce the remaining gap to the current best branch without "
                "reopening unrelated families."
            ),
        },
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json",
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json",
                "artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json",
                "artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json",
            ],
            "release_config_paths": [],
            "rules": [
                "Do not write fitted intrinsic profiles or benchmark outputs under the golden/reference roots.",
                "Keep issue-81 fitted artifacts under `algo/` and `artifacts/` only.",
                "Do not promote a release-facing config until the intrinsic route beats the tracked current-best guardrails.",
            ],
        },
        "sources": {
            "psd_artifact_path": str(psd_artifact.relative_to(repo_root)),
            "acutance_artifact_path": str(acutance_artifact.relative_to(repo_root)),
            "issue79_record": "docs/intrinsic_literal_next_slice.md",
        },
    }
    assert_storage_separation(payload)
    return payload


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def format_delta(value: float) -> str:
    return f"{value:+.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    candidate = payload["profiles"][CANDIDATE_LABEL]
    issue47 = payload["profiles"][ISSUE47_LABEL]
    issue34 = payload["profiles"][ISSUE34_LABEL]
    current_best = payload["profiles"][CURRENT_BEST_LABEL]
    lines = [
        "# Intrinsic Phase-Retained Quality-Loss Isolation Follow-up",
        "",
        "Issue `#81` implements the bounded slice selected in issue `#79` / PR `#80`: keep the phase-retained intrinsic transfer, but isolate downstream Quality Loss from the intrinsic path.",
        "",
        "## Scope",
        "",
        "- New intrinsic scope: `quality_loss_isolation`",
        "- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json`",
        "- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json`",
        "- Difference from `replace_all`: Quality Loss no longer consumes the intrinsic compensated MTF path.",
        "- Difference from `acutance_only`: this issue names the narrower downstream-isolation intent explicitly on top of the stronger phase-retained intrinsic branch.",
        "",
        "## Result",
        "",
        "Current PR `#30` branch:",
        "",
        f"- `curve_mae_mean = {format_metric(current_best['curve_mae_mean'])}`",
        f"- `focus_preset_acutance_mae_mean = {format_metric(current_best['focus_preset_acutance_mae_mean'])}`",
        f"- `overall_quality_loss_mae_mean = {format_metric(current_best['overall_quality_loss_mae_mean'])}`",
        "",
        "PR `#34` intrinsic baseline:",
        "",
        f"- `curve_mae_mean = {format_metric(issue34['curve_mae_mean'])}`",
        f"- `focus_preset_acutance_mae_mean = {format_metric(issue34['focus_preset_acutance_mae_mean'])}`",
        f"- `overall_quality_loss_mae_mean = {format_metric(issue34['overall_quality_loss_mae_mean'])}`",
        "",
        "PR `#47` phase-retained intrinsic baseline:",
        "",
        f"- `curve_mae_mean = {format_metric(issue47['curve_mae_mean'])}`",
        f"- `focus_preset_acutance_mae_mean = {format_metric(issue47['focus_preset_acutance_mae_mean'])}`",
        f"- `overall_quality_loss_mae_mean = {format_metric(issue47['overall_quality_loss_mae_mean'])}`",
        "",
        "Issue `#81` quality-loss-isolated candidate:",
        "",
        f"- `curve_mae_mean = {format_metric(candidate['curve_mae_mean'])}`",
        f"- `focus_preset_acutance_mae_mean = {format_metric(candidate['focus_preset_acutance_mae_mean'])}`",
        f"- `overall_quality_loss_mae_mean = {format_metric(candidate['overall_quality_loss_mae_mean'])}`",
        "",
        "## Comparison",
        "",
        f"- Versus PR `#47`, `overall_quality_loss_mae_mean` changes by `{format_delta(payload['comparisons']['candidate_vs_issue47']['delta']['overall_quality_loss_mae_mean'])}`.",
        f"- Versus PR `#34`, `curve_mae_mean` changes by `{format_delta(payload['comparisons']['candidate_vs_issue34']['delta']['curve_mae_mean'])}` and `focus_preset_acutance_mae_mean` changes by `{format_delta(payload['comparisons']['candidate_vs_issue34']['delta']['focus_preset_acutance_mae_mean'])}`.",
        f"- Versus current PR `#30`, `curve_mae_mean` changes by `{format_delta(payload['comparisons']['candidate_vs_current_best_pr30']['delta']['curve_mae_mean'])}` and `overall_quality_loss_mae_mean` changes by `{format_delta(payload['comparisons']['candidate_vs_current_best_pr30']['delta']['overall_quality_loss_mae_mean'])}`.",
        "",
        "## Acceptance",
        "",
        f"- `curve_mae_mean` no worse than issue `#34`: `{payload['acceptance']['curve_mae_non_worse_than_issue34']}`",
        f"- `focus_preset_acutance_mae_mean` no worse than issue `#34`: `{payload['acceptance']['focus_preset_acutance_non_worse_than_issue34']}`",
        f"- `overall_quality_loss_mae_mean` improved versus issue `#47`: `{payload['acceptance']['overall_quality_loss_improved_vs_issue47']}`",
        f"- All issue-81 gates pass: `{payload['acceptance']['all_issue81_gates_pass']}`",
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
