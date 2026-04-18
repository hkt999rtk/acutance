from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 130
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 124
CURRENT_BEST_PR = 125
DISCOVERY_ISSUE = 126
DISCOVERY_PR = 127
NEGATIVE_ISSUE = 128
NEGATIVE_PR = 129
BASELINE_PR = 30
SUMMARY_KIND = "issue130_next_slice_discovery"
SELECTED_DISCOVERY_ID = "post_issue128_curve_shape_or_small_print_preset_boundary"
SELECTED_SLICE_ID = "issue124_small_print_acutance_preset_only_boundary"
CURVE_GATE = 0.020
FOCUS_PRESET_GATE = 0.030
QUALITY_LOSS_GATE = 1.30
NON_PHONE_ACUTANCE_GATE = 0.030
PHONE_PRESET = '5.5" Phone Display Acutance'
SMALL_PRINT_PRESET = "Small Print Acutance"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build issue-130 next-slice discovery.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue124-summary",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
    )
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
        "--output-json",
        type=Path,
        default=Path("artifacts/issue130_next_slice_discovery.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue130_next_slice_discovery.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
            metrics["acutance_focus_preset_mae_mean"],
            FOCUS_PRESET_GATE,
        ),
        "overall_quality_loss_mae_mean": gate(
            metrics["overall_quality_loss_mae_mean"],
            QUALITY_LOSS_GATE,
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


def is_release_path(path: str) -> bool:
    return path.startswith(GOLDEN_REFERENCE_ROOTS)


def build_small_print_boundary(metrics: dict[str, Any]) -> dict[str, Any]:
    non_phone = {
        key: float(value)
        for key, value in metrics["acutance_preset_mae"].items()
        if key != PHONE_PRESET
    }
    worst_preset, worst_value = max(non_phone.items(), key=lambda item: item[1])
    return {
        "target_preset": SMALL_PRINT_PRESET,
        "current_value": float(non_phone[SMALL_PRINT_PRESET]),
        "gate": NON_PHONE_ACUTANCE_GATE,
        "delta_to_gate": float(non_phone[SMALL_PRINT_PRESET] - NON_PHONE_ACUTANCE_GATE),
        "worst_non_phone_preset": worst_preset,
        "worst_non_phone_value": float(worst_value),
        "non_phone_by_preset": dict(sorted(non_phone.items())),
    }


def build_payload(
    repo_root: Path,
    *,
    issue124_summary_path: Path,
    issue126_discovery_path: Path,
    issue128_summary_path: Path,
) -> dict[str, Any]:
    issue124 = load_json(resolve_path(repo_root, issue124_summary_path))
    issue126 = load_json(resolve_path(repo_root, issue126_discovery_path))
    issue128 = load_json(resolve_path(repo_root, issue128_summary_path))
    current = issue124["candidate"]
    current_metrics = current["metrics"]
    issue128_delta = issue128["comparisons"]["candidate_vs_pr125"]["delta"]
    issue128_curve = issue128["curve_shape_result"]
    small_print = build_small_print_boundary(current_metrics)
    curve_delta_to_gate = float(current_metrics["curve_mae_mean"] - CURVE_GATE)
    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "selected_discovery_id": SELECTED_DISCOVERY_ID,
        "current_best": {
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "profile_path": current["profile_path"],
            "metrics": current_metrics,
            "source_artifacts": [str(issue124_summary_path), *current["source_artifacts"]],
        },
        "readme_gate_status": readme_gate_summary(current_metrics),
        "evidence_base": {
            "source_artifacts": [
                str(issue124_summary_path),
                str(issue126_discovery_path),
                str(issue128_summary_path),
            ],
            "issue126_selected_curve_slice": {
                "slice_id": issue126["selected_next_slice"]["slice_id"],
                "target_mixups": issue126["selected_next_slice"]["target_mixups"],
                "rationale": issue126["selected_next_slice"]["repo_evidence"],
            },
            "issue128_negative_result": {
                "result_kind": issue128["result_kind"],
                "curve_mae_delta_vs_pr125": float(issue128_delta["curve_mae_mean"]),
                "mixup_015_delta_vs_pr125": float(issue128_curve["by_mixup_delta"]["0.15"]),
                "mixup_ori_delta_vs_pr125": float(issue128_curve["by_mixup_delta"]["ori"]),
                "protected_metrics_preserved": {
                    "reported_mtf": issue128["acceptance"]["reported_mtf_preserved"],
                    "focus_preset_acutance": issue128["acceptance"][
                        "focus_preset_acutance_preserved"
                    ],
                    "overall_quality_loss": issue128["acceptance"][
                        "overall_quality_loss_preserved"
                    ],
                    "small_print_acutance": issue128["acceptance"][
                        "small_print_acutance_preserved"
                    ],
                    "release_separation": issue128["acceptance"][
                        "release_separation_preserved"
                    ],
                },
            },
        },
        "curve_path_status": {
            "current_best_curve_mae_mean": float(current_metrics["curve_mae_mean"]),
            "curve_gate": CURVE_GATE,
            "delta_to_curve_gate": curve_delta_to_gate,
            "status": "not_selected_for_direct_implementation",
            "reason": (
                "Issue #128 proved that directly broadening the issue #124 curve-only "
                "anchor mask moves `0.15` in the wrong direction. Checked-in evidence "
                "does not identify a source-backed per-mixup or shape-family variant "
                "that first proves `0.15` improves."
            ),
            "future_curve_prerequisite": (
                "Before another full curve benchmark candidate, require a narrow "
                "preflight artifact showing `0.15` improves under a concrete per-mixup "
                "or shape-family boundary."
            ),
            "do_not_continue_broadening_issue124_anchor_mask": True,
        },
        "small_print_boundary": small_print,
        "selected_next_slice": {
            "slice_id": SELECTED_SLICE_ID,
            "selected": True,
            "slice_type": "Small Print Acutance preset-only boundary",
            "selected_summary": (
                "Stop direct curve-mask broadening for this handoff and split the "
                "deferred Small Print Acutance preset-only miss. The miss is small, "
                "isolated to the non-Phone Acutance gate, and can be tested without "
                "touching curve, Quality Loss coefficients, reported-MTF/readout, or "
                "release-facing configs."
            ),
            "minimum_implementation_boundary": [
                "Start from the issue #124 / PR #125 current-best profile.",
                "Restrict changes to the Small Print Acutance preset readout/input boundary.",
                "Do not change `curve_only_acutance_anchor_mixups` or any curve-shape branch.",
                "Do not change reported-MTF compensation/readout settings.",
                "Do not change Quality Loss coefficients or Quality Loss preset input overrides.",
                "Keep release-facing configs and golden/reference data untouched.",
            ],
            "repo_evidence": [
                "PR #125 is still the current-best candidate after PR #129.",
                "PR #129 worsened aggregate curve MAE and `0.15`, so direct anchor-mask broadening is not justified.",
                "The only non-Phone Acutance preset still above the README gate in PR #125 is Small Print Acutance.",
                "Small Print Acutance misses the `<= 0.030` gate by about `+0.00173`.",
                "Issue #126 and issue #128 already deferred Small Print Acutance preset-only work as the alternate bounded path.",
            ],
            "expected_preservation": {
                "curve_mae_mean": "preserve_pr125",
                "reported_mtf_parity": "preserve_pr125",
                "focus_preset_acutance_mae_mean": "improve_or_preserve_gate_pass",
                "overall_quality_loss_mae_mean": "preserve_pr125",
                "quality_loss_coefficients": "preserve",
                "release_separation": "preserve",
            },
            "promotion_acceptance": [
                "`Small Print Acutance <= 0.030`, or record the slice as bounded negative/non-promotable.",
                "`focus_preset_acutance_mae_mean <= 0.030` remains true.",
                "`curve_mae_mean` remains equal to PR #125 unless the result is explicitly non-promotable.",
                "Reported-MTF metrics remain equal to PR #125 / PR #30.",
                "`overall_quality_loss_mae_mean <= 1.30` remains true and Quality Loss inputs stay unchanged.",
                "Release-facing configs and golden/reference data roots remain untouched.",
            ],
            "validation_plan": [
                "Regenerate the Acutance/Quality Loss benchmark for the candidate profile.",
                "Regenerate the PSD/MTF benchmark to prove reported-MTF remains unchanged.",
                "Compare README gates, PR #125 deltas, and Small Print Acutance gate delta in a checked-in summary.",
                "Run focused summary tests plus `git diff --check`.",
            ],
        },
        "rejected_options": [
            {
                "id": "continue_issue124_anchor_mask_broadening",
                "selected": False,
                "reason": "Issue #128 worsened `0.15` and aggregate curve MAE.",
            },
            {
                "id": "full_curve_benchmark_without_015_preflight",
                "selected": False,
                "reason": "Issue #130 requires proof that `0.15` improves before another full curve candidate.",
            },
        ],
        "acceptance": {
            "identifies_next_bounded_slice": True,
            "next_handoff_is_not_umbrella": True,
            "selected_slice_from_checked_in_artifacts": True,
            "current_best_remains_pr125": True,
            "curve_continuation_requires_015_preflight": True,
            "small_print_handoff_is_preset_only": True,
            "release_separation_preserved": True,
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "This discovery does not promote a release-facing config.",
                "The selected follow-up must not write fitted outputs under golden/reference roots.",
                "The selected follow-up must keep release configs separate from canonical-target research.",
            ],
        },
        "refs": {
            "umbrella_issue": UMBRELLA_ISSUE,
            "current_issue": ISSUE,
            "current_best_issue": CURRENT_BEST_ISSUE,
            "current_best_pr": CURRENT_BEST_PR,
            "discovery_issue": DISCOVERY_ISSUE,
            "discovery_pr": DISCOVERY_PR,
            "negative_issue": NEGATIVE_ISSUE,
            "negative_pr": NEGATIVE_PR,
            "baseline_pr": BASELINE_PR,
        },
    }
    assert_storage_separation(payload)
    return payload


