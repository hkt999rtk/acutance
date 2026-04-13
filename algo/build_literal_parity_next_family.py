from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


@dataclass(frozen=True)
class MetricEvidence:
    artifact_path: str
    profile_path: str


@dataclass(frozen=True)
class CandidateSpec:
    family_id: str
    label: str
    rank: int
    decision: str
    source_types: tuple[str, ...]
    source_summary: str
    rationale_for_adoption: tuple[str, ...]
    rationale_for_exclusion: tuple[str, ...]
    doc_paths: tuple[str, ...]
    benchmark_evidence: tuple[MetricEvidence, ...]
    fitted_profile_paths: tuple[str, ...]
    release_config_paths: tuple[str, ...]
    next_fitted_artifact_targets: tuple[str, ...]


CANDIDATE_SPECS = (
    CandidateSpec(
        family_id="literal_measured_oecf_on_sensor_comp",
        label="literal/measured_oecf_on_sensor_comp",
        rank=1,
        decision="advance",
        source_types=("official_imatest_doc", "peer_reviewed_paper"),
        source_summary=(
            "Imatest gamma/OECF guidance plus the dead-leaves literature both point to "
            "measured linearization as a missing family; the checked-in toe proxy is only "
            "an engineering stand-in for that missing measured OECF."
        ),
        rationale_for_adoption=(
            "The literal parity sensor-plus-toe proxy branch is the strongest checked-in "
            "literal route on curve and overall Quality Loss metrics.",
            "The standard inverse-OETF controls are already checked in and are materially worse, "
            "so the open path is a measured OECF family rather than another generic OETF swap.",
            "This family naturally supports strict separation between golden/reference data and "
            "new fitted OECF artifacts.",
        ),
        rationale_for_exclusion=(),
        doc_paths=(
            "docs/dead_leaves_black_box_research.md",
            "docs/imatest_parity_oecf_sensor_compensation_followup.md",
            "docs/imatest_parity_oetf_family_followup.md",
        ),
        benchmark_evidence=(
            MetricEvidence(
                artifact_path="artifacts/imatest_parity_oecf_sensor_compensation_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json",
            ),
            MetricEvidence(
                artifact_path="artifacts/imatest_parity_oetf_family_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json",
            ),
            MetricEvidence(
                artifact_path="artifacts/imatest_parity_oetf_family_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json",
            ),
        ),
        fitted_profile_paths=("algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json",),
        release_config_paths=(
            "release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_toe_profile.release.json",
        ),
        next_fitted_artifact_targets=(
            "algo/*.json",
            "artifacts/*.json",
            "release/deadleaf_13b10_release/config/*.json",
        ),
    ),
    CandidateSpec(
        family_id="literal_intrinsic_full_reference",
        label="literal/intrinsic_full_reference",
        rank=2,
        decision="defer",
        source_types=("official_imatest_doc", "peer_reviewed_paper"),
        source_summary=(
            "Imatest Random-Cross and the intrinsic dead-leaves literature make the "
            "full-reference path a real source-backed family rather than a free-form retune."
        ),
        rationale_for_adoption=(
            "Intrinsic/full-reference is still a legitimate missing family in the repo's "
            "source inventory.",
            "It materially improves curve fit and non-Phone/focus-preset Acutance on the "
            "checked-in experiments.",
        ),
        rationale_for_exclusion=(
            "The current intrinsic implementations still break downstream Quality Loss too "
            "severely to be the next literal route.",
            "The remaining work is more naturally a later family once the literal linearization "
            "boundary and fitted-artifact separation are fixed.",
        ),
        doc_paths=(
            "docs/dead_leaves_black_box_research.md",
            "docs/imatest_parity_intrinsic_full_reference_followup.md",
            "docs/issue46_intrinsic_phase_retention_followup.md",
        ),
        benchmark_evidence=(
            MetricEvidence(
                artifact_path="artifacts/imatest_parity_intrinsic_full_reference_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json",
            ),
            MetricEvidence(
                artifact_path="artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json",
            ),
        ),
        fitted_profile_paths=(
            "algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json",
            "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json",
        ),
        release_config_paths=(),
        next_fitted_artifact_targets=(
            "algo/*.json",
            "artifacts/*.json",
        ),
    ),
    CandidateSpec(
        family_id="literal_chart_sensor_compensation_only",
        label="literal/chart_sensor_compensation_only",
        rank=3,
        decision="defer",
        source_types=("official_imatest_doc", "peer_reviewed_paper"),
        source_summary=(
            "Imatest MTF-compensation guidance and the dead-leaves literature both support chart "
            "and sensor compensation as a missing literal-parity family."
        ),
        rationale_for_adoption=(
            "The compensation-only branch removes a meaningful portion of the literal high-frequency "
            "underfit and improves threshold readouts.",
        ),
        rationale_for_exclusion=(
            "Compensation alone regresses focus-preset Acutance and overall Quality Loss.",
            "The sensor-comp-only path is already superseded by the stronger literal "
            "sensor-plus-OECF-proxy branch.",
        ),
        doc_paths=(
            "docs/dead_leaves_black_box_research.md",
            "docs/imatest_parity_sensor_compensation_followup.md",
        ),
        benchmark_evidence=(
            MetricEvidence(
                artifact_path="artifacts/imatest_parity_sensor_compensation_benchmark.json",
                profile_path="algo/deadleaf_13b10_imatest_sensor_comp_profile.json",
            ),
        ),
        fitted_profile_paths=("algo/deadleaf_13b10_imatest_sensor_comp_profile.json",),
        release_config_paths=(
            "release/deadleaf_13b10_release/config/imatest_parity_sensor_comp_profile.release.json",
        ),
        next_fitted_artifact_targets=(
            "algo/*.json",
            "artifacts/*.json",
            "release/deadleaf_13b10_release/config/*.json",
        ),
    ),
)


