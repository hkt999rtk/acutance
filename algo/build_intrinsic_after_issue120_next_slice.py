from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ISSUE = 122
SUMMARY_KIND = "intrinsic_after_issue120_next_slice"
CURRENT_BEST_LABEL = "issue118_large_print_quality_loss_input_boundary_candidate"
PR30_LABEL = "current_best_pr30_branch"
SELECTED_DISCOVERY_ID = "issue118_remaining_curve_small_print_acutance_discovery"
SELECTED_SLICE_ID = "issue118_curve_high_mixup_curve_only_boundary"
PHONE_PRESET = '5.5" Phone Display Acutance'
SMALL_PRINT_PRESET = "Small Print Acutance"
CURVE_GATE = 0.020
NON_PHONE_ACUTANCE_GATE = 0.030
FOCUS_ACUTANCE_GATE = 0.030
OVERALL_QUALITY_LOSS_GATE = 1.30
PHONE_ACUTANCE_GATE = 0.050
HIGH_MIXUP_KEYS = ("0.8", "ori")
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-122 post-issue120 next-slice discovery record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue120-summary",
        type=Path,
        default=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
        help="Repo-relative issue-120 README gate summary artifact path.",
    )
    parser.add_argument(
        "--issue118-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"),
        help="Repo-relative issue-118 summary artifact path.",
    )
    parser.add_argument(
        "--issue118-acutance-artifact",
        type=Path,
        default=Path("artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"),
        help="Repo-relative issue-118 acutance/Quality Loss benchmark artifact path.",
    )
    parser.add_argument(
        "--issue118-psd-artifact",
        type=Path,
        default=Path("artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json"),
        help="Repo-relative issue-118 PSD/MTF benchmark artifact path.",
    )
    parser.add_argument(
        "--record-summary",
        type=Path,
        default=Path(
            "artifacts/"
            "imatest_parity_reference_anchor_acutance_curve_qualityfit_allpreset_"
            "sextic_acutance_record_summary.json"
        ),
        help="Repo-relative acutance record summary used for stable mixup record counts.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue120_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue120_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def is_close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)


def select_profile(payload: dict[str, Any], profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(f"Profile {profile_path!r} not found. Available: {available}")


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
        "acutance_preset_mae": {
            key: float(candidate["acutance_preset_mae"][key] - baseline["acutance_preset_mae"][key])
            for key in candidate["acutance_preset_mae"]
        },
        "quality_loss_preset_mae": {
            key: float(
                candidate["quality_loss_preset_mae"][key]
                - baseline["quality_loss_preset_mae"][key]
            )
            for key in candidate["quality_loss_preset_mae"]
        },
    }


def readme_gate_status(current_best: dict[str, Any]) -> dict[str, Any]:
    acutance = current_best["acutance_preset_mae"]
    non_phone = {key: value for key, value in acutance.items() if key != PHONE_PRESET}
    worst_non_phone, worst_non_phone_value = max(non_phone.items(), key=lambda item: item[1])
    gates = {
        "curve_mae_mean": {
            "value": float(current_best["curve_mae_mean"]),
            "threshold": CURVE_GATE,
            "delta_to_gate": float(current_best["curve_mae_mean"] - CURVE_GATE),
            "pass": current_best["curve_mae_mean"] <= CURVE_GATE,
        },
        "focus_preset_acutance_mae_mean": {
            "value": float(current_best["focus_preset_acutance_mae_mean"]),
            "threshold": FOCUS_ACUTANCE_GATE,
            "delta_to_gate": float(
                current_best["focus_preset_acutance_mae_mean"] - FOCUS_ACUTANCE_GATE
            ),
            "pass": current_best["focus_preset_acutance_mae_mean"] <= FOCUS_ACUTANCE_GATE,
        },
        "overall_quality_loss_mae_mean": {
            "value": float(current_best["overall_quality_loss_mae_mean"]),
            "threshold": OVERALL_QUALITY_LOSS_GATE,
            "delta_to_gate": float(
                current_best["overall_quality_loss_mae_mean"] - OVERALL_QUALITY_LOSS_GATE
            ),
            "pass": current_best["overall_quality_loss_mae_mean"] <= OVERALL_QUALITY_LOSS_GATE,
        },
        "non_phone_acutance_preset_mae_max": {
            "value": float(worst_non_phone_value),
            "threshold": NON_PHONE_ACUTANCE_GATE,
            "delta_to_gate": float(worst_non_phone_value - NON_PHONE_ACUTANCE_GATE),
            "pass": worst_non_phone_value <= NON_PHONE_ACUTANCE_GATE,
            "worst_preset": worst_non_phone,
            "by_preset": {key: float(value) for key, value in sorted(non_phone.items())},
        },
        PHONE_PRESET: {
            "value": float(acutance[PHONE_PRESET]),
            "threshold": PHONE_ACUTANCE_GATE,
            "delta_to_gate": float(acutance[PHONE_PRESET] - PHONE_ACUTANCE_GATE),
            "pass": acutance[PHONE_PRESET] <= PHONE_ACUTANCE_GATE,
        },
    }
    return {
        "all_readme_gates_pass": all(gate["pass"] for gate in gates.values()),
        "failed_gates": [name for name, gate in gates.items() if not gate["pass"]],
        "gates": gates,
    }


def mixup_counts(record_summary: dict[str, Any]) -> dict[str, int]:
    return {
        mixup: int(summary["count"])
        for mixup, summary in record_summary["curve_acutance_error_by_mixup"].items()
    }


def mixup_residual_evidence(
    *,
    current_profile: dict[str, Any],
    comparison_profile: dict[str, Any],
    counts: dict[str, int],
) -> dict[str, Any]:
    current_by_mixup = current_profile["by_mixup_curve_mae_mean"]
    comparison_by_mixup = comparison_profile["by_mixup_curve_mae_mean"]
    total_count = sum(counts[mixup] for mixup in current_by_mixup)
    weighted_total = sum(current_by_mixup[mixup] * counts[mixup] for mixup in current_by_mixup)
    by_mixup = {}
    for mixup in sorted(current_by_mixup, key=lambda item: (item == "ori", float(item) if item != "ori" else 9.9)):
        weighted_contribution = current_by_mixup[mixup] * counts[mixup] / total_count
        by_mixup[mixup] = {
            "current_best_curve_mae": float(current_by_mixup[mixup]),
            "comparison_curve_mae": float(comparison_by_mixup[mixup]),
            "delta_vs_comparison": float(current_by_mixup[mixup] - comparison_by_mixup[mixup]),
            "record_count": counts[mixup],
            "record_fraction": counts[mixup] / total_count,
            "weighted_contribution_to_curve_mae": float(weighted_contribution),
            "weighted_error_share": float(
                (current_by_mixup[mixup] * counts[mixup]) / weighted_total
            ),
            "passes_curve_gate_if_viewed_alone": current_by_mixup[mixup] <= CURVE_GATE,
        }
    high_mixup_weighted_share = sum(
        by_mixup[mixup]["weighted_error_share"] for mixup in HIGH_MIXUP_KEYS
    )
    high_mixup_record_fraction = sum(by_mixup[mixup]["record_fraction"] for mixup in HIGH_MIXUP_KEYS)
    high_mixup_deltas = {
        mixup: by_mixup[mixup]["delta_vs_comparison"] for mixup in HIGH_MIXUP_KEYS
    }
    low_mid_already_below_gate = {
        mixup: by_mixup[mixup]["passes_curve_gate_if_viewed_alone"]
        for mixup in ("0.4", "0.65")
    }
    return {
        "comparison_profile_path": comparison_profile["profile_path"],
        "current_profile_path": current_profile["profile_path"],
        "weighted_curve_mae_mean": float(weighted_total / total_count),
        "total_curve_record_count": total_count,
        "by_mixup": by_mixup,
        "high_mixup_keys": list(HIGH_MIXUP_KEYS),
        "high_mixup_weighted_error_share": float(high_mixup_weighted_share),
        "high_mixup_record_fraction": float(high_mixup_record_fraction),
        "high_mixup_deltas_vs_comparison": high_mixup_deltas,
        "low_mid_already_below_gate": low_mid_already_below_gate,
    }


def quality_loss_boundary_invariance(profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels = [
        "issue108_pr30_observed_bundle_candidate",
        "issue114_computer_monitor_quality_loss_input_boundary_candidate",
        "issue116_small_print_quality_loss_input_boundary_candidate",
        CURRENT_BEST_LABEL,
    ]
    first = profiles[labels[0]]
    keys = [
        "curve_mae_mean",
        "focus_preset_acutance_mae_mean",
        "mtf_abs_signed_rel_mean",
    ]
    invariant_keys = {
        key: all(is_close(profiles[label][key], first[key]) for label in labels[1:])
        for key in keys
    }
    invariant_presets = {
        preset: all(
            is_close(
                profiles[label]["acutance_preset_mae"][preset],
                first["acutance_preset_mae"][preset],
            )
            for label in labels[1:]
        )
        for preset in first["acutance_preset_mae"]
    }
    return {
        "profile_labels": labels,
        "invariant_core_metrics": invariant_keys,
        "invariant_acutance_presets": invariant_presets,
        "all_curve_and_acutance_metrics_invariant": all(invariant_keys.values())
        and all(invariant_presets.values()),
        "interpretation": (
            "The issue #114, #116, and #118 Quality Loss input-boundary changes do not move "
            "curve MAE, focus Acutance, reported-MTF, or any Acutance preset MAE. The remaining "
            "README misses therefore sit on the upstream Acutance/curve branch, not on the "
            "Quality Loss mapping branch."
        ),
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        if path.startswith(GOLDEN_REFERENCE_ROOTS):
            raise ValueError(f"Path {path} leaks into golden/reference root")


def build_payload(
    repo_root: Path,
    *,
    issue120_summary_path: Path,
    issue118_summary_path: Path,
    issue118_acutance_artifact_path: Path,
    issue118_psd_artifact_path: Path,
    record_summary_path: Path,
) -> dict[str, Any]:
    issue120_summary = load_json(resolve_path(repo_root, issue120_summary_path))
    issue118_summary = load_json(resolve_path(repo_root, issue118_summary_path))
    acutance_artifact = load_json(resolve_path(repo_root, issue118_acutance_artifact_path))
    psd_artifact = load_json(resolve_path(repo_root, issue118_psd_artifact_path))
    record_summary = load_json(resolve_path(repo_root, record_summary_path))

    current_best_profile_path = issue120_summary["current_best"]["profile_path"]
    current_best = issue118_summary["profiles"][CURRENT_BEST_LABEL]
    pr30 = issue118_summary["profiles"][PR30_LABEL]
    if current_best["profile_path"] != current_best_profile_path:
        raise ValueError("Issue #120 current-best path diverges from issue #118 summary")

    current_acutance_profile = select_profile(acutance_artifact, current_best_profile_path)
    current_psd_profile = select_profile(psd_artifact, current_best_profile_path)
    comparison_acutance_profile = acutance_artifact["profiles"][0]

    if not is_close(
        current_acutance_profile["overall"]["curve_mae_mean"],
        current_best["curve_mae_mean"],
    ):
        raise ValueError("Issue #118 acutance artifact diverges from embedded current-best summary")
    if not is_close(
        current_psd_profile["overall"]["mtf_abs_signed_rel_mean"],
        current_best["mtf_abs_signed_rel_mean"],
    ):
        raise ValueError("Issue #118 PSD artifact diverges from embedded current-best summary")

    readme_status = readme_gate_status(current_best)
    current_vs_pr30 = delta_map(current_best, pr30)
    mixup_evidence = mixup_residual_evidence(
        current_profile=current_acutance_profile,
        comparison_profile=comparison_acutance_profile,
        counts=mixup_counts(record_summary),
    )
    ql_invariance = quality_loss_boundary_invariance(issue118_summary["profiles"])

    split_recommendation = {
        "recommendation": "split_remaining_misses",
        "reason": (
            "The curve miss is the dominant README miss and is concentrated in high-mixup/ori "
            "curve records, while the only non-Phone Acutance miss is a small Small Print preset "
            "excess. Existing issue #114/#116/#118 Quality Loss boundary changes leave all curve "
            "and Acutance-preset metrics invariant, so a single Quality Loss or broad readout "
            "slice is not supported by the current evidence."
        ),
        "first_slice": SELECTED_SLICE_ID,
        "defer_slice": "issue118_small_print_acutance_preset_only_boundary",
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "selected": True,
            "selected_summary": (
                "Isolate a curve-only boundary on the issue #118 profile that targets the "
                "high-mixup/ori curve tail while leaving preset Acutance, Quality Loss, and "
                "reported-MTF branches unchanged."
            ),
            "repo_evidence": [
                "Issue #120 records curve MAE as the largest remaining gate miss.",
                "`0.8` and `ori` are only 30% of curve records but contribute more than half of weighted curve MAE.",
                "The current issue #118 profile already keeps reported-MTF parity with PR #30.",
                "Prior curve-side mid-scale clip-hi work showed curve-only Acutance correction can move curve MAE while holding preset Acutance and Quality Loss fixed.",
            ],
            "minimum_implementation_boundary": [
                "Start from the issue #118 current-best profile.",
                "Touch only the curve-side Acutance/intrinsic-full-reference boundary used to produce `curve_mae_mean`.",
                "Do not alter `quality_loss_preset_input_profile_overrides`, Quality Loss coefficients, reported-MTF compensation/readout settings, or release-facing configs.",
            ],
            "expected_preservation": {
                "reported_mtf_parity": "preserve",
                "overall_quality_loss_mae_mean": "preserve",
                "focus_preset_acutance_mae_mean": "preserve_or_non_worse",
                "small_print_acutance": "preserve_or_measure_tradeoff",
            },
            "validation_plan": [
                "Regenerate PSD/MTF and Acutance/Quality Loss benchmarks for the candidate.",
                "Compare README gates against PR #119 and PR #30.",
                "Require `mtf20`, `mtf30`, `mtf50`, and `mtf_abs_signed_rel_mean` to remain equal to PR #119 unless the tradeoff is explicitly accepted.",
                "Require `overall_quality_loss_mae_mean <= 1.20435969` or an explicit non-promotion result.",
            ],
        },
        {
            "slice_id": "issue118_small_print_acutance_preset_only_boundary",
            "selected": False,
            "selected_summary": (
                "A later split, only if needed, should target the Small Print Acutance preset "
                "boundary after the curve-tail slice proves whether it preserves or improves the "
                "small preset miss."
            ),
            "repo_evidence": [
                "Small Print Acutance misses the non-Phone gate by only +0.00172625.",
                "The issue #118 branch already improves Small Print Acutance versus PR #30 by about -0.01497.",
                "The focus-preset Acutance mean and Phone Acutance gates already pass.",
            ],
            "minimum_implementation_boundary": [
                "Do not retune Quality Loss coefficients.",
                "Do not alter reported-MTF/readout settings.",
                "Restrict any later preset experiment to the Small Print Acutance branch.",
            ],
            "expected_preservation": {
                "reported_mtf_parity": "preserve",
                "overall_quality_loss_mae_mean": "preserve",
                "curve_mae_mean": "preserve_or_measure_tradeoff",
            },
            "validation_plan": [
                "Compare Small Print Acutance against the <= 0.030 gate.",
                "Verify focus-preset Acutance mean remains <= 0.030.",
                "Verify PR #119 Quality Loss and reported-MTF record is preserved.",
            ],
        },
    ]

    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "selected_discovery_id": SELECTED_DISCOVERY_ID,
        "selected_slice_id": SELECTED_SLICE_ID,
        "current_best": {
            "label": CURRENT_BEST_LABEL,
            "profile_path": current_best["profile_path"],
            "metrics": {
                "curve_mae_mean": float(current_best["curve_mae_mean"]),
                "focus_preset_acutance_mae_mean": float(
                    current_best["focus_preset_acutance_mae_mean"]
                ),
                "overall_quality_loss_mae_mean": float(
                    current_best["overall_quality_loss_mae_mean"]
                ),
                "mtf_abs_signed_rel_mean": float(current_best["mtf_abs_signed_rel_mean"]),
                "mtf_threshold_mae": {
                    key: float(value) for key, value in current_best["mtf_threshold_mae"].items()
                },
                "acutance_preset_mae": {
                    key: float(value) for key, value in current_best["acutance_preset_mae"].items()
                },
            },
        },
        "comparisons": {
            "current_best_vs_pr30": {"delta": current_vs_pr30},
        },
        "readme_gate_status": readme_status,
        "residual_curve_evidence": mixup_evidence,
        "residual_small_print_evidence": {
            "small_print_value": float(current_best["acutance_preset_mae"][SMALL_PRINT_PRESET]),
            "threshold": NON_PHONE_ACUTANCE_GATE,
            "delta_to_gate": float(
                current_best["acutance_preset_mae"][SMALL_PRINT_PRESET]
                - NON_PHONE_ACUTANCE_GATE
            ),
            "delta_vs_pr30": current_vs_pr30["acutance_preset_mae"][SMALL_PRINT_PRESET],
            "only_non_phone_preset_miss": (
                readme_status["gates"]["non_phone_acutance_preset_mae_max"]["worst_preset"]
                == SMALL_PRINT_PRESET
            ),
        },
        "quality_loss_boundary_invariance": ql_invariance,
        "split_recommendation": split_recommendation,
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue120_next_slice_benchmark.json",
                "docs/intrinsic_after_issue120_next_slice.md",
            ],
            "rules": [
                "This issue is a canonical-target discovery record, not a release config promotion.",
                "Do not write fitted profiles, transfer tables, or generated outputs under golden/reference roots.",
                "Do not touch release-facing configs until a later implementation clears the README gates.",
            ],
        },
        "refs": {
            "umbrella_issue": 29,
            "current_issue": 122,
            "source_issue": 120,
            "current_best_issue": 118,
            "current_best_pr": 119,
            "gate_summary_pr": 121,
            "baseline_pr": 30,
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_best"]
    gates = payload["readme_gate_status"]["gates"]
    curve = payload["residual_curve_evidence"]
    small_print = payload["residual_small_print_evidence"]
    selected = next(row for row in payload["candidate_slices"] if row["selected"])

    lines = [
        "# Intrinsic After Issue 120 Next Slice",
        "",
        "Issue `#122` is the developer-discovery pass selected by issue `#120` / PR `#121`.",
        "",
        "## Current Best",
        "",
        f"- Profile: `{current['profile_path']}`",
        f"- `curve_mae_mean = {format_metric(current['metrics']['curve_mae_mean'])}`; README gate delta `{gates['curve_mae_mean']['delta_to_gate']:+.5f}`.",
        f"- `focus_preset_acutance_mae_mean = {format_metric(current['metrics']['focus_preset_acutance_mae_mean'])}`; gate status `{gates['focus_preset_acutance_mae_mean']['pass']}`.",
        f"- `overall_quality_loss_mae_mean = {format_metric(current['metrics']['overall_quality_loss_mae_mean'])}`; gate status `{gates['overall_quality_loss_mae_mean']['pass']}`.",
        f"- `Small Print Acutance = {format_metric(small_print['small_print_value'])}`; non-Phone gate delta `{small_print['delta_to_gate']:+.5f}`.",
        "",
        "## Curve Residual Evidence",
        "",
        f"- Weighted curve MAE recomputed from mixup records: `{format_metric(curve['weighted_curve_mae_mean'])}`.",
        f"- High-mixup keys `{', '.join(curve['high_mixup_keys'])}` are `{curve['high_mixup_record_fraction']:.3f}` of curve records but `{curve['high_mixup_weighted_error_share']:.3f}` of weighted curve error.",
        f"- Current `0.8` curve MAE: `{format_metric(curve['by_mixup']['0.8']['current_best_curve_mae'])}`; delta versus the comparison profile `{curve['by_mixup']['0.8']['delta_vs_comparison']:+.5f}`.",
        f"- Current `ori` curve MAE: `{format_metric(curve['by_mixup']['ori']['current_best_curve_mae'])}`; delta versus the comparison profile `{curve['by_mixup']['ori']['delta_vs_comparison']:+.5f}`.",
        f"- Lower/mid checks already under gate: `0.4 = {curve['low_mid_already_below_gate']['0.4']}`, `0.65 = {curve['low_mid_already_below_gate']['0.65']}`.",
        "",
        "## Split Decision",
        "",
        f"- Recommendation: `{payload['split_recommendation']['recommendation']}`",
        f"- Reason: {payload['split_recommendation']['reason']}",
        f"- First slice: `{payload['split_recommendation']['first_slice']}`",
        f"- Deferred slice: `{payload['split_recommendation']['defer_slice']}`",
        "",
        "## Selected Next Slice",
        "",
        f"- Slice id: `{selected['slice_id']}`",
        f"- Summary: {selected['selected_summary']}",
        "",
        "Repo evidence:",
        "",
    ]
    for item in selected["repo_evidence"]:
        lines.append(f"- {item}")
    lines.extend(["", "Minimum implementation boundary:", ""])
    for item in selected["minimum_implementation_boundary"]:
        lines.append(f"- {item}")
    lines.extend(["", "Expected preservation:", ""])
    for key, value in selected["expected_preservation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "Validation plan:", ""])
    for item in selected["validation_plan"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Quality Loss Boundary Evidence",
            "",
            f"- Curve and Acutance metrics invariant across issue #108/#114/#116/#118 Quality Loss boundary records: `{payload['quality_loss_boundary_invariance']['all_curve_and_acutance_metrics_invariant']}`.",
            f"- Interpretation: {payload['quality_loss_boundary_invariance']['interpretation']}",
            "",
            "## Storage Separation",
            "",
        ]
    )
    for rule in payload["storage_policy"]["rules"]:
        lines.append(f"- {rule}")
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(
        repo_root,
        issue120_summary_path=args.issue120_summary,
        issue118_summary_path=args.issue118_summary,
        issue118_acutance_artifact_path=args.issue118_acutance_artifact,
        issue118_psd_artifact_path=args.issue118_psd_artifact,
        record_summary_path=args.record_summary,
    )
    write_text(
        resolve_path(repo_root, args.output_json),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    write_text(resolve_path(repo_root, args.output_md), render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
