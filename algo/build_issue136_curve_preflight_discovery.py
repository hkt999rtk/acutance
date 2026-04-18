from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 136
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 132
CURRENT_BEST_PR = 135
CURRENT_BEST_HEAD = "c490e27"
CURRENT_BEST_MERGE = "3f57758"
CURRENT_BEST_PROFILE = "algo/issue132_small_print_acutance_parity_input_profile.json"
BASELINE_PR = 30
PR125 = 125
PR127 = 127
PR129 = 129
PR131 = 131
SUMMARY_KIND = "issue136_curve_preflight_discovery"
RESULT_KIND = "technical_discovery_no_source_backed_next_curve_slice"
SELECTED_DISCOVERY_ID = "post_issue132_curve_015_preflight_discovery"
CURVE_GATE = 0.020
FOCUS_PRESET_GATE = 0.030
QUALITY_LOSS_GATE = 1.30
NON_PHONE_ACUTANCE_GATE = 0.030
PHONE_PRESET = '5.5" Phone Display Acutance'
TARGET_MIXUP = "0.15"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build issue-136 curve preflight discovery.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue126-discovery",
        type=Path,
        default=Path("artifacts/issue126_residual_curve_discovery.json"),
    )
    parser.add_argument(
        "--issue128-summary",
        type=Path,
        default=Path("artifacts/issue128_ori_015_curve_shape_summary.json"),
    )
    parser.add_argument(
        "--issue130-discovery",
        type=Path,
        default=Path("artifacts/issue130_next_slice_discovery.json"),
    )
    parser.add_argument(
        "--issue132-summary",
        type=Path,
        default=Path("artifacts/issue132_small_print_acutance_boundary_summary.json"),
    )
    parser.add_argument(
        "--issue132-acutance",
        type=Path,
        default=Path("artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"),
    )
    parser.add_argument(
        "--parity-acutance",
        type=Path,
        default=Path("artifacts/parity_acutance_quality_loss_benchmark.json"),
    )
    parser.add_argument(
        "--issue63-acutance",
        type=Path,
        default=Path("artifacts/issue63_empirical_linearization_acutance_benchmark.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue136_curve_preflight_discovery.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue136_curve_preflight_discovery.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_profile(payload: dict[str, Any], profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == profile_path:
            return profile
    raise ValueError(f"Profile not found in artifact: {profile_path}")


def gate(value: float, threshold: float) -> dict[str, Any]:
    value = float(value)
    return {
        "value": value,
        "threshold": threshold,
        "operator": "<=",
        "pass": value <= threshold,
        "delta_to_gate": value - threshold,
    }


def readme_gate_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    non_phone = {
        key: value for key, value in metrics["acutance_preset_mae"].items() if key != PHONE_PRESET
    }
    worst_preset, worst_value = max(non_phone.items(), key=lambda item: item[1])
    gates = {
        "curve_mae_mean": gate(metrics["curve_mae_mean"], CURVE_GATE),
        "focus_preset_acutance_mae_mean": gate(
            metrics["acutance_focus_preset_mae_mean"], FOCUS_PRESET_GATE
        ),
        "overall_quality_loss_mae_mean": gate(
            metrics["overall_quality_loss_mae_mean"], QUALITY_LOSS_GATE
        ),
        "non_phone_acutance_preset_mae_max": {
            **gate(worst_value, NON_PHONE_ACUTANCE_GATE),
            "worst_preset": worst_preset,
            "by_preset": {key: float(value) for key, value in sorted(non_phone.items())},
        },
        PHONE_PRESET: gate(metrics["acutance_preset_mae"][PHONE_PRESET], 0.050),
    }
    return {
        "all_readme_gates_pass": all(row["pass"] for row in gates.values()),
        "failed_gates": [key for key, row in gates.items() if not row["pass"]],
        "gates": gates,
    }


def profile_preflight_row(
    *,
    artifact_path: Path,
    profile: dict[str, Any],
    baseline_015: float,
    classification: str,
    rejection_reason: str,
) -> dict[str, Any]:
    overall = profile["overall"]
    by_mixup = profile["by_mixup_curve_mae_mean"]
    return {
        "artifact_path": str(artifact_path),
        "profile_path": profile["profile_path"],
        "classification": classification,
        "curve_mae_mean": float(overall["curve_mae_mean"]),
        "mixup_015_curve_mae": float(by_mixup[TARGET_MIXUP]),
        "mixup_015_delta_vs_issue132": float(by_mixup[TARGET_MIXUP] - baseline_015),
        "mixup_ori_curve_mae": float(by_mixup["ori"]),
        "overall_quality_loss_mae_mean": float(overall["overall_quality_loss_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            overall["acutance_focus_preset_mae_mean"]
        ),
        "readme_gate_summary": readme_gate_summary(overall),
        "rejection_reason": rejection_reason,
        "accepted_as_source_backed_current_topology_preflight": False,
    }


def is_release_path(path: str) -> bool:
    return path.startswith(GOLDEN_REFERENCE_ROOTS)


def build_payload(
    repo_root: Path,
    *,
    issue126_discovery_path: Path,
    issue128_summary_path: Path,
    issue130_discovery_path: Path,
    issue132_summary_path: Path,
    issue132_acutance_path: Path,
    parity_acutance_path: Path,
    issue63_acutance_path: Path,
) -> dict[str, Any]:
    issue126 = load_json(resolve_path(repo_root, issue126_discovery_path))
    issue128 = load_json(resolve_path(repo_root, issue128_summary_path))
    issue130 = load_json(resolve_path(repo_root, issue130_discovery_path))
    issue132 = load_json(resolve_path(repo_root, issue132_summary_path))
    issue132_acutance = load_json(resolve_path(repo_root, issue132_acutance_path))
    parity_acutance = load_json(resolve_path(repo_root, parity_acutance_path))
    issue63_acutance = load_json(resolve_path(repo_root, issue63_acutance_path))

    current_profile = select_profile(issue132_acutance, CURRENT_BEST_PROFILE)
    current_metrics = current_profile["overall"]
    current_by_mixup = current_profile["by_mixup_curve_mae_mean"]
    current_015 = float(current_by_mixup[TARGET_MIXUP])
    issue128_curve = issue128["curve_shape_result"]
    direct_015 = float(issue128_curve["by_mixup_candidate"][TARGET_MIXUP])
    direct_015_delta = float(issue128_curve["by_mixup_delta"][TARGET_MIXUP])
    parity_profile = select_profile(
        parity_acutance, "algo/deadleaf_13b10_parity_psd_mtf_profile.json"
    )
    empirical_profile = select_profile(
        issue63_acutance,
        "algo/deadleaf_13b10_imatest_sensor_comp_power_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_roi_reference_only_empirical_linearization_profile.json",
    )

    apparent_candidates = [
        profile_preflight_row(
            artifact_path=parity_acutance_path,
            profile=parity_profile,
            baseline_015=current_015,
            classification="fitted_release_workaround_not_source_backed_current_topology",
            rejection_reason=(
                "The release parity-fit profile numerically improves `0.15`, but issue #29 "
                "explicitly keeps that profile separated as a workaround rather than a "
                "source-backed canonical model-family slice."
            ),
        ),
        profile_preflight_row(
            artifact_path=issue63_acutance_path,
            profile=empirical_profile,
            baseline_015=current_015,
            classification="historical_non_current_topology_with_protected_gate_regression",
            rejection_reason=(
                "The historical empirical-linearization profile improves `0.15`, but it is not "
                "a post-PR #135 current-topology preflight and fails the current overall "
                "Quality Loss gate."
            ),
        ),
    ]

    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "result_kind": RESULT_KIND,
        "selected_discovery_id": SELECTED_DISCOVERY_ID,
        "current_best": {
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "implementation_head": CURRENT_BEST_HEAD,
            "merge_commit": CURRENT_BEST_MERGE,
            "profile_path": CURRENT_BEST_PROFILE,
            "metrics": current_metrics,
            "by_mixup_curve_mae_mean": {
                key: float(value) for key, value in current_by_mixup.items()
            },
            "source_artifacts": [
                str(issue132_summary_path),
                str(issue132_acutance_path),
            ],
        },
        "readme_gate_status": readme_gate_summary(current_metrics),
        "evidence_base": {
            "source_artifacts": [
                str(issue126_discovery_path),
                str(issue128_summary_path),
                str(issue130_discovery_path),
                str(issue132_summary_path),
                str(issue132_acutance_path),
                str(parity_acutance_path),
                str(issue63_acutance_path),
            ],
            "issue126_curve_requirement": {
                "selected_minimum_gate_clear_mixups": issue126[
                    "residual_curve_evidence"
                ]["selected_minimum_gate_clear_mixups"],
                "ori_and_015_if_reduced_to_gate_curve_mae": float(
                    issue126["residual_curve_evidence"][
                        "ori_and_015_if_reduced_to_gate_curve_mae"
                    ]
                ),
                "ori_and_025_if_reduced_to_gate_curve_mae": float(
                    issue126["residual_curve_evidence"][
                        "ori_and_025_if_reduced_to_gate_curve_mae"
                    ]
                ),
            },
            "issue128_direct_015_negative": {
                "candidate_boundary": issue128_curve["candidate_boundary"],
                "baseline_015_curve_mae": float(
                    issue128_curve["by_mixup_baseline"][TARGET_MIXUP]
                ),
                "candidate_015_curve_mae": direct_015,
                "delta_vs_pr125": direct_015_delta,
                "aggregate_curve_delta_vs_pr125": float(
                    issue128["comparisons"]["candidate_vs_pr125"]["delta"][
                        "curve_mae_mean"
                    ]
                ),
                "moves_015_in_wrong_direction": direct_015_delta > 0.0,
                "protected_metrics_preserved": {
                    "reported_mtf": issue128["acceptance"]["reported_mtf_preserved"],
                    "focus_preset_acutance": issue128["acceptance"][
                        "focus_preset_acutance_preserved"
                    ],
                    "overall_quality_loss": issue128["acceptance"][
                        "overall_quality_loss_preserved"
                    ],
                    "release_separation": issue128["acceptance"][
                        "release_separation_preserved"
                    ],
                },
            },
            "issue130_curve_rule": issue130["curve_path_status"],
            "issue132_non_curve_gate_result": {
                "small_print_gate_pass": issue132["acceptance"]["small_print_gate_pass"],
                "non_phone_gate_pass": issue132["readme_gate_summary"]["gates"][
                    "non_phone_acutance_preset_mae_max"
                ]["pass"],
                "remaining_failed_gates": issue132["readme_gate_summary"]["failed_gates"],
            },
            "apparent_015_improvement_examples": apparent_candidates,
        },
        "preflight_decision": {
            "status": "no_source_backed_current_topology_015_preflight_found",
            "selected_follow_up": None,
            "do_not_open_full_curve_candidate": True,
            "reason": (
                "The only current-topology `0.15` implementation evidence is PR #129, "
                "which worsened `0.15`. Older apparent improvements are either fitted "
                "workaround profiles or non-current-topology artifacts that fail protected "
                "issue #136 constraints, so they do not satisfy the source-backed preflight gate."
            ),
            "required_to_resume_curve_work": [
                "A post-PR #135 current-topology preflight artifact that lowers `0.15` versus 0.029378599163150443.",
                "A source-backed model-family explanation for that preflight, not a fitted release-workaround graft.",
                "Preservation, or explicitly measured bounded tradeoff, for reported-MTF, focus-preset Acutance, overall Quality Loss, non-Phone Acutance, and release separation.",
            ],
        },
        "acceptance": {
            "records_post_pr135_readme_gates": issue132["readme_gate_summary"][
                "failed_gates"
            ]
            == ["curve_mae_mean"],
            "records_pr129_015_negative": direct_015_delta > 0.0,
            "requires_015_preflight": True,
            "no_full_curve_candidate_selected": True,
            "no_source_backed_current_topology_preflight_found": True,
            "result_is_developer_discovery_not_pm_question": True,
            "release_separation_preserved": True,
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "Discovery records checked-in evidence only.",
                "No fitted outputs are promoted into release-facing configs.",
                "No golden/reference data roots are modified by this discovery.",
            ],
        },
        "refs": {
            "umbrella_issue": UMBRELLA_ISSUE,
            "current_issue": ISSUE,
            "current_best_issue": CURRENT_BEST_ISSUE,
            "current_best_pr": CURRENT_BEST_PR,
            "pr125": PR125,
            "pr127": PR127,
            "pr129": PR129,
            "pr131": PR131,
            "baseline_pr": BASELINE_PR,
        },
    }
    assert_storage_separation(payload)
    return payload


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["current_best"]["source_artifacts"]:
        if is_release_path(path):
            raise ValueError(f"discovery source path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_best"]
    metrics = current["metrics"]
    gates = payload["readme_gate_status"]["gates"]
    issue128 = payload["evidence_base"]["issue128_direct_015_negative"]
    candidates = payload["evidence_base"]["apparent_015_improvement_examples"]
    decision = payload["preflight_decision"]
    return "\n".join(
        [
            "# Issue 136 Curve Preflight Discovery",
            "",
            f"- Result: `{payload['result_kind']}`.",
            f"- Current best: issue `#{current['issue']}` / PR `#{current['pr']}`.",
            f"- Current profile: `{current['profile_path']}`.",
            f"- Decision: `{decision['status']}`.",
            "",
            "## README Gate Status",
            "",
            "| Gate | Value | Threshold | Delta | Status |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(metrics['curve_mae_mean'])} | "
            f"{format_metric(gates['curve_mae_mean']['threshold'])} | "
            f"{format_metric(gates['curve_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['curve_mae_mean']['pass'] else 'miss'} |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(metrics['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['threshold'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['focus_preset_acutance_mae_mean']['pass'] else 'miss'} |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(metrics['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['threshold'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['overall_quality_loss_mae_mean']['pass'] else 'miss'} |",
            f"| non-phone Acutance max | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['value'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['threshold'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['delta_to_gate'])} | "
            f"{'pass' if gates['non_phone_acutance_preset_mae_max']['pass'] else 'miss'} |",
            "",
            "## 0.15 Preflight Evidence",
            "",
            f"- Current PR #135 `0.15` curve MAE: "
            f"`{format_metric(current['by_mixup_curve_mae_mean'][TARGET_MIXUP])}`.",
            f"- PR #129 direct `0.15` anchor-mask broadening moved `0.15` to "
            f"`{format_metric(issue128['candidate_015_curve_mae'])}` "
            f"(`{issue128['delta_vs_pr125']:+.5f}`), so it remains negative evidence.",
            "",
            "| Artifact | Profile | 0.15 MAE | Delta vs #135 | Curve MAE | QL MAE | Classification |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
            *[
                f"| `{row['artifact_path']}` | `{row['profile_path']}` | "
                f"{format_metric(row['mixup_015_curve_mae'])} | "
                f"{row['mixup_015_delta_vs_issue132']:+.5f} | "
                f"{format_metric(row['curve_mae_mean'])} | "
                f"{format_metric(row['overall_quality_loss_mae_mean'])} | "
                f"`{row['classification']}` |"
                for row in candidates
            ],
            "",
            "Rejected apparent improvements:",
            "",
            *[f"- {row['rejection_reason']}" for row in candidates],
            "",
            "## Decision",
            "",
            decision["reason"],
            "",
            "Required evidence before curve work resumes:",
            "",
            *[f"- {item}" for item in decision["required_to_resume_curve_work"]],
            "",
            "## Release Separation",
            "",
            "This discovery does not promote fitted outputs into golden/reference roots or "
            "release-facing configs.",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = args.repo_root
    payload = build_payload(
        repo_root,
        issue126_discovery_path=args.issue126_discovery,
        issue128_summary_path=args.issue128_summary,
        issue130_discovery_path=args.issue130_discovery,
        issue132_summary_path=args.issue132_summary,
        issue132_acutance_path=args.issue132_acutance,
        parity_acutance_path=args.parity_acutance,
        issue63_acutance_path=args.issue63_acutance,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
