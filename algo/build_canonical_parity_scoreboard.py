from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any


TREND_ARTIFACT_PRIORITY = (
    "artifacts/amodel_gray_texture_series_penalty_benchmark.json",
    "artifacts/amodel_gray_texture_benchmark.json",
    "artifacts/amodel_gain_hypothesis_benchmark.json",
    "artifacts/amodel_gain_trend_benchmark.json",
)

STATUS_DEFINITIONS = {
    "parity-valid": (
        "Still kept as a live parity candidate or retained release reference rather than only as "
        "a diagnostic probe."
    ),
    "diagnostic-only": (
        "Useful for explaining a residual or narrowing the next slice, but not kept as the "
        "current default or a release-safe replacement."
    ),
    "archived / exhausted": (
        "Closed bounded negative or legacy-only line; kept for historical comparison but not for "
        "further direct follow-up on the current surface."
    ),
}


@dataclass(frozen=True)
class ReleaseFamilySpec:
    family_id: str
    label: str
    profile_path: str
    status: str
    status_reason: str
    doc_paths: tuple[str, ...]


@dataclass(frozen=True)
class DirectMethodSpec:
    family_id: str
    label: str
    status: str
    status_reason: str
    doc_paths: tuple[str, ...]
    psd_artifact_path: str
    acutance_artifact_path: str
    primary_path_override: str | None = None


