from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_literal_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE34_LABEL = "issue34_intrinsic_full_reference"
ISSUE37_LABEL = "issue37_intrinsic_acutance_only_split"
ISSUE44_LABEL = "issue44_intrinsic_affine_registration"
ISSUE47_LABEL = "issue47_intrinsic_phase_retained_real"
ISSUE78_LABEL = "issue78_measured_oecf_negative"
SELECTED_SLICE_ID = "phase_retained_intrinsic_quality_loss_isolation"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-79 intrinsic literal next-slice record."
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
        default=Path("artifacts/intrinsic_literal_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_literal_next_slice.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relative_path(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


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
    psd_payload: dict[str, Any] | None,
    acutance_payload: dict[str, Any],
    profile_path: str,
    issue: int,
    pr: int,
    artifact_paths: list[str],
    note_paths: list[str],
) -> dict[str, Any]:
    acutance_profile = select_profile(acutance_payload, profile_path)
    acutance_overall = acutance_profile["overall"]
    summary = {
        "label": label,
        "issue": issue,
        "pr": pr,
        "profile_path": profile_path,
        "artifact_paths": artifact_paths,
        "note_paths": note_paths,
        "analysis_pipeline": acutance_profile["analysis_pipeline"],
        "curve_mae_mean": float(acutance_overall["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(acutance_overall["acutance_focus_preset_mae_mean"]),
        "overall_quality_loss_mae_mean": float(acutance_overall["overall_quality_loss_mae_mean"]),
    }
    if psd_payload is not None:
        psd_profile = select_profile(psd_payload, profile_path)
        psd_overall = psd_profile["overall"]
        summary["mtf_abs_signed_rel_mean"] = float(psd_overall["mtf_abs_signed_rel_mean"])
        summary["mtf_threshold_mae"] = {
            key: float(value) for key, value in psd_overall["mtf_threshold_mae"].items()
        }
    return summary


def delta_map(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["focus_preset_acutance_mae_mean"]
            - baseline["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            candidate["overall_quality_loss_mae_mean"]
            - baseline["overall_quality_loss_mae_mean"]
        ),
    }
    if "mtf_threshold_mae" in candidate and "mtf_threshold_mae" in baseline:
        payload["mtf_threshold_mae"] = {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        }
    return payload


def format_metric(value: float | None) -> str:
    return "-" if value is None else f"{value:.5f}"


def format_paths(paths: list[str]) -> str:
    return ", ".join(f"`{path}`" for path in paths)


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(repo_root: Path) -> dict[str, Any]:
    issue71_artifact = load_json(
        resolve_path(repo_root, Path("artifacts/literal_parity_next_family_benchmark.json"))
    )
    issue77_artifact = load_json(
        resolve_path(repo_root, Path("artifacts/imatest_parity_measured_oecf_benchmark.json"))
    )
    issue77_psd = load_json(
        resolve_path(repo_root, Path("artifacts/issue77_measured_oecf_psd_benchmark.json"))
    )
    issue77_acutance = load_json(
        resolve_path(repo_root, Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"))
    )
    issue46_psd = load_json(
        resolve_path(repo_root, Path("artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json"))
    )
    issue46_acutance = load_json(
        resolve_path(repo_root, Path("artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json"))
    )
    issue37_acutance = load_json(
        resolve_path(
            repo_root,
            Path("artifacts/imatest_parity_intrinsic_full_reference_acutance_side_only_benchmark.json"),
        )
    )

    records = {
        CURRENT_BEST_LABEL: summarize_profile(
            label=CURRENT_BEST_LABEL,
            psd_payload=issue77_psd,
            acutance_payload=issue77_acutance,
            profile_path=(
                "algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_"
                "acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_"
                "midclip0895_anchored_hf_psd_profile.json"
            ),
            issue=29,
            pr=30,
            artifact_paths=[
                "artifacts/issue77_measured_oecf_psd_benchmark.json",
                "artifacts/issue77_measured_oecf_acutance_benchmark.json",
            ],
            note_paths=["planning/workgraph.yaml"],
        ),
        ISSUE34_LABEL: summarize_profile(
            label=ISSUE34_LABEL,
            psd_payload=issue46_psd,
            acutance_payload=issue46_acutance,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json",
            issue=33,
            pr=34,
            artifact_paths=[
                "artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json",
                "artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json",
            ],
            note_paths=["docs/imatest_parity_intrinsic_full_reference_followup.md"],
        ),
        ISSUE37_LABEL: summarize_profile(
            label=ISSUE37_LABEL,
            psd_payload=None,
            acutance_payload=issue37_acutance,
            profile_path=(
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_acutance_side_only_profile.json"
            ),
            issue=37,
            pr=38,
            artifact_paths=[
                "artifacts/imatest_parity_intrinsic_full_reference_acutance_side_only_benchmark.json"
            ],
            note_paths=[
                "docs/imatest_parity_intrinsic_full_reference_acutance_side_only_followup.md"
            ],
        ),
        ISSUE44_LABEL: summarize_profile(
            label=ISSUE44_LABEL,
            psd_payload=issue46_psd,
            acutance_payload=issue46_acutance,
            profile_path="algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_ecc_affine_profile.json",
            issue=44,
            pr=45,
            artifact_paths=[
                "artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json",
                "artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json",
            ],
            note_paths=["docs/issue44_intrinsic_phase_ecc_affine_followup.md"],
        ),
        ISSUE47_LABEL: summarize_profile(
            label=ISSUE47_LABEL,
            psd_payload=issue46_psd,
            acutance_payload=issue46_acutance,
            profile_path=(
                "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json"
            ),
            issue=46,
            pr=47,
            artifact_paths=[
                "artifacts/issue46_intrinsic_phase_retention_psd_benchmark.json",
                "artifacts/issue46_intrinsic_phase_retention_acutance_benchmark.json",
            ],
            note_paths=["docs/issue46_intrinsic_phase_retention_followup.md"],
        ),
        ISSUE78_LABEL: summarize_profile(
            label=ISSUE78_LABEL,
            psd_payload=issue77_psd,
            acutance_payload=issue77_acutance,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json",
            issue=77,
            pr=78,
            artifact_paths=[
                "artifacts/issue77_measured_oecf_psd_benchmark.json",
                "artifacts/issue77_measured_oecf_acutance_benchmark.json",
                "artifacts/imatest_parity_measured_oecf_benchmark.json",
            ],
            note_paths=[
                "docs/imatest_parity_measured_oecf_followup.md",
                "docs/literal_parity_next_family.md",
            ],
        ),
    }

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "phase-retained intrinsic with downstream quality-loss isolation",
            "decision": "advance",
            "foundation_record": ISSUE47_LABEL,
            "preserve": [
                "phase_correlation registration",
                "radial_real_mean intrinsic transfer",
                "the stronger intrinsic curve / focus-preset Acutance signal from issue #46 / PR #47",
            ],
            "isolate": [
                "downstream quality-loss compensated MTF exposure to the intrinsic transfer",
                "any new fitted intrinsic transfer tables, benchmark outputs, or calibrations from golden/reference roots",
            ],
            "adoption_reasons": [
                "Issue #46 / PR #47 is the strongest checked-in intrinsic branch on curve MAE and focus-preset Acutance MAE, so the next slice should build on that upstream evidence rather than restart from weaker intrinsic variants.",
                "Issue #33 / PR #34 already showed that the intrinsic family\'s blocker is downstream Quality Loss, which makes quality-loss boundary isolation the narrowest unresolved technical point.",
                "Issue #37 proved that the existing `acutance_only` split is too broad: it protects Quality Loss only by giving back the intrinsic curve and Acutance gains, so the missing boundary is narrower than the current scope enum.",
                "Issue #77 / PR #78 already closed measured OECF as a bounded negative family, so reopening measured OECF or generic direct-method retunes would ignore the current source-backed ranking.",
            ],
            "comparison_basis": {
                "vs_current_best_pr30_branch": delta_map(
                    records[ISSUE47_LABEL], records[CURRENT_BEST_LABEL]
                ),
                "vs_issue34_intrinsic_full_reference": delta_map(
                    records[ISSUE47_LABEL], records[ISSUE34_LABEL]
                ),
                "vs_issue78_measured_oecf_negative": delta_map(
                    records[ISSUE47_LABEL], records[ISSUE78_LABEL]
                ),
            },
            "minimum_implementation_boundary": [
                "Add one new intrinsic scope or equivalent code path between `replace_all` and `acutance_only` in the parity benchmarks.",
                "Keep the issue-47 phase-retained intrinsic transfer active for PSD and Acutance evaluation.",
                "Route Quality Loss evaluation through the non-intrinsic compensated MTF path so the next issue isolates only the downstream Quality Loss exposure.",
                "Do not reopen measured OECF, affine registration, or generic direct-method retunes in that implementation issue.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The new scope leaves the phase-retained intrinsic curve / Acutance path intact enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` remain no worse than the older issue-34 intrinsic baseline.",
                "The same implementation materially reduces `overall_quality_loss_mae_mean` versus issue #46 / PR #47.",
                "All new fitted intrinsic artifacts remain under `algo/` or `artifacts/`, not under golden/reference roots.",
                "The implementation issue reruns focused PSD and acutance/quality-loss parity benchmarks for the selected intrinsic profile.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the phase-retained intrinsic profile plus the new scope.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair.",
                "Add focused tests around the new intrinsic scope so Quality Loss routing is isolated without regressing the PSD/Acutance path.",
            ],
        },
        {
            "slice_id": "replay_intrinsic_acutance_only_scope",
            "label": "replay the existing acutance_only intrinsic scope",
            "decision": "exclude",
            "foundation_record": ISSUE37_LABEL,
            "exclusion_reasons": [
                "Issue #37 already showed that `acutance_only` protects Quality Loss only by losing the intrinsic family\'s curve and Acutance benefit, so replaying it would not narrow the unresolved boundary.",
                "Because this scope is already checked in, rerunning it would be workflow churn rather than a new bounded implementation slice.",
            ],
        },
        {
            "slice_id": "revisit_affine_registration_variant",
            "label": "revisit the affine-registration intrinsic variant",
            "decision": "exclude",
            "foundation_record": ISSUE44_LABEL,
            "exclusion_reasons": [
                "The affine-registration intrinsic variant is worse than the original issue-34 intrinsic baseline on curve and focus-preset Acutance while still regressing Quality Loss.",
                "That makes registration refinement a dominated branch rather than the next rational bounded slice.",
            ],
        },
        {
            "slice_id": "reopen_measured_oecf_or_direct_retune",
            "label": "reopen measured OECF or generic direct-method retunes",
            "decision": "exclude",
            "foundation_record": ISSUE78_LABEL,
            "exclusion_reasons": [
                "Issue #71 selected measured OECF before intrinsic, and issue #77 / PR #78 then closed that family as a bounded negative result.",
                "Without a new source basis, reopening measured OECF or generic direct-method retunes would contradict both issue #71 and issue #79 scope constraints.",
            ],
        },
    ]

    payload = {
        "issue": 79,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": issue77_psd["dataset_root"],
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": (
            "Advance one bounded intrinsic/full-reference implementation slice: keep the "
            "stronger phase-retained intrinsic transfer, but isolate only downstream Quality "
            "Loss exposure instead of replaying older intrinsic variants or reopening measured OECF."
        ),
        "family_context": {
            "issue71_selector": {
                "artifact_path": "artifacts/literal_parity_next_family_benchmark.json",
                "selected_family_id": issue71_artifact["selected_family_id"],
                "selected_label": issue71_artifact["selected_label"],
                "selection_summary": issue71_artifact["selection_summary"],
            },
            "issue77_outcome": {
                "artifact_path": "artifacts/imatest_parity_measured_oecf_benchmark.json",
                "status": issue77_artifact["conclusion"]["status"],
                "next_step": issue77_artifact["conclusion"]["next_step"],
            },
        },
        "comparison_records": records,
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_literal_next_slice_benchmark.json",
            ],
            "rules": [
                "Do not write fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Keep issue-79 discovery outputs and the next intrinsic implementation artifacts under `algo/` and `artifacts/` only.",
                "Do not add or modify release-facing configs until an intrinsic slice beats the current tracked guards rather than only improving an internal sub-metric.",
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
    lines = [
        "# Intrinsic Literal Next Slice",
        "",
        "This note records the issue `#79` developer-discovery narrowing pass after the bounded-negative measured-OECF result in issue `#77` / PR `#78`.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{selected['slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        f"- Issue #71 context: `{payload['family_context']['issue71_selector']['selected_label']}` was selected ahead of intrinsic earlier, but issue #77 closed that family as `{payload['family_context']['issue77_outcome']['status']}`, so intrinsic is now the next source-backed route to narrow.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Key Readout |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    ordered_records = [
        CURRENT_BEST_LABEL,
        ISSUE34_LABEL,
        ISSUE37_LABEL,
        ISSUE44_LABEL,
        ISSUE47_LABEL,
        ISSUE78_LABEL,
    ]
    readouts = {
        CURRENT_BEST_LABEL: "Current release-facing best branch; strongest overall guardrail balance.",
        ISSUE34_LABEL: "First intrinsic baseline: better curve / Acutance, but Quality Loss regresses hard.",
        ISSUE37_LABEL: "Existing acutance_only split keeps Quality Loss but destroys the intrinsic gains.",
        ISSUE44_LABEL: "Affine registration is dominated by the simpler intrinsic baseline.",
        ISSUE47_LABEL: "Strongest intrinsic upstream record; Quality Loss is the remaining blocker.",
        ISSUE78_LABEL: "Measured OECF is already a bounded negative and should not be reopened here.",
    }
    for key in ordered_records:
        record = records[key]
        mtf = record.get("mtf_threshold_mae", {})
        lines.append(
            "| "
            f"{record['label']} | "
            f"{format_metric(record['curve_mae_mean'])} | "
            f"{format_metric(record['focus_preset_acutance_mae_mean'])} | "
            f"{format_metric(record['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(mtf.get('mtf20'))} | "
            f"{format_metric(mtf.get('mtf30'))} | "
            f"{format_metric(mtf.get('mtf50'))} | "
            f"{readouts[key]} |"
        )

    lines.extend(
        [
            "",
            "## Why This Slice",
            "",
        ]
    )
    for reason in selected["adoption_reasons"]:
        lines.append(f"- {reason}")

    lines.extend(
        [
            "",
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
    for criterion in selected["acceptance_criteria_for_next_issue"]:
        lines.append(f"- {criterion}")

    lines.extend(
        [
            "",
            "## Validation Plan For The Next Implementation Issue",
            "",
        ]
    )
    for step in selected["validation_plan_for_next_issue"]:
        lines.append(f"- {step}")

    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(repo_root)
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