EXCLUDED_RETUNE_LINES = (
    {
        "label": "generic standard inverse-OETF swaps",
        "status": "excluded",
        "reason": (
            "The checked-in `sRGB` and `Rec.709` literal branches are source-backed controls, "
            "but both are already worse than the toe proxy and therefore should not be reopened "
            "as the next family."
        ),
        "doc_paths": ("docs/imatest_parity_oetf_family_followup.md",),
    },
    {
        "label": "generic direct-method retunes without new source basis",
        "status": "excluded",
        "reason": (
            "Issue #71 explicitly forbids reopening exhausted generic direct-method retunes "
            "without a new source basis, and the issue-56 / issue-67 / issue-70 chain already "
            "closed those paths."
        ),
        "doc_paths": (
            "docs/issue56_empirical_frequency_scale_followup.md",
            "docs/issue67_readout_policy_followup.md",
            "docs/phone_preset_gap_followup.md",
        ),
    },
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-71 literal-parity next-family selector."
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
        default=Path("artifacts/literal_parity_next_family_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/literal_parity_next_family.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def resolve_output(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def extract_metrics(repo_root: Path, evidence: MetricEvidence) -> dict[str, Any]:
    payload = load_json(repo_root / evidence.artifact_path)
    for profile in payload["profiles"]:
        if profile["profile_path"] == evidence.profile_path:
            overall = profile["overall"]
            result = {
                "artifact_path": evidence.artifact_path,
                "profile_path": evidence.profile_path,
                "curve_mae_mean": float(overall["curve_mae_mean"]),
            }
            if "acutance_focus_preset_mae_mean" in overall:
                result["acutance_focus_preset_mae_mean"] = float(
                    overall["acutance_focus_preset_mae_mean"]
                )
                result["overall_quality_loss_mae_mean"] = float(
                    overall["overall_quality_loss_mae_mean"]
                )
            if "mtf_threshold_mae" in overall:
                result["mtf_threshold_mae"] = {
                    key: float(value) for key, value in overall["mtf_threshold_mae"].items()
                }
            return result
    raise ValueError(f"Profile {evidence.profile_path} not found in {evidence.artifact_path}")


def assert_storage_paths(spec: CandidateSpec) -> None:
    for path in (*spec.fitted_profile_paths, *spec.release_config_paths):
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_candidate_row(repo_root: Path, spec: CandidateSpec) -> dict[str, Any]:
    assert_storage_paths(spec)
    return {
        "family_id": spec.family_id,
        "label": spec.label,
        "rank": spec.rank,
        "decision": spec.decision,
        "source_types": list(spec.source_types),
        "source_summary": spec.source_summary,
        "rationale_for_adoption": list(spec.rationale_for_adoption),
        "rationale_for_exclusion": list(spec.rationale_for_exclusion),
        "doc_paths": list(spec.doc_paths),
        "benchmark_evidence": [
            extract_metrics(repo_root, evidence) for evidence in spec.benchmark_evidence
        ],
        "storage": {
            "fitted_profile_paths": list(spec.fitted_profile_paths),
            "release_config_paths": list(spec.release_config_paths),
            "next_fitted_artifact_targets": list(spec.next_fitted_artifact_targets),
        },
    }


def build_payload(repo_root: Path) -> dict[str, Any]:
    rows = [build_candidate_row(repo_root, spec) for spec in CANDIDATE_SPECS]
    selected = next(row for row in rows if row["decision"] == "advance")
    return {
        "issue": 71,
        "selected_family_id": selected["family_id"],
        "selected_label": selected["label"],
        "selection_summary": (
            "Advance the measured OECF-driven linearization family on top of the literal "
            "sensor-compensation route, keep intrinsic/full-reference as a later family, and "
            "do not reopen generic direct-method retunes or generic standard-OETF swaps."
        ),
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "rules": [
                "Do not write fitted profiles, calibrations, or benchmark outputs under the golden/reference roots.",
                "Keep new fitted profiles and calibrations in algo/ and measured benchmark outputs in artifacts/.",
                "Only add release-facing configs under release/deadleaf_13b10_release/config/ after a family is chosen for release-facing validation.",
            ],
        },
        "candidates": rows,
        "excluded_retune_lines": list(EXCLUDED_RETUNE_LINES),
    }


def format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Literal Parity Next Family",
        "",
        "This note records the issue `#71` selection of the next source-backed literal parity family.",
        "",
        "## Selected Route",
        "",
        f"- Selected family: `{payload['selected_label']}`",
        f"- Summary: {payload['selection_summary']}",
        "",
        "## Candidate Table",
        "",
        "| Rank | Family | Decision | Source Types | Curve MAE | Focus Acu MAE | Overall QL | Key Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["candidates"]:
        primary = row["benchmark_evidence"][0]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["rank"]),
                    row["label"],
                    row["decision"],
                    ", ".join(row["source_types"]),
                    format_metric(primary.get("curve_mae_mean")),
                    format_metric(primary.get("acutance_focus_preset_mae_mean")),
                    format_metric(primary.get("overall_quality_loss_mae_mean")),
                    row["rationale_for_adoption"][0]
                    if row["decision"] == "advance"
                    else row["rationale_for_exclusion"][0],
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Candidate Readout",
            "",
        ]
    )
    for row in payload["candidates"]:
        lines.extend(
            [
                f"### {row['label']}",
                "",
                f"- Decision: `{row['decision']}`",
                f"- Source types: {', '.join(f'`{kind}`' for kind in row['source_types'])}",
                f"- Source summary: {row['source_summary']}",
            ]
        )
        for reason in row["rationale_for_adoption"]:
            lines.append(f"- Adopt reason: {reason}")
        for reason in row["rationale_for_exclusion"]:
            lines.append(f"- Exclude/defer reason: {reason}")
        lines.append("- Evidence:")
        for evidence in row["benchmark_evidence"]:
            mtf = evidence.get("mtf_threshold_mae", {})
            lines.append(
                "  "
                + f"`{evidence['profile_path']}` from `{evidence['artifact_path']}`: "
                + f"`curve_mae_mean={format_metric(evidence.get('curve_mae_mean'))}`, "
                + f"`focus_acu_mae={format_metric(evidence.get('acutance_focus_preset_mae_mean'))}`, "
                + f"`overall_ql={format_metric(evidence.get('overall_quality_loss_mae_mean'))}`, "
                + f"`MTF20/30/50={format_metric(mtf.get('mtf20'))}/{format_metric(mtf.get('mtf30'))}/{format_metric(mtf.get('mtf50'))}`"
            )
        if row["storage"]["fitted_profile_paths"]:
            lines.append(
                "- Fitted profiles: "
                + ", ".join(f"`{path}`" for path in row["storage"]["fitted_profile_paths"])
            )
        if row["storage"]["release_config_paths"]:
            lines.append(
                "- Release-facing configs: "
                + ", ".join(f"`{path}`" for path in row["storage"]["release_config_paths"])
            )
        lines.append("")

    lines.extend(
        [
            "## Storage Separation",
            "",
            "- Golden/reference roots:",
            *[f"  - `{path}`" for path in payload["storage_policy"]["golden_reference_roots"]],
            "- Fitted artifact roots:",
            *[f"  - `{path}`" for path in payload["storage_policy"]["fitted_artifact_roots"]],
            "- Release-facing config roots:",
            *[f"  - `{path}`" for path in payload["storage_policy"]["release_config_roots"]],
            "- Rules:",
            *[f"  - {rule}" for rule in payload["storage_policy"]["rules"]],
            "",
            "## Excluded Retunes",
            "",
        ]
    )
    for row in payload["excluded_retune_lines"]:
        lines.append(f"- `{row['label']}`: {row['reason']}")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], *, repo_root: Path, output_json: Path, output_md: Path) -> None:
    json_path = resolve_output(output_json, repo_root)
    md_path = resolve_output(output_md, repo_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(repo_root)
    write_outputs(payload, repo_root=repo_root, output_json=args.output_json, output_md=args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