RELEASE_FAMILIES = (
    ReleaseFamilySpec(
        family_id="release_parity_fit",
        label="release/parity_fit",
        profile_path="release/deadleaf_13b10_release/config/parity_fit_profile.release.json",
        status="parity-valid",
        status_reason="Current release default and primary target profile.",
        doc_paths=("release/deadleaf_13b10_release/README.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_recommended",
        label="release/recommended",
        profile_path="release/deadleaf_13b10_release/config/recommended_profile.release.json",
        status="parity-valid",
        status_reason=(
            "Retained split-workaround parity reference; no longer primary, but still an active "
            "comparison line rather than a pure diagnostic control."
        ),
        doc_paths=(
            "release/deadleaf_13b10_release/README.md",
            "docs/parity_acutance_quality_loss_validation.md",
        ),
    ),
    ReleaseFamilySpec(
        family_id="release_experimental_shape",
        label="release/experimental_shape",
        profile_path="release/deadleaf_13b10_release/config/experimental_shape_profile.release.json",
        status="diagnostic-only",
        status_reason="Current experiment reference for trend mismatch, not a shipped default.",
        doc_paths=(
            "docs/amodel_gain_trend_experiment.md",
            "docs/amodel_gray_texture_series_penalty_followup.md",
        ),
    ),
    ReleaseFamilySpec(
        family_id="release_imatest_parity",
        label="release/imatest_parity",
        profile_path="release/deadleaf_13b10_release/config/imatest_parity_profile.release.json",
        status="diagnostic-only",
        status_reason="README marks this literal-gamma route as a reference-only hypothesis.",
        doc_paths=("release/deadleaf_13b10_release/README.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_imatest_parity_sensor_comp",
        label="release/imatest_parity_sensor_comp",
        profile_path="release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_profile.release.json",
        status="diagnostic-only",
        status_reason="README marks this literal-parity plus sensor-comp line as reference-only.",
        doc_paths=("release/deadleaf_13b10_release/README.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_imatest_parity_sensor_comp_toe",
        label="release/imatest_parity_sensor_comp_toe",
        profile_path="release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_toe_profile.release.json",
        status="diagnostic-only",
        status_reason="README marks this literal-parity plus sensor-comp plus toe line as reference-only.",
        doc_paths=("release/deadleaf_13b10_release/README.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gain_noise",
        label="release/parity_gain_noise",
        profile_path="release/deadleaf_13b10_release/config/parity_gain_noise_profile.release.json",
        status="diagnostic-only",
        status_reason="Gain-noise hypothesis trims delta error slightly but does not fix trend direction.",
        doc_paths=("docs/amodel_gain_hypothesis_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gain_shape",
        label="release/parity_gain_shape",
        profile_path="release/deadleaf_13b10_release/config/parity_gain_shape_profile.release.json",
        status="diagnostic-only",
        status_reason="Gain-shape hypothesis remains inconclusive and is not strong enough for promotion.",
        doc_paths=(
            "docs/amodel_gain_hypothesis_followup.md",
            "docs/amodel_gray_texture_followup.md",
        ),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gray_shape",
        label="release/parity_gray_shape",
        profile_path="release/deadleaf_13b10_release/config/parity_gray_shape_profile.release.json",
        status="diagnostic-only",
        status_reason="Gray-only factor isolate improves delta magnitude but not direction-match count.",
        doc_paths=("docs/amodel_gray_texture_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_texture_shape",
        label="release/parity_texture_shape",
        profile_path="release/deadleaf_13b10_release/config/parity_texture_shape_profile.release.json",
        status="diagnostic-only",
        status_reason="Texture-support-only isolate leaves trend direction unresolved and inflates series error.",
        doc_paths=("docs/amodel_gray_texture_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gray_texture_shape",
        label="release/parity_gray_texture_shape",
        profile_path="release/deadleaf_13b10_release/config/parity_gray_texture_shape_profile.release.json",
        status="diagnostic-only",
        status_reason="Best explanatory gray-plus-texture trend branch, but still experiment-only because series MAE is too high.",
        doc_paths=(
            "docs/amodel_gray_texture_followup.md",
            "docs/amodel_gray_texture_series_penalty_followup.md",
        ),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gray_texture_shape_freq110",
        label="release/parity_gray_texture_shape_freq110",
        profile_path="release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq110_profile.release.json",
        status="diagnostic-only",
        status_reason="Narrowed experiment-only gray-plus-texture variant; still not the preferred tradeoff.",
        doc_paths=("docs/amodel_gray_texture_series_penalty_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gray_texture_shape_freq105",
        label="release/parity_gray_texture_shape_freq105",
        profile_path="release/deadleaf_13b10_release/config/parity_gray_texture_shape_freq105_profile.release.json",
        status="diagnostic-only",
        status_reason="Current best gray-plus-texture compromise, but still experiment-only pending release-facing validation.",
        doc_paths=("docs/amodel_gray_texture_series_penalty_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_parity_gray_texture_shape_nofreq",
        label="release/parity_gray_texture_shape_nofreq",
        profile_path="release/deadleaf_13b10_release/config/parity_gray_texture_shape_nofreq_profile.release.json",
        status="diagnostic-only",
        status_reason="Useful narrowed control inside the gray-plus-texture family, not a promoted release path.",
        doc_paths=("docs/amodel_gray_texture_series_penalty_followup.md",),
    ),
    ReleaseFamilySpec(
        family_id="release_legacy_linear",
        label="release/legacy_linear",
        profile_path="release/deadleaf_13b10_release/config/legacy_linear_profile.release.json",
        status="archived / exhausted",
        status_reason="Legacy comparison baseline retained only for historical contrast.",
        doc_paths=("release/deadleaf_13b10_release/README.md",),
    ),
)


DIRECT_METHOD_FAMILIES = (
    DirectMethodSpec(
        family_id="direct_issue118_quality_loss_boundary",
        label="direct/issue118_quality_loss_boundary",
        status="parity-valid",
        status_reason=(
            "Current best canonical-target candidate from issue #118 / PR #119: it beats the "
            "PR #30 branch on overall Quality Loss while preserving the reported-MTF, curve, "
            "and focus-preset gains from the intrinsic issue-116 line. It remains candidate-only "
            "because README gates still miss on curve MAE and Small Print Acutance."
        ),
        doc_paths=(
            "docs/intrinsic_after_issue116_quality_loss_boundary.md",
            "docs/issue120_current_best_readme_gate_summary.md",
        ),
        psd_artifact_path="artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json",
        acutance_artifact_path=(
            "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json"
        ),
    ),
    DirectMethodSpec(
        family_id="direct_issue29_anchored_hf_psd",
        label="direct/issue29_anchored_hf_psd",
        status="parity-valid",
        status_reason=(
            "Small but real source-backed lower-layer improvement that stayed downstream-safe "
            "enough to keep as a tracked candidate."
        ),
        doc_paths=("docs/issue29_anchored_high_frequency_psd_followup.md",),
        psd_artifact_path="artifacts/issue29_anchored_high_frequency_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue29_anchored_high_frequency_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue52_roi_reference",
        label="direct/issue52_roi_reference",
        status="diagnostic-only",
        status_reason="Clear lower-layer win, but Quality Loss regressed too much for adoption.",
        doc_paths=("docs/issue52_direct_roi_reference_followup.md",),
        psd_artifact_path="artifacts/issue52_roi_reference_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue52_roi_reference_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue54_observable_bins",
        label="direct/issue54_observable_bins",
        status="archived / exhausted",
        status_reason="Closed frequency-bin branch; static inferred bins remained the better default on this dataset.",
        doc_paths=("docs/issue54_observable_frequency_bins_followup.md",),
        psd_artifact_path="artifacts/issue54_observable_frequency_bins_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue54_observable_frequency_bins_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue56_empirical_frequency_scale",
        label="direct/issue56_empirical_frequency_scale",
        status="archived / exhausted",
        status_reason="Closed empirical frequency-scale line; threshold-only gain did not transfer to the full parity objective.",
        doc_paths=("docs/issue56_empirical_frequency_scale_followup.md",),
        psd_artifact_path="artifacts/issue56_empirical_frequency_scale_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue56_empirical_frequency_scale_acutance_benchmark.json",
        primary_path_override=(
            "algo/"
            "deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_"
            "curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_"
            "psd_roi_reference_only_freqscale_1095_profile.json"
        ),
    ),
    DirectMethodSpec(
        family_id="direct_issue58_chart_sensor_comp",
        label="direct/issue58_chart_sensor_comp",
        status="diagnostic-only",
        status_reason="Healthier than the older chart/sensor branch, but still not strong enough to replace the default line.",
        doc_paths=("docs/issue58_chart_sensor_compensation_followup.md",),
        psd_artifact_path="artifacts/issue58_chart_sensor_compensation_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue58_chart_sensor_compensation_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue61_isp_family",
        label="direct/issue61_isp_family",
        status="diagnostic-only",
        status_reason="Useful source-backed negative showing the remaining gap is not solved by the bounded ISP proxy alone.",
        doc_paths=("docs/issue61_isp_family_followup.md",),
        psd_artifact_path="artifacts/issue61_isp_family_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue61_isp_family_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue63_empirical_linearization",
        label="direct/issue63_empirical_linearization",
        status="diagnostic-only",
        status_reason="Important mixed branch: Acutance improved sharply, but PSD and Quality Loss stayed too weak for promotion.",
        doc_paths=("docs/issue63_empirical_linearization_followup.md",),
        psd_artifact_path="artifacts/issue63_empirical_linearization_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue63_empirical_linearization_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue65_chart_prior_inverse_linearization",
        label="direct/issue65_chart_prior_inverse_linearization",
        status="archived / exhausted",
        status_reason="Explicit bounded negative refinement of the issue-63 branch.",
        doc_paths=("docs/issue65_chart_prior_inverse_linearization_followup.md",),
        psd_artifact_path="artifacts/issue65_chart_prior_inverse_linearization_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue65_chart_prior_inverse_linearization_acutance_benchmark.json",
    ),
    DirectMethodSpec(
        family_id="direct_issue67_readout_policy",
        label="direct/issue67_readout_policy",
        status="archived / exhausted",
        status_reason="Explicitly exhausted readout-policy family after the bounded negative re-check.",
        doc_paths=("docs/issue67_readout_policy_followup.md",),
        psd_artifact_path="artifacts/issue67_readout_policy_psd_benchmark.json",
        acutance_artifact_path="artifacts/issue67_readout_policy_acutance_benchmark.json",
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the canonical parity scoreboard from tracked artifacts."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/canonical_parity_scoreboard.json"),
        help="Repo-relative output path for the machine-readable scoreboard.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/canonical_parity_scoreboard.md"),
        help="Repo-relative output path for the Markdown scoreboard.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def iter_trend_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "profiles" in payload:
        return list(payload["profiles"])
    entries: list[dict[str, Any]] = []
    baseline = payload.get("baseline")
    if isinstance(baseline, dict):
        entries.append(baseline)
    hypotheses = payload.get("hypotheses")
    if isinstance(hypotheses, list):
        entries.extend(entry for entry in hypotheses if isinstance(entry, dict))
    return entries


def build_trend_index(repo_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for artifact_path in TREND_ARTIFACT_PRIORITY:
        payload = load_json(repo_root / artifact_path)
        for entry in iter_trend_entries(payload):
            profile_name = Path(entry["profile_path"]).name
            if profile_name in index:
                continue
            index[profile_name] = {
                "artifact_path": artifact_path,
                "profile_path": entry["profile_path"],
                "summary": entry["summary"],
            }
    return index


def build_trend_metrics(
    trend_index: dict[str, dict[str, Any]],
    profile_name: str,
) -> tuple[dict[str, Any], list[str]]:
    trend_entry = trend_index.get(profile_name)
    if trend_entry is None:
        return (
            {
                "trend_direction_match_rate": None,
                "trend_direction_match_count": None,
                "trend_direction_group_count": None,
                "gain_trend_series_shape_error": None,
                "gain_trend_delta_mae_mean": None,
            },
            [],
        )

    summary = trend_entry["summary"]
    match_count = int(summary["focus_preset_direction_match_count"])
    group_count = int(summary["focus_preset_direction_group_count"])
    match_rate = None
    if group_count:
        match_rate = match_count / group_count
    return (
        {
            "trend_direction_match_rate": match_rate,
            "trend_direction_match_count": match_count,
            "trend_direction_group_count": group_count,
            "gain_trend_series_shape_error": float(summary["focus_preset_series_mae_mean"]),
            "gain_trend_delta_mae_mean": float(summary["focus_preset_gain_delta_mae_mean"]),
        },
        [trend_entry["artifact_path"]],
    )


def build_release_row(
    spec: ReleaseFamilySpec,
    repo_root: Path,
    trend_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    profile_name = Path(spec.profile_path).name
    trend_metrics, trend_artifacts = build_trend_metrics(trend_index, profile_name)
    profile_path = repo_root / spec.profile_path
    return {
        "family_id": spec.family_id,
        "label": spec.label,
        "family_type": "release_profile",
        "status": spec.status,
        "status_reason": spec.status_reason,
        "trend_coverage": any(
            trend_metrics[key] is not None
            for key in (
                "trend_direction_match_rate",
                "gain_trend_series_shape_error",
            )
        ),
        "dead_leaves_coverage": False,
        **trend_metrics,
        "curve_mae_mean": None,
        "focus_preset_acutance_mae_mean": None,
        "overall_quality_loss_mae_mean": None,
        "mtf_threshold_mae": {
            "mtf20": None,
            "mtf30": None,
            "mtf50": None,
        },
        "acutance_preset_mae": {
            '5.5" Phone Display Acutance': None,
            "Computer Monitor Acutance": None,
            "UHDTV Display Acutance": None,
            "Small Print Acutance": None,
            "Large Print Acutance": None,
        },
        "quality_loss_preset_mae": {},
        "sources": {
            "primary_path": relative_path(profile_path, repo_root),
            "doc_paths": list(spec.doc_paths),
            "artifact_paths": trend_artifacts,
        },
    }


def build_direct_method_row(spec: DirectMethodSpec, repo_root: Path) -> dict[str, Any]:
    psd_payload = load_json(repo_root / spec.psd_artifact_path)
    acutance_payload = load_json(repo_root / spec.acutance_artifact_path)
    psd_profile = psd_payload["profiles"][-1]
    acutance_profile = acutance_payload["profiles"][-1]
    profile_path = normalize_direct_method_primary_path(
        repo_root=repo_root,
        raw_profile_path=str(acutance_profile["profile_path"]),
        override=spec.primary_path_override,
        doc_paths=spec.doc_paths,
    )
    return {
        "family_id": spec.family_id,
        "label": spec.label,
        "family_type": "direct_method_branch",
        "status": spec.status,
        "status_reason": spec.status_reason,
        "trend_coverage": False,
        "dead_leaves_coverage": True,
        "trend_direction_match_rate": None,
        "trend_direction_match_count": None,
        "trend_direction_group_count": None,
        "gain_trend_series_shape_error": None,
        "gain_trend_delta_mae_mean": None,
        "curve_mae_mean": float(acutance_profile["overall"]["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            acutance_profile["overall"]["acutance_focus_preset_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            acutance_profile["overall"]["overall_quality_loss_mae_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(value)
            for key, value in psd_profile["overall"]["mtf_threshold_mae"].items()
        },
        "acutance_preset_mae": {
            key: float(value)
            for key, value in acutance_profile["overall"]["acutance_preset_mae"].items()
        },
        "quality_loss_preset_mae": {
            key: float(value)
            for key, value in acutance_profile["overall"]["quality_loss_preset_mae"].items()
        },
        "sources": {
            "primary_path": profile_path,
            "doc_paths": list(spec.doc_paths),
            "artifact_paths": [
                spec.psd_artifact_path,
                spec.acutance_artifact_path,
            ],
        },
}


def normalize_direct_method_primary_path(
    *,
    repo_root: Path,
    raw_profile_path: str,
    override: str | None,
    doc_paths: tuple[str, ...],
) -> str:
    if override is not None:
        return override

    candidate = Path(raw_profile_path)
    if candidate.is_absolute():
        try:
            return str(candidate.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            pass
    else:
        repo_candidate = repo_root / candidate
        if repo_candidate.exists():
            return relative_path(repo_candidate, repo_root)

    # Historical artifacts sometimes only preserve temp paths. When that happens,
    # keep the canonical scoreboard repo-local by falling back to the closest
    # tracked provenance record instead of leaking an ephemeral filesystem path.
    return doc_paths[0]


def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    trend_rate = row["trend_direction_match_rate"]
    trend_error = row["gain_trend_series_shape_error"]
    curve_mae = row["curve_mae_mean"]
    focus_mae = row["focus_preset_acutance_mae_mean"]
    return (
        0 if trend_rate is not None else 1,
        -(trend_rate if trend_rate is not None else -1.0),
        trend_error if trend_error is not None else math.inf,
        curve_mae if curve_mae is not None else math.inf,
        focus_mae if focus_mae is not None else math.inf,
        row["label"],
    )


def build_scoreboard(repo_root: Path) -> dict[str, Any]:
    trend_index = build_trend_index(repo_root)
    rows = [
        *(build_release_row(spec, repo_root, trend_index) for spec in RELEASE_FAMILIES),
        *(build_direct_method_row(spec, repo_root) for spec in DIRECT_METHOD_FAMILIES),
    ]
    ordered_rows = sorted(rows, key=sort_key)
    for rank, row in enumerate(ordered_rows, start=1):
        row["rank"] = rank
    return {
        "scoreboard_version": 1,
        "ranking_policy": {
            "primary": "trend_direction_match_rate desc",
            "trend_tiebreaker": "gain_trend_series_shape_error asc",
            "secondary": "curve_mae_mean asc",
            "tertiary": "focus_preset_acutance_mae_mean asc",
            "missing_value_policy": (
                "Rows without tracked trend coverage sort after rows with trend coverage. "
                "Rows without tracked dead-leaves parity coverage keep null parity fields."
            ),
        },
        "status_definitions": STATUS_DEFINITIONS,
        "rows": ordered_rows,
    }


def format_value(value: float | None, *, digits: int = 5) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def format_rate(row: dict[str, Any]) -> str:
    count = row["trend_direction_match_count"]
    total = row["trend_direction_group_count"]
    rate = row["trend_direction_match_rate"]
    if count is None or total is None or rate is None:
        return "-"
    return f"{count}/{total} ({rate:.3f})"


def format_source(row: dict[str, Any]) -> str:
    artifact_paths = row["sources"]["artifact_paths"]
    if not artifact_paths:
        return row["sources"]["primary_path"]
    artifact_names = ", ".join(Path(path).name for path in artifact_paths)
    return f"{row['sources']['primary_path']} [{artifact_names}]"


def render_markdown(scoreboard: dict[str, Any]) -> str:
    rows = scoreboard["rows"]
    lines = [
        "# Canonical Parity Scoreboard",
        "",
        "This scoreboard is the repo-local decision surface requested by issue `#69`.",
        "",
        "Ranking policy:",
        "",
        "1. `trend direction match rate` descending",
        "2. `gain-trend series shape error` ascending as the trend tie-breaker",
        "3. `curve_mae_mean` ascending",
        "4. `focus preset acutance mae mean` ascending",
        "",
        "Coverage note:",
        "",
        "- release-profile rows carry tracked A-model trend metrics when the repo has a checked-in gain-trend benchmark for that exact release config.",
        "- direct-method rows carry tracked dead-leaves parity metrics from the issue artifacts; these rows currently have no exact checked-in A-model trend benchmark on the same profile path, so trend fields remain `-`.",
        "",
        "| Rank | Family | Type | Status | Trend match | Series err | Curve MAE | Focus Acu MAE | Phone A | Monitor A | UHDTV A | Small Print A | Large Print A | MTF20 | MTF30 | MTF50 | Overall QL | Source |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        presets = row["acutance_preset_mae"]
        mtf = row["mtf_threshold_mae"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["rank"]),
                    row["label"],
                    row["family_type"],
                    row["status"],
                    format_rate(row),
                    format_value(row["gain_trend_series_shape_error"]),
                    format_value(row["curve_mae_mean"]),
                    format_value(row["focus_preset_acutance_mae_mean"]),
                    format_value(presets['5.5" Phone Display Acutance']),
                    format_value(presets["Computer Monitor Acutance"]),
                    format_value(presets["UHDTV Display Acutance"]),
                    format_value(presets["Small Print Acutance"]),
                    format_value(presets["Large Print Acutance"]),
                    format_value(mtf["mtf20"]),
                    format_value(mtf["mtf30"]),
                    format_value(mtf["mtf50"]),
                    format_value(row["overall_quality_loss_mae_mean"]),
                    format_source(row),
                ]
            )
            + " |"
        )

    top_trend_row = next((row for row in rows if row["trend_coverage"]), None)
    top_direct_row = next((row for row in rows if row["family_type"] == "direct_method_branch"), None)
    top_parity_valid_direct_row = next(
        (
            row
            for row in rows
            if row["family_type"] == "direct_method_branch" and row["status"] == "parity-valid"
        ),
        None,
    )
    exhausted_rows = [row["label"] for row in rows if row["status"] == "archived / exhausted"]

    lines.extend(
        [
            "",
            "## Current Readout",
            "",
            (
                f"- Top tracked trend row: `{top_trend_row['label']}` with "
                f"`{format_rate(top_trend_row)}` and series error "
                f"`{format_value(top_trend_row['gain_trend_series_shape_error'])}`; "
                f"status = `{top_trend_row['status']}`."
                if top_trend_row is not None
                else "- No tracked trend rows were found."
            ),
            (
                f"- Top tracked direct-method row by the fixed sort: `{top_direct_row['label']}` with "
                f"`curve_mae_mean = {format_value(top_direct_row['curve_mae_mean'])}` and "
                f"`overall_quality_loss_mae_mean = {format_value(top_direct_row['overall_quality_loss_mae_mean'])}`; "
                f"status = `{top_direct_row['status']}`."
                if top_direct_row is not None
                else "- No tracked direct-method rows were found."
            ),
            (
                f"- Best still-parity-valid direct-method row: `{top_parity_valid_direct_row['label']}` with "
                f"`curve_mae_mean = {format_value(top_parity_valid_direct_row['curve_mae_mean'])}` and "
                f"`overall_quality_loss_mae_mean = {format_value(top_parity_valid_direct_row['overall_quality_loss_mae_mean'])}`."
                if top_parity_valid_direct_row is not None
                else "- No parity-valid direct-method rows are currently tracked."
            ),
            (
                "- Explicit archived / exhausted lines in the current scoreboard: "
                + ", ".join(f"`{label}`" for label in exhausted_rows)
                + "."
                if exhausted_rows
                else "- No archived / exhausted lines are currently marked."
            ),
            "",
            "The machine-readable companion artifact at "
            "`artifacts/canonical_parity_scoreboard.json` keeps the full status reasons, "
            "per-preset values, and provenance paths for later issues to cite directly.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    scoreboard: dict[str, Any],
    *,
    repo_root: Path,
    output_json: Path,
    output_md: Path,
) -> None:
    json_path = output_json if output_json.is_absolute() else repo_root / output_json
    md_path = output_md if output_md.is_absolute() else repo_root / output_md
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(scoreboard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(scoreboard), encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    scoreboard = build_scoreboard(repo_root)
    write_outputs(
        scoreboard,
        repo_root=repo_root,
        output_json=args.output_json,
        output_md=args.output_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
