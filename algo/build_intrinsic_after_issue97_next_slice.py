from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue97_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE93_LABEL = "issue93_downstream_matched_ori_only_candidate"
ISSUE97_LABEL = "issue97_reported_mtf_disconnect_candidate"
SELECTED_SLICE_ID = "issue97_topology_add_readout_only_sensor_aperture_compensation"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-99 intrinsic post-issue97 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue95-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue93_next_slice_benchmark.json"),
        help="Repo-relative issue-95 discovery artifact path.",
    )
    parser.add_argument(
        "--issue93-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_downstream_matched_ori_only_benchmark.json"),
        help="Repo-relative issue-93 summary artifact path.",
    )
    parser.add_argument(
        "--issue97-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_reported_mtf_disconnect_benchmark.json"),
        help="Repo-relative issue-97 summary artifact path.",
    )
    parser.add_argument(
        "--current-best-psd-artifact",
        type=Path,
        default=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
        help="Repo-relative current-best PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--issue93-psd-artifact",
        type=Path,
        default=Path("artifacts/issue93_intrinsic_phase_retained_downstream_matched_ori_only_psd_benchmark.json"),
        help="Repo-relative issue-93 PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--issue97-psd-artifact",
        type=Path,
        default=Path("artifacts/issue97_intrinsic_phase_retained_reported_mtf_disconnect_psd_benchmark.json"),
        help="Repo-relative issue-97 PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue97_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue97_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def is_close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)


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


def pipeline_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    candidate_pipeline = candidate["analysis_pipeline"]
    baseline_pipeline = baseline["analysis_pipeline"]
    keys = [
        "calibration_file",
        "high_frequency_guard_start_cpp",
        "intrinsic_full_reference_mode",
        "intrinsic_full_reference_scope",
        "intrinsic_full_reference_transfer_mode",
        "matched_ori_anchor_mode",
        "mtf_compensation_mode",
        "sensor_fill_factor",
        "texture_support_scale",
    ]
    return {
        key: {
            ISSUE97_LABEL: candidate_pipeline.get(key),
            CURRENT_BEST_LABEL: baseline_pipeline.get(key),
        }
        for key in keys
        if candidate_pipeline.get(key) != baseline_pipeline.get(key)
    }


def select_single_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profiles = payload["profiles"]
    if len(profiles) != 1:
        raise ValueError(f"Expected exactly one profile, found {len(profiles)}")
    return profiles[0]


def select_profile(payload: dict[str, Any], expected_profile_path: str) -> dict[str, Any]:
    for profile in payload["profiles"]:
        if profile["profile_path"] == expected_profile_path:
            return profile
    available = ", ".join(profile["profile_path"] for profile in payload["profiles"])
    raise ValueError(
        f"Profile {expected_profile_path!r} not found in artifact. Available: {available}"
    )


def band_signatures(profile: dict[str, Any]) -> dict[str, float]:
    return {
        band: float(summary["signed_rel_mean"])
        for band, summary in profile["overall"]["mtf_bands"].items()
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(
    repo_root: Path,
    *,
    issue95_artifact_path: Path,
    issue93_artifact_path: Path,
    issue97_artifact_path: Path,
    current_best_psd_artifact_path: Path,
    issue93_psd_artifact_path: Path,
    issue97_psd_artifact_path: Path,
) -> dict[str, Any]:
    issue95_artifact = load_json(resolve_path(repo_root, issue95_artifact_path))
    issue93_artifact = load_json(resolve_path(repo_root, issue93_artifact_path))
    issue97_artifact = load_json(resolve_path(repo_root, issue97_artifact_path))
    current_best_psd_artifact = load_json(resolve_path(repo_root, current_best_psd_artifact_path))
    issue93_psd_artifact = load_json(resolve_path(repo_root, issue93_psd_artifact_path))
    issue97_psd_artifact = load_json(resolve_path(repo_root, issue97_psd_artifact_path))

    comparison_records = {
        CURRENT_BEST_LABEL: issue97_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE93_LABEL: issue97_artifact["profiles"][ISSUE93_LABEL],
        ISSUE97_LABEL: issue97_artifact["profiles"][ISSUE97_LABEL],
    }
    current_best = comparison_records[CURRENT_BEST_LABEL]
    issue93 = comparison_records[ISSUE93_LABEL]
    issue97 = comparison_records[ISSUE97_LABEL]

    current_best_psd = select_profile(current_best_psd_artifact, current_best["profile_path"])
    issue93_psd = select_single_profile(issue93_psd_artifact)
    issue97_psd = select_single_profile(issue97_psd_artifact)

    issue97_vs_issue93 = delta_map(issue97, issue93)
    issue97_vs_current_best = delta_map(issue97, current_best)

    current_best_band_signatures = band_signatures(current_best_psd)
    issue93_band_signatures = band_signatures(issue93_psd)
    issue97_band_signatures = band_signatures(issue97_psd)

    residual_gap_evidence = {
        "issue97_preserves_issue93_core_record": {
            "curve_mae_mean": is_close(issue97["curve_mae_mean"], issue93["curve_mae_mean"]),
            "focus_preset_acutance_mae_mean": is_close(
                issue97["focus_preset_acutance_mae_mean"],
                issue93["focus_preset_acutance_mae_mean"],
            ),
            "overall_quality_loss_mae_mean": is_close(
                issue97["overall_quality_loss_mae_mean"],
                issue93["overall_quality_loss_mae_mean"],
            ),
            "delta": {
                "curve_mae_mean": issue97_vs_issue93["curve_mae_mean"],
                "focus_preset_acutance_mae_mean": issue97_vs_issue93[
                    "focus_preset_acutance_mae_mean"
                ],
                "overall_quality_loss_mae_mean": issue97_vs_issue93[
                    "overall_quality_loss_mae_mean"
                ],
            },
        },
        "issue97_threshold_tradeoff_vs_issue93": {
            "mtf20_improved": issue97["mtf_threshold_mae"]["mtf20"] < issue93["mtf_threshold_mae"]["mtf20"],
            "mtf30_regressed": issue97["mtf_threshold_mae"]["mtf30"] > issue93["mtf_threshold_mae"]["mtf30"],
            "mtf50_regressed": issue97["mtf_threshold_mae"]["mtf50"] > issue93["mtf_threshold_mae"]["mtf50"],
            "mtf_abs_signed_rel_regressed": issue97["mtf_abs_signed_rel_mean"]
            > issue93["mtf_abs_signed_rel_mean"],
            "delta": issue97_vs_issue93,
        },
        "issue97_band_signed_rel_direction": {
            band: {
                CURRENT_BEST_LABEL: current_best_band_signatures[band],
                ISSUE93_LABEL: issue93_band_signatures[band],
                ISSUE97_LABEL: issue97_band_signatures[band],
                "issue97_flips_negative_vs_issue93": issue93_band_signatures[band] > 0.0
                and issue97_band_signatures[band] < 0.0,
            }
            for band in ("low", "mid", "high", "top")
        },
        "issue97_still_trails_pr30": {
            "mtf20": issue97["mtf_threshold_mae"]["mtf20"]
            > current_best["mtf_threshold_mae"]["mtf20"],
            "mtf30": issue97["mtf_threshold_mae"]["mtf30"]
            > current_best["mtf_threshold_mae"]["mtf30"],
            "mtf50": issue97["mtf_threshold_mae"]["mtf50"]
            > current_best["mtf_threshold_mae"]["mtf50"],
            "mtf_abs_signed_rel_mean": issue97["mtf_abs_signed_rel_mean"]
            > current_best["mtf_abs_signed_rel_mean"],
            "delta": issue97_vs_current_best,
        },
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "keep the issue-97 topology but add readout-only sensor-aperture compensation",
            "decision": "advance",
            "technical_narrowing_point": (
                "issue97_showed_that_the_reported_mtf_disconnect_boundary_removed_the_wrong_"
                "directional_bias_only_partially_and_left_a_readout_amplitude_underestimate_"
                "that_now_points_at_the_compensation_boundary"
            ),
            "selected_summary": (
                "Keep issue #97's observed reported-MTF threshold branch and issue #93's "
                "downstream-only matched-ori Quality Loss branch unchanged, but restore "
                "sensor-aperture MTF compensation only on the reported-MTF/readout path "
                "before `compute_mtf_metrics(...)`. Use the PR #30 readout compensation "
                "settings (`sensor_aperture_sinc`, `sensor_fill_factor=1.5`) only on that "
                "branch, while leaving `compensated_mtf_for_acutance` and "
                "`quality_loss_compensated_mtf_for_acutance` on the existing issue-97 topology."
            ),
            "repo_evidence": [
                "Issue #97 preserves issue #93's `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` exactly, so the downstream-only matched-ori Quality Loss branch remains correctly isolated and does not need to be reopened.",
                "Issue #97 improves `mtf20` versus issue #93, but it regresses `mtf_abs_signed_rel_mean`, `mtf30`, and `mtf50`, which means the disconnect boundary moved the reported-MTF readout path in the right direction only for the lowest threshold and still left a residual readout-only failure mode.",
                "In the raw PSD output, issue #97 flips every signed-relative band negative (`low`, `mid`, `high`, `top`), while issue #93 was positive in `mid`, `high`, and `top`. That is a directional underestimation pattern on the observed readout curve rather than a Quality Loss branch interaction.",
                "The current PR #30 branch differs from issue #97 on several readout-adjacent knobs, but `mtf_compensation_mode='sensor_aperture_sinc'` plus `sensor_fill_factor=1.5` is the narrowest one that directly changes readout-curve amplitude before threshold extraction. `high_frequency_guard_start_cpp`, anchored calibration, and `texture_support_scale` are broader upstream or axis-scaling changes.",
                "Issue #97 still keeps `readout_smoothing_window=1` and `readout_interpolation='linear'`, matching PR #30 already, so the remaining failure mode is not in the final threshold smoother/interpolator pair.",
            ],
            "comparison_basis": {
                "pr96_selected_slice_id": issue95_artifact["selected_slice_id"],
                "pr94_issue93_vs_current_best_pr30": {
                    "delta": issue95_artifact["candidate_slices"][0]["comparison_basis"][
                        "issue93_vs_current_best_pr30"
                    ]["delta"],
                },
                "pr98_issue97_vs_issue93": {
                    "delta": issue97_vs_issue93,
                    "band_signed_rel_direction": residual_gap_evidence[
                        "issue97_band_signed_rel_direction"
                    ],
                },
                "pr98_issue97_vs_current_best_pr30": {
                    "delta": issue97_vs_current_best,
                },
            },
            "runtime_boundary_evidence": [
                {
                    "file_path": "algo/benchmark_parity_psd_mtf.py",
                    "line_range": "425-435, 686-730",
                    "observations": [
                        "The PSD driver builds `compensated_mtf` and `compensated_mtf_for_acutance` from the same profile-wide `mtf_compensation_mode` before any intrinsic or matched-ori branching happens.",
                        "`compute_mtf_metrics(...)` and `band_error_summary(...)` later consume only `readout_scaled_frequencies` plus `compensated_mtf`, so a dedicated readout-only compensation variable would directly isolate the remaining failure mode without touching the acutance branches.",
                        "Issue #97 already leaves `compensated_mtf` on the observed branch by not overwriting it with `intrinsic_mtf`; the next minimum slice is therefore to change the readout compensation boundary on that observed branch, not to reconnect intrinsic MTF again.",
                    ],
                },
                {
                    "file_path": "algo/benchmark_parity_acutance_quality_loss.py",
                    "line_range": "741-747, 866-972",
                    "observations": [
                        "The acutance/quality-loss driver already keeps `quality_loss_compensated_mtf_for_acutance` separate from the main acutance branch and anchors it later on the downstream-only matched-ori path.",
                        "Because issue #97 preserves the issue-93 topology here, a readout-only compensation graft in the PSD driver can leave `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` untouched.",
                        "This makes readout-only sensor-aperture compensation the smallest implementation that can target the remaining reported-MTF failure mode while preserving issue #97's curve/focus/Quality Loss record.",
                    ],
                },
            ],
            "minimum_implementation_boundary": [
                "Keep issue #97's `reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only` topology, intrinsic transfer, registration mode, and downstream-only matched-ori Quality Loss branch unchanged.",
                "Add one bounded scope or profile family that computes a readout-only `sensor_aperture_sinc` compensation path with `sensor_fill_factor=1.5` for the observed reported-MTF branch consumed by `compute_mtf_metrics(...)` and `band_error_summary(...)`.",
                "Leave `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` on the existing issue-97 branches; do not yet enable anchored calibration, `texture_support_scale`, or `high_frequency_guard_start_cpp`.",
            ],
            "explicitly_do_not_change": [
                "Do not reopen the issue-97 reported-MTF disconnect boundary or route thresholds back through the intrinsic reconnect path.",
                "Do not touch the downstream-only matched-ori Quality Loss branch, the main acutance branch, or release-facing PR30 coefficients/configs.",
                "Do not bundle anchored calibration, texture-support scaling, and high-frequency guard into the same implementation issue.",
                "Do not write new fitted outputs under `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, or `release/deadleaf_13b10_release/config/`.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The new bounded implementation keeps `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` no worse than issue #97.",
                "The same implementation improves `mtf_abs_signed_rel_mean`, `mtf30`, and `mtf50` versus issue #97 while keeping `mtf20` no worse than issue #97.",
                "The implementation keeps the downstream-only matched-ori Quality Loss branch isolated from the reported-MTF/readout path.",
                "All new fitted outputs remain under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on an issue-97-based profile that adds readout-only sensor-aperture compensation, then compare `mtf_abs_signed_rel_mean`, `mtf20`, `mtf30`, and `mtf50` against issue #97, issue #93, and PR #30.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same scope to confirm `curve_mae_mean`, `focus_preset_acutance_mae_mean`, and `overall_quality_loss_mae_mean` stay at or below issue #97.",
                "Add focused tests that prove only the reported-MTF/readout path receives the new compensation mode while `compensated_mtf_for_acutance` and `quality_loss_compensated_mtf_for_acutance` remain on the existing issue-97 branches.",
            ],
        },
        {
            "slice_id": "bundle_anchored_calibration_texture_scale_and_high_frequency_guard",
            "label": "bundle PR30's anchored calibration, texture-support scaling, and high-frequency guard into issue-97 now",
            "decision": "exclude",
            "exclusion_reasons": [
                "Those knobs live in a broader observable-stack family and would change both upstream PSD estimation and the frequency axis together.",
                "Issue #99 is a narrowing pass, so it should not jump from one failed readout boundary straight into a three-knob bundle before the single compensation boundary is isolated.",
            ],
        },
        {
            "slice_id": "reconnect_reported_mtf_to_intrinsic_branch_again",
            "label": "route reported-MTF thresholds back through the intrinsic reconnect path",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #95 / PR #96 already selected the disconnect boundary as the minimum post-issue93 slice, and PR #98 completed that experiment cleanly.",
                "Reconnecting thresholds to the intrinsic branch would reopen a path that issue #97 has already bounded, rather than narrowing the remaining failure mode.",
            ],
        },
        {
            "slice_id": "restart_broader_matched_ori_or_intrinsic_family_search",
            "label": "restart broader matched-ori, observable-stack, or intrinsic family search",
            "decision": "exclude",
            "exclusion_reasons": [
                "The remaining failure mode is already localized to the reported-MTF/readout path after issue #97; the repo evidence no longer supports reopening whole-family search.",
                "Issue #99 must leave engineering with one direct bounded implementation issue, not another unbounded family sweep.",
            ],
        },
    ]

    payload = {
        "issue": 99,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue95_summary_artifact": str(issue95_artifact_path),
            "issue95_selected_slice_id": issue95_artifact["selected_slice_id"],
            "issue93_summary_artifact": str(issue93_artifact_path),
            "issue93_conclusion_status": issue93_artifact["conclusion"]["status"],
            "issue97_summary_artifact": str(issue97_artifact_path),
            "issue97_conclusion_status": issue97_artifact["conclusion"]["status"],
        },
        "comparison_records": comparison_records,
        "residual_gap_evidence": residual_gap_evidence,
        "pipeline_delta_summary": pipeline_delta(issue97, current_best),
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue97_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep this issue's discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Do not touch release-facing configs until a later bounded implementation clears the current README-facing guardrails.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )
    records = payload["comparison_records"]
    residual = payload["residual_gap_evidence"]

    lines = [
        "# Intrinsic After Issue 97 Next Slice",
        "",
        "This note records the issue `#99` developer-discovery pass after issue `#97` / PR `#98` proved that disconnecting reported-MTF thresholds from the intrinsic reconnect preserves the issue-93 curve/focus/Quality Loss record but still leaves a residual reported-MTF/readout failure mode.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{payload['selected_slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        f"- Prior narrowing lineage: issue `#95` / PR `#96` selected `{payload['source_artifacts']['issue95_selected_slice_id']}`, and issue `#97` / PR `#98` completed that implementation cleanly enough to expose the next remaining boundary.",
        "- Remaining gap location: after issue #97, the downstream-only matched-ori Quality Loss win is already preserved and the reported-MTF branch is already disconnected from intrinsic reconnect. The next minimum slice is now the readout-only compensation boundary on the observed branch.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Reading |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    descriptions = {
        CURRENT_BEST_LABEL: "Current best PR30 branch.",
        ISSUE93_LABEL: "Issue-93 bounded positive baseline from PR #94.",
        ISSUE97_LABEL: "Issue-97 reported-MTF disconnect result from PR #98.",
    }
    for key in (CURRENT_BEST_LABEL, ISSUE93_LABEL, ISSUE97_LABEL):
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
            f"{descriptions[key]} |"
        )

    lines.extend(
        [
            "",
            "## Residual Gap Evidence",
            "",
            f"- Issue #97 preserves issue #93 `curve_mae_mean`: `{residual['issue97_preserves_issue93_core_record']['curve_mae_mean']}`",
            f"- Issue #97 preserves issue #93 `focus_preset_acutance_mae_mean`: `{residual['issue97_preserves_issue93_core_record']['focus_preset_acutance_mae_mean']}`",
            f"- Issue #97 preserves issue #93 `overall_quality_loss_mae_mean`: `{residual['issue97_preserves_issue93_core_record']['overall_quality_loss_mae_mean']}`",
            f"- Issue #97 improves issue #93 `mtf20`: `{residual['issue97_threshold_tradeoff_vs_issue93']['mtf20_improved']}`",
            f"- Issue #97 regresses issue #93 `mtf30`: `{residual['issue97_threshold_tradeoff_vs_issue93']['mtf30_regressed']}`",
            f"- Issue #97 regresses issue #93 `mtf50`: `{residual['issue97_threshold_tradeoff_vs_issue93']['mtf50_regressed']}`",
            f"- Issue #97 regresses issue #93 `mtf_abs_signed_rel_mean`: `{residual['issue97_threshold_tradeoff_vs_issue93']['mtf_abs_signed_rel_regressed']}`",
            "",
            "## Band Direction Evidence",
            "",
        ]
    )
    for band, values in residual["issue97_band_signed_rel_direction"].items():
        lines.append(
            f"- `{band}` signed-rel mean: pr30={values[CURRENT_BEST_LABEL]:.5f}, "
            f"issue93={values[ISSUE93_LABEL]:.5f}, issue97={values[ISSUE97_LABEL]:.5f}, "
            f"`issue97_flips_negative_vs_issue93={values['issue97_flips_negative_vs_issue93']}`"
        )

    lines.extend(
        [
            "",
            "## Pipeline Delta Between Issue 97 And PR30",
            "",
        ]
    )
    for key, values in payload["pipeline_delta_summary"].items():
        lines.append(
            f"- `{key}`: issue97={values[ISSUE97_LABEL]!r}, pr30={values[CURRENT_BEST_LABEL]!r}"
        )

    lines.extend(
        [
            "",
            "## Why The Next Slice Is Readout-Only Sensor-Aperture Compensation",
            "",
        ]
    )
    for reason in selected["repo_evidence"]:
        lines.append(f"- {reason}")

    lines.extend(
        [
            "",
            "## Runtime Boundary Evidence",
            "",
        ]
    )
    for item in selected["runtime_boundary_evidence"]:
        lines.append(f"### `{item['file_path']}` ({item['line_range']})")
        lines.append("")
        for observation in item["observations"]:
            lines.append(f"- {observation}")
        lines.append("")

    lines.extend(
        [
            "## Implementation Boundary",
            "",
        ]
    )
    for entry in selected["minimum_implementation_boundary"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Explicit Non-Changes",
            "",
        ]
    )
    for entry in selected["explicitly_do_not_change"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Excluded Routes",
            "",
        ]
    )
    for row in payload["candidate_slices"]:
        if row["decision"] != "exclude":
            continue
        lines.append(f"### `{row['slice_id']}`")
        lines.append("")
        lines.append(f"- Route: {row['label']}")
        for reason in row["exclusion_reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    lines.extend(
        [
            "## Acceptance For The Next Implementation Issue",
            "",
        ]
    )
    for entry in selected["acceptance_criteria_for_next_issue"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Validation Plan For The Next Implementation Issue",
            "",
        ]
    )
    for entry in selected["validation_plan_for_next_issue"]:
        lines.append(f"- {entry}")

    lines.extend(
        [
            "",
            "## Storage Separation",
            "",
            f"- Golden/reference roots: `{GOLDEN_REFERENCE_ROOTS[0]}`, `{GOLDEN_REFERENCE_ROOTS[1]}`",
            "- Fitted artifact roots: `algo/*.json`, `artifacts/*.json`",
            "- Release config roots: `release/deadleaf_13b10_release/config/*.json`",
        ]
    )
    for rule in payload["storage_policy"]["rules"]:
        lines.append(f"- {rule}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_payload(
        args.repo_root,
        issue95_artifact_path=args.issue95_artifact,
        issue93_artifact_path=args.issue93_artifact,
        issue97_artifact_path=args.issue97_artifact,
        current_best_psd_artifact_path=args.current_best_psd_artifact,
        issue93_psd_artifact_path=args.issue93_psd_artifact,
        issue97_psd_artifact_path=args.issue97_psd_artifact,
    )
    output_json = resolve_path(args.repo_root, args.output_json)
    output_md = resolve_path(args.repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
