from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue85_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE47_LABEL = "issue47_phase_retained_replace_all"
ISSUE81_LABEL = "issue81_quality_loss_isolation_candidate"
ISSUE85_LABEL = "issue85_readout_reconnect_quality_loss_isolation_candidate"
SELECTED_SLICE_ID = (
    "phase_retained_intrinsic_matched_ori_correction_graft_with_quality_loss_isolation"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-87 intrinsic post-issue85 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue83-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue81_next_slice_benchmark.json"),
        help="Repo-relative issue-83 discovery artifact path.",
    )
    parser.add_argument(
        "--issue85-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_readout_reconnect_benchmark.json"),
        help="Repo-relative issue-85 summary artifact path.",
    )
    parser.add_argument(
        "--issue47-psd-artifact",
        type=Path,
        default=Path("artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json"),
        help="Repo-relative issue-47 PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--issue47-acutance-artifact",
        type=Path,
        default=Path("artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json"),
        help="Repo-relative issue-47 acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--issue81-psd-artifact",
        type=Path,
        default=Path("artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_psd_benchmark.json"),
        help="Repo-relative issue-81 PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--issue81-acutance-artifact",
        type=Path,
        default=Path("artifacts/issue81_intrinsic_phase_retained_quality_loss_isolation_acutance_benchmark.json"),
        help="Repo-relative issue-81 acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--issue85-psd-artifact",
        type=Path,
        default=Path("artifacts/issue85_intrinsic_phase_retained_readout_reconnect_psd_benchmark.json"),
        help="Repo-relative issue-85 PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--issue85-acutance-artifact",
        type=Path,
        default=Path("artifacts/issue85_intrinsic_phase_retained_readout_reconnect_acutance_benchmark.json"),
        help="Repo-relative issue-85 acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--current-best-psd-artifact",
        type=Path,
        default=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
        help="Repo-relative current-best PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--current-best-acutance-artifact",
        type=Path,
        default=Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"),
        help="Repo-relative current-best acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue85_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue85_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def format_paths(paths: list[str]) -> str:
    return ", ".join(f"`{path}`" for path in paths)


def select_profile(payload: dict[str, Any], expected_profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == expected_profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(
        f"Profile {expected_profile_path!r} not found in artifact. Available: {available}"
    )


def profile_detail(
    *,
    psd_payload: dict[str, Any],
    acutance_payload: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    psd_profile = select_profile(psd_payload, profile_path)
    acutance_profile = select_profile(acutance_payload, profile_path)
    return {
        "mtf_band_mae": {
            key: float(value["mae_mean"])
            for key, value in psd_profile["overall"]["mtf_bands"].items()
        },
        "acutance_preset_mae": {
            key: float(value)
            for key, value in acutance_profile["overall"]["acutance_preset_mae"].items()
        },
        "quality_loss_preset_mae": {
            key: float(value)
            for key, value in acutance_profile["overall"]["quality_loss_preset_mae"].items()
        },
        "quality_loss_focus_preset_mae_mean": float(
            acutance_profile["overall"]["quality_loss_focus_preset_mae_mean"]
        ),
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


def is_close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)


def maps_match(lhs: dict[str, float], rhs: dict[str, float]) -> bool:
    return lhs.keys() == rhs.keys() and all(is_close(lhs[key], rhs[key]) for key in lhs)


def pipeline_gap_summary(current_best: dict[str, Any], issue85: dict[str, Any]) -> dict[str, Any]:
    current_pipeline = current_best["analysis_pipeline"]
    issue85_pipeline = issue85["analysis_pipeline"]
    keys = [
        "matched_ori_reference_anchor",
        "matched_ori_strength_curve_frequencies",
        "matched_ori_strength_curve_values",
        "matched_ori_acutance_reference_anchor",
        "matched_ori_acutance_strength_curve_relative_scales",
        "matched_ori_acutance_strength_curve_values",
        "matched_ori_acutance_curve_correction_clip_hi_relative_scales",
        "matched_ori_acutance_curve_correction_clip_hi_values",
        "matched_ori_acutance_preset_correction_delta_power_relative_scales",
        "matched_ori_acutance_preset_correction_delta_power_values",
        "matched_ori_acutance_preset_strength_curve_relative_scales",
        "matched_ori_acutance_preset_strength_curve_values",
    ]
    return {
        key: {
            "current_best_pr30_branch": current_pipeline.get(key),
            "issue85_readout_reconnect_quality_loss_isolation_candidate": issue85_pipeline.get(key),
        }
        for key in keys
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(
    repo_root: Path,
    *,
    issue83_artifact_path: Path,
    issue85_artifact_path: Path,
    issue47_psd_artifact_path: Path,
    issue47_acutance_artifact_path: Path,
    issue81_psd_artifact_path: Path,
    issue81_acutance_artifact_path: Path,
    issue85_psd_artifact_path: Path,
    issue85_acutance_artifact_path: Path,
    current_best_psd_artifact_path: Path,
    current_best_acutance_artifact_path: Path,
) -> dict[str, Any]:
    issue83_artifact = load_json(resolve_path(repo_root, issue83_artifact_path))
    issue85_artifact = load_json(resolve_path(repo_root, issue85_artifact_path))

    comparison_records = {
        CURRENT_BEST_LABEL: issue85_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE47_LABEL: issue85_artifact["profiles"][ISSUE47_LABEL],
        ISSUE81_LABEL: issue85_artifact["profiles"][ISSUE81_LABEL],
        ISSUE85_LABEL: issue85_artifact["profiles"][ISSUE85_LABEL],
    }

    current_best_details = profile_detail(
        psd_payload=load_json(resolve_path(repo_root, current_best_psd_artifact_path)),
        acutance_payload=load_json(resolve_path(repo_root, current_best_acutance_artifact_path)),
        profile_path=comparison_records[CURRENT_BEST_LABEL]["profile_path"],
    )
    issue47_details = profile_detail(
        psd_payload=load_json(resolve_path(repo_root, issue47_psd_artifact_path)),
        acutance_payload=load_json(resolve_path(repo_root, issue47_acutance_artifact_path)),
        profile_path=comparison_records[ISSUE47_LABEL]["profile_path"],
    )
    issue81_details = profile_detail(
        psd_payload=load_json(resolve_path(repo_root, issue81_psd_artifact_path)),
        acutance_payload=load_json(resolve_path(repo_root, issue81_acutance_artifact_path)),
        profile_path=comparison_records[ISSUE81_LABEL]["profile_path"],
    )
    issue85_details = profile_detail(
        psd_payload=load_json(resolve_path(repo_root, issue85_psd_artifact_path)),
        acutance_payload=load_json(resolve_path(repo_root, issue85_acutance_artifact_path)),
        profile_path=comparison_records[ISSUE85_LABEL]["profile_path"],
    )
    detail_records = {
        CURRENT_BEST_LABEL: current_best_details,
        ISSUE47_LABEL: issue47_details,
        ISSUE81_LABEL: issue81_details,
        ISSUE85_LABEL: issue85_details,
    }

    issue85 = comparison_records[ISSUE85_LABEL]
    issue81 = comparison_records[ISSUE81_LABEL]
    issue47 = comparison_records[ISSUE47_LABEL]
    current_best = comparison_records[CURRENT_BEST_LABEL]

    residual_alignment = {
        "issue85_quality_loss_matches_issue81": {
            "overall_quality_loss_mae_mean": is_close(
                issue85["overall_quality_loss_mae_mean"],
                issue81["overall_quality_loss_mae_mean"],
            ),
            "quality_loss_focus_preset_mae_mean": is_close(
                issue85_details["quality_loss_focus_preset_mae_mean"],
                issue81_details["quality_loss_focus_preset_mae_mean"],
            ),
            "quality_loss_preset_mae": maps_match(
                issue85_details["quality_loss_preset_mae"],
                issue81_details["quality_loss_preset_mae"],
            ),
        },
        "issue85_readout_matches_issue47": {
            "mtf_abs_signed_rel_mean": is_close(
                issue85["mtf_abs_signed_rel_mean"],
                issue47["mtf_abs_signed_rel_mean"],
            ),
            "mtf_threshold_mae": maps_match(
                issue85["mtf_threshold_mae"],
                issue47["mtf_threshold_mae"],
            ),
            "mtf_band_mae": maps_match(
                issue85_details["mtf_band_mae"],
                issue47_details["mtf_band_mae"],
            ),
        },
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "graft the current-best PR30 matched-ori correction and acutance-anchor family onto issue-85's split topology",
            "decision": "advance",
            "technical_narrowing_point": (
                "issue85_left_two_residuals_that_map_to_existing_downstream_correction_boundaries_"
                "rather_than_to_new_intrinsic_transfer_or_registration_families"
            ),
            "selected_summary": (
                "Keep issue #85's phase-retained intrinsic transfer, readout reconnect, and "
                "downstream Quality Loss isolation, but graft the current-best PR30 matched-ori "
                "correction / acutance-anchor family onto the readout path and the isolated "
                "Quality Loss branch."
            ),
            "repo_evidence": [
                "Issue #85's `overall_quality_loss_mae_mean` is exactly equal to issue #81, including the per-preset Quality Loss errors, so the remaining overall Quality Loss gap did not move when readout reconnect landed.",
                "Issue #85's `mtf_abs_signed_rel_mean`, threshold errors, and MTF band errors are exactly equal to issue #47, so the residual `mtf20` gap also predates issue #85's split and stays on the readout side.",
                "The current-best PR30 branch carries a tuned matched-ori reference-correction family and acutance-anchor family that issue #85 does not enable, which is the largest still-untried downstream boundary shared by the remaining `overall_quality_loss_mae_mean` and `mtf20` gaps.",
                "The low-band MTF MAE on issue #85 is already better than PR30, yet `mtf20` is still farther away. That points to threshold-crossing / correction-shape behavior rather than to a missing wholesale intrinsic transfer family.",
            ],
            "comparison_basis": {
                "issue85_vs_current_best_pr30": {
                    "delta": delta_map(issue85, current_best),
                },
                "issue85_vs_issue47": {
                    "delta": delta_map(issue85, issue47),
                    "readout_metrics_match_issue47": residual_alignment[
                        "issue85_readout_matches_issue47"
                    ],
                },
                "issue85_vs_issue81": {
                    "delta": delta_map(issue85, issue81),
                    "quality_loss_metrics_match_issue81": residual_alignment[
                        "issue85_quality_loss_matches_issue81"
                    ],
                },
                "issue83_selected_slice_id": issue83_artifact["selected_slice_id"],
            },
            "runtime_boundary_evidence": [
                {
                    "file_path": "algo/benchmark_parity_psd_mtf.py",
                    "line_range": "502-508, 509-653, 654-659",
                    "observations": [
                        "Issue #85 already reconnects the phase-retained intrinsic branch into `compensated_mtf` when the scope is `readout_reconnect_quality_loss_isolation`.",
                        "The matched-ori reference correction then applies directly to both `compensated_mtf` and `compensated_mtf_for_acutance`, so the next bounded slice can target readout correction without touching the intrinsic transfer derivation.",
                        "`compute_mtf_metrics(...)` still reads thresholds from the corrected `compensated_mtf`, which makes this the narrowest live boundary for the residual `mtf20` gap.",
                    ],
                },
                {
                    "file_path": "algo/benchmark_parity_acutance_quality_loss.py",
                    "line_range": "329-337, 745-869, 921-948, 1003-1008",
                    "observations": [
                        "`maybe_anchor_acutance_results(...)` is gated by `matched_ori_acutance_reference_anchor`, and it runs on both the main acutance path and the isolated Quality Loss acutance path.",
                        "The matched-ori reference correction also applies to `quality_loss_compensated_mtf_for_acutance`, which means one bounded graft can influence both the residual overall Quality Loss gap and the readout-side threshold shape.",
                        "`quality_loss_presets_from_acutance(...)` consumes that isolated downstream acutance path after correction and anchoring, so the next issue can stay bounded to downstream correction/anchor behavior rather than reopening intrinsic transfer or OECF work.",
                    ],
                },
            ],
            "minimum_implementation_boundary": [
                "Keep issue #85's `readout_reconnect_quality_loss_isolation` topology and `radial_real_mean` / `phase_correlation` intrinsic path unchanged.",
                "Add one bounded mode or profile family that grafts PR30's matched-ori reference correction onto the issue-85 readout path, including the `matched_ori_reference_anchor` strength-curve settings used around `compensated_mtf`.",
                "Apply the same bounded graft to the isolated downstream Quality Loss path, including the `matched_ori_acutance_reference_anchor` family that runs through `maybe_anchor_acutance_results(...)`.",
                "Keep downstream Quality Loss isolated off the non-intrinsic branch; do not collapse back to `replace_all`.",
            ],
            "explicitly_do_not_change": [
                "Do not change intrinsic transfer mode, registration mode, or restart a wider intrinsic-family sweep.",
                "Do not reopen measured OECF or affine-registration branches.",
                "Do not retune release-facing PR30 coefficients directly or promote any fitted intrinsic profile into release-facing config in this issue.",
                "Do not write fitted profiles, transfer tables, or generated outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The new bounded graft preserves issue #85's curve and focus-preset Acutance gains closely enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` are no worse than issue #85.",
                "The same implementation improves `overall_quality_loss_mae_mean` versus issue #85 while keeping the isolated downstream Quality Loss routing intact.",
                "The same implementation improves `mtf20` toward the current PR #30 branch versus issue #85 and does not give back the issue-85 `mtf_abs_signed_rel_mean` improvement.",
                "All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-85-based profile that enables the bounded matched-ori correction graft, then compare thresholds and `mtf_abs_signed_rel_mean` against issue #85 and PR #30.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair to confirm `overall_quality_loss_mae_mean` improves without collapsing the isolated downstream branch.",
                "Add focused tests that cover the graft across `compensated_mtf`, `compensated_mtf_for_acutance`, `quality_loss_compensated_mtf_for_acutance`, and `maybe_anchor_acutance_results(...)`.",
            ],
        },
        {
            "slice_id": "promote_issue85_as_is",
            "label": "promote issue-85 scope as-is",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #85 is a real bounded positive, but it still trails PR #30 materially on `overall_quality_loss_mae_mean` and does not improve `mtf20` toward the current best branch.",
                "Promoting it without another narrowing pass would skip the exact residual gaps this issue was created to isolate.",
            ],
        },
        {
            "slice_id": "reopen_measured_oecf_family",
            "label": "reopen measured OECF",
            "decision": "exclude",
            "exclusion_reasons": [
                "Measured OECF already closed as a bounded negative in issue #77 / PR #78.",
                "Issue #87 is downstream of issue #85's intrinsic split result, and the surviving gap maps to correction / anchor boundaries that already exist in the repo.",
            ],
        },
        {
            "slice_id": "rerun_affine_registration_intrinsic",
            "label": "rerun affine-registration intrinsic variant",
            "decision": "exclude",
            "exclusion_reasons": [
                "Affine registration was already dominated by the phase-correlation intrinsic path and is still explicitly out of scope for this narrowing pass.",
                "The issue-85 residuals match earlier branches exactly, which points to post-transfer downstream correction rather than to registration choice.",
            ],
        },
        {
            "slice_id": "restart_unbounded_intrinsic_inventory",
            "label": "restart an unbounded intrinsic family search",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #87 is a developer-discovery narrowing pass, not a license to reopen the full intrinsic search tree.",
                "The repo already contains one implementable next slice with code-level boundary evidence, so broader family churn would be workflow regress rather than progress.",
            ],
        },
    ]

    payload = {
        "issue": 87,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue83_summary_artifact": str(issue83_artifact_path),
            "issue83_selected_slice_id": issue83_artifact["selected_slice_id"],
            "issue85_summary_artifact": str(issue85_artifact_path),
            "issue85_conclusion_status": issue85_artifact["conclusion"]["status"],
        },
        "comparison_records": comparison_records,
        "detail_records": detail_records,
        "residual_alignment_evidence": residual_alignment,
        "pipeline_gap_summary": pipeline_gap_summary(current_best, issue85),
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue85_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep this issue's discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Do not touch release-facing configs until a later bounded implementation actually clears the current README-facing guardrails.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )
    issue83_selected = payload["source_artifacts"]["issue83_selected_slice_id"]
    records = payload["comparison_records"]
    details = payload["detail_records"]

    lines = [
        "# Intrinsic After Issue 85 Next Slice",
        "",
        "This note records the issue `#87` developer-discovery pass after issue `#85` / PR `#86` proved that the intrinsic line can reconnect the readout path without giving back the issue-81 downstream Quality Loss isolation gains.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        f"- Prior narrowing lineage: issue `#83` selected `{issue83_selected}`, and issue `#85` implemented it successfully.",
        "- Remaining gap location: the surviving `overall_quality_loss_mae_mean` and `mtf20` gaps now point to the still-missing matched-ori downstream correction / anchor family, not to a new intrinsic transfer family.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Quality Loss |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    readouts = {
        CURRENT_BEST_LABEL: "Current best branch; already carries the matched-ori downstream correction stack.",
        ISSUE47_LABEL: "Phase-retained intrinsic baseline; its readout metrics exactly match issue #85.",
        ISSUE81_LABEL: "Quality Loss isolation landed; its overall Quality Loss metrics exactly match issue #85.",
        ISSUE85_LABEL: "Readout reconnect landed; residual `mtf20` / overall Quality Loss gap still remains.",
    }
    order = [CURRENT_BEST_LABEL, ISSUE47_LABEL, ISSUE81_LABEL, ISSUE85_LABEL]
    for key in order:
        record = records[key]
        mtf = record["mtf_threshold_mae"]
        lines.append(
            f"| {key} | "
            f"{format_metric(record['curve_mae_mean'])} | "
            f"{format_metric(record['focus_preset_acutance_mae_mean'])} | "
            f"{format_metric(record['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(mtf['mtf20'])} | "
            f"{format_metric(mtf['mtf30'])} | "
            f"{format_metric(mtf['mtf50'])} | "
            f"{format_metric(record['mtf_abs_signed_rel_mean'])} | "
            f"{readouts[key]} |"
        )

    lines.extend(
        [
            "",
            "## Why The Gap Still Remains After Issue 85",
            "",
        ]
    )
    for reason in selected["repo_evidence"]:
        lines.append(f"- {reason}")

    lines.extend(
        [
            "",
            "## Residual Alignment Evidence",
            "",
            f"- Issue `#85` and issue `#81` have identical overall Quality Loss MAE: `{format_metric(records[ISSUE85_LABEL]['overall_quality_loss_mae_mean'])}`.",
            f"- Issue `#85` and issue `#47` have identical `mtf_abs_signed_rel_mean`: `{format_metric(records[ISSUE85_LABEL]['mtf_abs_signed_rel_mean'])}`.",
            f"- Issue `#85` Quality Loss focus-preset MAE mean also matches issue `#81`: `{format_metric(details[ISSUE85_LABEL]['quality_loss_focus_preset_mae_mean'])}`.",
            "",
            "### Issue 85 Quality Loss Preset Errors",
            "",
            "| Preset | PR30 | Issue47 | Issue81 | Issue85 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for preset in details[CURRENT_BEST_LABEL]["quality_loss_preset_mae"]:
        lines.append(
            f"| {preset} | "
            f"{format_metric(details[CURRENT_BEST_LABEL]['quality_loss_preset_mae'][preset])} | "
            f"{format_metric(details[ISSUE47_LABEL]['quality_loss_preset_mae'][preset])} | "
            f"{format_metric(details[ISSUE81_LABEL]['quality_loss_preset_mae'][preset])} | "
            f"{format_metric(details[ISSUE85_LABEL]['quality_loss_preset_mae'][preset])} |"
        )

    lines.extend(
        [
            "",
            "### Issue 85 MTF Band Errors",
            "",
            "| Band | PR30 | Issue47 | Issue81 | Issue85 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for band in ("low", "mid", "high", "top"):
        lines.append(
            f"| {band} | "
            f"{format_metric(details[CURRENT_BEST_LABEL]['mtf_band_mae'][band])} | "
            f"{format_metric(details[ISSUE47_LABEL]['mtf_band_mae'][band])} | "
            f"{format_metric(details[ISSUE81_LABEL]['mtf_band_mae'][band])} | "
            f"{format_metric(details[ISSUE85_LABEL]['mtf_band_mae'][band])} |"
        )

    lines.extend(
        [
            "",
            "## Pipeline Gap Versus PR30",
            "",
            "The current-best PR30 branch still carries the matched-ori correction / anchor family that issue `#85` does not enable:",
            "",
        ]
    )
    for key, values in payload["pipeline_gap_summary"].items():
        lines.append(
            f"- `{key}`: PR30={values['current_best_pr30_branch']!r}, issue85={values['issue85_readout_reconnect_quality_loss_isolation_candidate']!r}"
        )

    lines.extend(
        [
            "",
            "## Runtime Boundary Evidence",
            "",
        ]
    )
    for row in selected["runtime_boundary_evidence"]:
        lines.append(f"### `{row['file_path']}` ({row['line_range']})")
        lines.append("")
        for observation in row["observations"]:
            lines.append(f"- {observation}")
        lines.append("")

    lines.extend(
        [
            "## Excluded Routes",
            "",
        ]
    )
    for row in payload["candidate_slices"]:
        if row["decision"] == "advance":
            continue
        lines.append(f"### {row['label']}")
        lines.append("")
        for reason in row["exclusion_reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    lines.extend(
        [
            "## Implementation Boundary",
            "",
        ]
    )
    for step in selected["minimum_implementation_boundary"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Explicit Non-Changes",
            "",
        ]
    )
    for item in selected["explicitly_do_not_change"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Storage Separation",
            "",
            f"- Golden/reference roots: {format_paths(payload['storage_policy']['golden_reference_roots'])}",
            f"- Fitted artifact roots: {format_paths(payload['storage_policy']['fitted_artifact_roots'])}",
            f"- Release config roots: {format_paths(payload['storage_policy']['release_config_roots'])}",
        ]
    )
    for rule in payload["storage_policy"]["rules"]:
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## Acceptance For The Next Implementation Issue",
            "",
        ]
    )
    for item in selected["acceptance_criteria_for_next_issue"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Validation Plan For The Next Implementation Issue",
            "",
        ]
    )
    for item in selected["validation_plan_for_next_issue"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(
        repo_root,
        issue83_artifact_path=args.issue83_artifact,
        issue85_artifact_path=args.issue85_artifact,
        issue47_psd_artifact_path=args.issue47_psd_artifact,
        issue47_acutance_artifact_path=args.issue47_acutance_artifact,
        issue81_psd_artifact_path=args.issue81_psd_artifact,
        issue81_acutance_artifact_path=args.issue81_acutance_artifact,
        issue85_psd_artifact_path=args.issue85_psd_artifact,
        issue85_acutance_artifact_path=args.issue85_acutance_artifact,
        current_best_psd_artifact_path=args.current_best_psd_artifact,
        current_best_acutance_artifact_path=args.current_best_acutance_artifact,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