def assert_storage_separation(payload: dict[str, Any]) -> None:
    paths = [
        payload["current_best"]["profile_path"],
        *payload["current_best"]["source_artifacts"],
        *payload["evidence_base"]["source_artifacts"],
    ]
    for path in paths:
        if is_release_path(path):
            raise ValueError(f"candidate path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_best"]
    metrics = current["metrics"]
    gates = payload["readme_gate_status"]["gates"]
    issue128 = payload["evidence_base"]["issue128_negative_result"]
    small = payload["small_print_boundary"]
    selected = payload["selected_next_slice"]
    return "\n".join(
        [
            "# Issue 130 Next-Slice Discovery",
            "",
            f"- Selected discovery: `{payload['selected_discovery_id']}`.",
            f"- Current best remains issue `#{current['issue']}` / PR `#{current['pr']}`.",
            f"- Selected next slice: `{selected['slice_id']}`.",
            "",
            "## Current README Gate Status",
            "",
            "| Gate | Value | Threshold | Delta | Status |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(gates['curve_mae_mean']['value'])} | "
            f"{format_metric(gates['curve_mae_mean']['threshold'])} | "
            f"{format_metric(gates['curve_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['curve_mae_mean']['pass'] else 'miss'} |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['value'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['threshold'])} | "
            f"{format_metric(gates['focus_preset_acutance_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['focus_preset_acutance_mae_mean']['pass'] else 'miss'} |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['value'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['threshold'])} | "
            f"{format_metric(gates['overall_quality_loss_mae_mean']['delta_to_gate'])} | "
            f"{'pass' if gates['overall_quality_loss_mae_mean']['pass'] else 'miss'} |",
            f"| non-phone Acutance max ({small['worst_non_phone_preset']}) | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['value'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['threshold'])} | "
            f"{format_metric(gates['non_phone_acutance_preset_mae_max']['delta_to_gate'])} | "
            f"{'pass' if gates['non_phone_acutance_preset_mae_max']['pass'] else 'miss'} |",
            f"| {PHONE_PRESET} | {format_metric(gates[PHONE_PRESET]['value'])} | "
            f"{format_metric(gates[PHONE_PRESET]['threshold'])} | "
            f"{format_metric(gates[PHONE_PRESET]['delta_to_gate'])} | "
            f"{'pass' if gates[PHONE_PRESET]['pass'] else 'miss'} |",
            "",
            "## Curve Path Decision",
            "",
            f"- PR #129 curve delta versus PR #125: `{issue128['curve_mae_delta_vs_pr125']:+.5f}`.",
            f"- PR #129 `0.15` curve delta versus PR #125: `{issue128['mixup_015_delta_vs_pr125']:+.5f}`.",
            "- Decision: do not continue broadening the issue #124 curve-only anchor mask.",
            "- Future curve work requires a per-mixup or shape-family preflight proving `0.15` improves before a full benchmark candidate.",
            "",
            "## Selected Next Slice",
            "",
            selected["selected_summary"],
            "",
            f"- Target preset: `{small['target_preset']}`.",
            f"- Current Small Print Acutance: `{format_metric(small['current_value'])}`.",
            f"- Gate delta: `{small['delta_to_gate']:+.5f}`.",
            f"- Slice type: `{selected['slice_type']}`.",
            "",
            "Minimum implementation boundary:",
            "",
            *[f"- {item}" for item in selected["minimum_implementation_boundary"]],
            "",
            "Promotion acceptance:",
            "",
            *[f"- {item}" for item in selected["promotion_acceptance"]],
            "",
            "Validation plan:",
            "",
            *[f"- {item}" for item in selected["validation_plan"]],
            "",
            "## Release Separation",
            "",
            "This remains canonical-target discovery. The selected follow-up must not alter "
            "release-facing configs or write fitted outputs under golden/reference roots.",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = args.repo_root
    payload = build_payload(
        repo_root,
        issue124_summary_path=args.issue124_summary,
        issue126_discovery_path=args.issue126_discovery,
        issue128_summary_path=args.issue128_summary,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
