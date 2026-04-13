from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUMMARY_KIND = "intrinsic_after_issue81_next_slice"
CURRENT_BEST_LABEL = "current_best_pr30_branch"
ISSUE34_LABEL = "issue34_intrinsic_full_reference"
ISSUE47_LABEL = "issue47_phase_retained_replace_all"
ISSUE81_LABEL = "issue81_quality_loss_isolation_candidate"
SELECTED_SLICE_ID = (
    "phase_retained_intrinsic_readout_reconnect_with_quality_loss_isolation"
)
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-83 intrinsic post-issue81 next-slice record."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue81-artifact",
        type=Path,
        default=Path("artifacts/intrinsic_phase_retained_quality_loss_isolation_benchmark.json"),
        help="Repo-relative issue-81 summary artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue81_next_slice_benchmark.json"),
        help="Repo-relative output path for the machine-readable artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/intrinsic_after_issue81_next_slice.md"),
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


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage_policy"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(repo_root: Path, *, issue81_artifact_path: Path) -> dict[str, Any]:
    issue81_artifact = load_json(resolve_path(repo_root, issue81_artifact_path))
    records = {
        CURRENT_BEST_LABEL: issue81_artifact["profiles"][CURRENT_BEST_LABEL],
        ISSUE34_LABEL: issue81_artifact["profiles"][ISSUE34_LABEL],
        ISSUE47_LABEL: issue81_artifact["profiles"][ISSUE47_LABEL],
        ISSUE81_LABEL: issue81_artifact["profiles"][ISSUE81_LABEL],
    }
    issue81_vs_current_best = issue81_artifact["comparisons"]["candidate_vs_current_best_pr30"]
    issue81_vs_issue34 = issue81_artifact["comparisons"]["candidate_vs_issue34"]
    issue81_vs_issue47 = issue81_artifact["comparisons"]["candidate_vs_issue47"]

    candidate_slices = [
        {
            "slice_id": SELECTED_SLICE_ID,
            "label": "reconnect phase-retained intrinsic to the reported-MTF/readout path while keeping downstream Quality Loss isolated",
            "decision": "advance",
            "technical_narrowing_point": (
                "issue81_quality_loss_isolation_kept_curve_and_focus_on_the_intrinsic_path_"
                "but_left_reported_mtf_readouts_on_compensated_mtf"
            ),
            "selected_summary": (
                "Keep the phase-retained intrinsic branch for both the acutance path and the "
                "reported-MTF/readout path, but leave the downstream Quality Loss path isolated "
                "on the non-intrinsic branch."
            ),
            "repo_evidence": [
                "Issue #81 preserved the issue-47 intrinsic curve / focus-preset Acutance gains exactly while materially improving overall Quality Loss, so the unresolved gap is no longer the upstream intrinsic transfer itself.",
                "The remaining large gap versus PR #30 is concentrated in `mtf_abs_signed_rel_mean` and the MTF-threshold readouts, which means the next slice should target the readout boundary rather than reopening measured OECF or generic direct-method retunes.",
                "Issue #81 worsens `mtf_abs_signed_rel_mean` from 0.13994 to 0.37917 versus issue #47, even though its curve / focus metrics stay identical. That asymmetry points to the PSD/readout path rather than the intrinsic curve path.",
                "The quality-loss benchmark already keeps a separate `quality_loss_*` branch under `quality_loss_isolation`, so reconnecting the reported-MTF/readout path can stay bounded instead of replaying the whole intrinsic family.",
            ],
            "comparison_basis": {
                "issue81_vs_current_best_pr30": issue81_vs_current_best,
                "issue81_vs_issue34": issue81_vs_issue34,
                "issue81_vs_issue47": issue81_vs_issue47,
            },
            "runtime_boundary_evidence": [
                {
                    "file_path": "algo/benchmark_parity_psd_mtf.py",
                    "line_range": "650-691",
                    "observations": [
                        "`compute_mtf_metrics(...)` derives the reported MTF thresholds from `compensated_mtf`.",
                        "`acutance_curve_from_mtf(...)` and `acutance_presets_from_mtf(...)` derive curve/preset outputs from `compensated_mtf_for_acutance` instead.",
                        "`resample_curve(...)` also publishes the PSD/readout comparison from `compensated_mtf`, so issue #81 can preserve curve/preset gains while leaving reported-MTF readouts on a different branch.",
                    ],
                },
                {
                    "file_path": "algo/benchmark_parity_acutance_quality_loss.py",
                    "line_range": "675-743, 920-936",
                    "observations": [
                        "`quality_loss_scaled_frequencies` and `quality_loss_compensated_mtf_for_acutance` are split out as a dedicated downstream Quality Loss branch.",
                        "Under `quality_loss_isolation`, the intrinsic transfer is applied to the main acutance path, but the quality-loss-specific branch is only replaced for `replace_all`.",
                        "That existing split means the next bounded implementation can reconnect the reported-MTF/readout path without forcing downstream Quality Loss back onto the intrinsic branch.",
                    ],
                },
            ],
            "minimum_implementation_boundary": [
                "Add one new intrinsic scope or equivalent code path that feeds the phase-retained intrinsic branch into `compensated_mtf` for reported-MTF/readout metrics.",
                "Keep the issue-81 `quality_loss_isolation` downstream routing so Quality Loss still evaluates on the non-intrinsic branch.",
                "Preserve `phase_correlation` registration and `radial_real_mean` transfer mode from issue #46 / PR #47 and issue #81 / PR #82.",
                "Do not reopen measured OECF, affine registration, or a generic intrinsic multi-family sweep in that implementation issue.",
            ],
            "explicitly_do_not_change": [
                "Do not change the matched-ori anchor family or the PR #30 release-facing direct-method profile in this slice.",
                "Do not move fitted profiles, transfer tables, or benchmark outputs under `20260318_deadleaf_13b10` or `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`.",
                "Do not promote any intrinsic config into release-facing config until the next bounded implementation actually beats the current guardrails.",
            ],
            "acceptance_criteria_for_next_issue": [
                "The next intrinsic scope preserves the issue-81 curve and focus-preset Acutance gains closely enough that `curve_mae_mean` and `focus_preset_acutance_mae_mean` are no worse than issue #81.",
                "The same implementation improves reported-MTF/readout metrics versus issue #81, with `mtf_abs_signed_rel_mean` reduced and the MTF-threshold errors moving materially toward the current PR #30 branch.",
                "The downstream `overall_quality_loss_mae_mean` does not regress versus issue #81.",
                "All new fitted intrinsic artifacts stay under `algo/` or `artifacts/`, not under golden/reference roots or release-facing config roots.",
            ],
            "validation_plan_for_next_issue": [
                "Run `python3 -m algo.benchmark_parity_psd_mtf ...` on the phase-retained intrinsic profile plus the new readout-reconnect scope.",
                "Run `python3 -m algo.benchmark_parity_acutance_quality_loss ...` on the same profile/scope pair to confirm Quality Loss remains isolated.",
                "Add focused tests around the split between `compensated_mtf`, `compensated_mtf_for_acutance`, and the quality-loss-specific branch.",
            ],
        },
        {
            "slice_id": "promote_issue81_as_is",
            "label": "promote issue-81 scope as-is",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #81 is a real positive bounded record, but its `overall_quality_loss_mae_mean` and reported-MTF/readout metrics are still far worse than the current PR #30 branch.",
                "Treating issue #81 as promotable without narrowing the remaining readout boundary would skip the exact unresolved technical gap this issue was created to isolate.",
            ],
        },
        {
            "slice_id": "reopen_measured_oecf_family",
            "label": "reopen measured OECF",
            "decision": "exclude",
            "exclusion_reasons": [
                "Measured OECF already closed as a bounded negative in issue #77 / PR #78, and issue #83 explicitly forbids reopening that family.",
                "The issue-81 evidence points to an intrinsic-side readout boundary, not to missing measured-OECF data or retuning.",
            ],
        },
        {
            "slice_id": "rerun_affine_registration_intrinsic",
            "label": "rerun affine-registration intrinsic variant",
            "decision": "exclude",
            "exclusion_reasons": [
                "Affine registration was already dominated by the simpler intrinsic baseline and is explicitly out of scope for issue #83.",
                "The post-issue81 gap is narrower than registration choice: the surviving mismatch is the split between readout and downstream Quality Loss branches.",
            ],
        },
        {
            "slice_id": "restart_unbounded_intrinsic_inventory",
            "label": "restart an unbounded intrinsic family search",
            "decision": "exclude",
            "exclusion_reasons": [
                "Issue #83 is a developer-discovery narrowing pass, not a new multi-family search.",
                "The repo already contains enough evidence to name one bounded implementation slice directly, so broad family churn would be workflow regress rather than progress.",
            ],
        },
    ]

    payload = {
        "issue": 83,
        "summary_kind": SUMMARY_KIND,
        "selected_slice_id": SELECTED_SLICE_ID,
        "selected_summary": candidate_slices[0]["selected_summary"],
        "source_artifacts": {
            "issue81_summary_artifact": str(issue81_artifact_path),
            "issue81_conclusion_status": issue81_artifact["conclusion"]["status"],
        },
        "comparison_records": records,
        "candidate_slices": candidate_slices,
        "storage_policy": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "fitted_artifact_roots": ["algo/*.json", "artifacts/*.json"],
            "release_config_roots": ["release/deadleaf_13b10_release/config/*.json"],
            "new_fitted_artifact_paths": [
                "artifacts/intrinsic_after_issue81_next_slice_benchmark.json",
            ],
            "rules": [
                "Keep this issue's discovery outputs under `docs/` and `artifacts/` only.",
                "Do not write new fitted intrinsic profiles, transfer tables, or benchmark outputs under the golden/reference roots.",
                "Do not touch release-facing configs until a later bounded intrinsic implementation actually clears the current readme-facing guardrails.",
            ],
        },
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    records = payload["comparison_records"]
    selected = next(
        row for row in payload["candidate_slices"] if row["slice_id"] == payload["selected_slice_id"]
    )
    lines = [
        "# Intrinsic After Issue 81 Next Slice",
        "",
        "This note records the issue `#83` developer-discovery pass after issue `#81` / PR `#82` proved that the intrinsic line can preserve the phase-retained curve / focus gains while shrinking the downstream Quality Loss regression.",
        "",
        "## Selected Slice",
        "",
        f"- Selected slice: `{selected['slice_id']}`",
        f"- Summary: {payload['selected_summary']}",
        "- Remaining gap location: the intrinsic branch now survives on the curve / acutance side, but the reported-MTF/readout path still diverges from that branch.",
        "",
        "## Comparison Table",
        "",
        "| Record | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel | Readout |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    readouts = {
        CURRENT_BEST_LABEL: "Current best branch; best overall Quality Loss / readout balance.",
        ISSUE34_LABEL: "First intrinsic baseline; curve and Acutance improve, Quality Loss regresses.",
        ISSUE47_LABEL: "Strongest intrinsic upstream record before issue #81; Quality Loss is the blocker.",
        ISSUE81_LABEL: "Issue #81 keeps the intrinsic upstream gains and reduces Quality Loss, but readout metrics still lag.",
    }
    for key in (CURRENT_BEST_LABEL, ISSUE34_LABEL, ISSUE47_LABEL, ISSUE81_LABEL):
        record = records[key]
        mtf = record["mtf_threshold_mae"]
        lines.append(
            "| "
            f"{record['label']} | "
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
            "## Why The Gap Still Remains After Issue 81",
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
    payload = build_payload(repo_root, issue81_artifact_path=args.issue81_artifact)
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    write_text(output_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text(output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
