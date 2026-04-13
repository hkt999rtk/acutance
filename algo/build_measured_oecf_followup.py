from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_BRANCH_LABEL = "current_best_pr30_branch"
TOE_PROXY_LABEL = "literal_toe_proxy_baseline"
MEASURED_OECF_LABEL = "measured_oecf_candidate"
SRGB_LABEL = "inverse_srgb_control"
REC709_LABEL = "inverse_rec709_control"
SUMMARY_KIND = "imatest_parity_measured_oecf_followup"
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the issue-77 measured-OECF follow-up summary."
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
        default=Path("artifacts/issue77_measured_oecf_psd_benchmark.json"),
        help="Repo-relative PSD benchmark artifact path.",
    )
    parser.add_argument(
        "--acutance-artifact",
        type=Path,
        default=Path("artifacts/issue77_measured_oecf_acutance_benchmark.json"),
        help="Repo-relative acutance/quality-loss benchmark artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/imatest_parity_measured_oecf_benchmark.json"),
        help="Repo-relative output path for the machine-readable issue artifact.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/imatest_parity_measured_oecf_followup.md"),
        help="Repo-relative output path for the Markdown note.",
    )
    return parser


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_output(path: Path, repo_root: Path) -> Path:
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
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in ("mtf20", "mtf30", "mtf50")
        },
    }


def promotion_passes(comparison: dict[str, Any]) -> bool:
    return all(
        (
            comparison["curve_mae_improved"],
            comparison["focus_preset_acutance_improved"],
            comparison["overall_quality_loss_improved"],
            comparison["mtf_thresholds_non_worse"],
        )
    )


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def format_delta(value: float) -> str:
    return f"{value:+.5f}"


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["storage"]["new_fitted_artifact_paths"]:
        for root in GOLDEN_REFERENCE_ROOTS:
            if path.startswith(root):
                raise ValueError(f"Path {path} leaks into golden/reference root {root}")


def build_payload(repo_root: Path, *, psd_artifact_path: Path, acutance_artifact_path: Path) -> dict[str, Any]:
    psd_artifact = resolve_output(psd_artifact_path, repo_root)
    acutance_artifact = resolve_output(acutance_artifact_path, repo_root)
    psd_payload = load_json(psd_artifact)
    acutance_payload = load_json(acutance_artifact)

    profiles = {
        CURRENT_BEST_BRANCH_LABEL: summarize_profile(
            label=CURRENT_BEST_BRANCH_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_reference_anchor_acutance_only_curve_preset_qualityfit_allpreset_sextic_curve_midclip0895_anchored_hf_psd_profile.json",
        ),
        TOE_PROXY_LABEL: summarize_profile(
            label=TOE_PROXY_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_profile.json",
        ),
        MEASURED_OECF_LABEL: summarize_profile(
            label=MEASURED_OECF_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json",
        ),
        SRGB_LABEL: summarize_profile(
            label=SRGB_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_srgb_profile.json",
        ),
        REC709_LABEL: summarize_profile(
            label=REC709_LABEL,
            psd_payload=psd_payload,
            acutance_payload=acutance_payload,
            profile_path="algo/deadleaf_13b10_imatest_sensor_comp_rec709_profile.json",
        ),
    }

    measured = profiles[MEASURED_OECF_LABEL]
    toe = profiles[TOE_PROXY_LABEL]
    current_best = profiles[CURRENT_BEST_BRANCH_LABEL]
    srgb = profiles[SRGB_LABEL]
    rec709 = profiles[REC709_LABEL]

    payload = {
        "issue": 77,
        "summary_kind": SUMMARY_KIND,
        "dataset_root": psd_payload["dataset_root"],
        "family_boundary_change": {
            "source_basis": [
                "docs/dead_leaves_black_box_research.md",
                "docs/imatest_parity_matched_ori_oecf_proxy_followup.md",
                "docs/literal_parity_next_family.md",
            ],
            "toe_proxy_baseline": toe["profile_path"],
            "measured_oecf_candidate": measured["profile_path"],
            "change": (
                "Keep the literal sensor-compensation plus toe linearization route intact, "
                "then add the matched-ORI quantile transfer as the smallest measured-OECF-driven "
                "family boundary that the current repo can derive without chart-patch OECF data."
            ),
            "note": (
                "The new candidate is still a fitted artifact rather than a golden/reference asset. "
                "It isolates the measured-OECF family boundary from the earlier toe-only stand-in."
            ),
        },
        "profiles": profiles,
        "comparisons": {
            "measured_oecf_vs_toe_proxy": {
                "delta": delta_map(measured, toe),
                "curve_mae_improved": measured["curve_mae_mean"] < toe["curve_mae_mean"],
                "focus_preset_acutance_improved": (
                    measured["focus_preset_acutance_mae_mean"]
                    < toe["focus_preset_acutance_mae_mean"]
                ),
                "overall_quality_loss_improved": (
                    measured["overall_quality_loss_mae_mean"]
                    < toe["overall_quality_loss_mae_mean"]
                ),
                "mtf_thresholds_non_worse": all(
                    measured["mtf_threshold_mae"][key] <= toe["mtf_threshold_mae"][key]
                    for key in ("mtf20", "mtf30", "mtf50")
                ),
            },
            "measured_oecf_vs_current_best_pr30": {
                "delta": delta_map(measured, current_best),
            },
            "measured_oecf_vs_inverse_oetf_controls": {
                "srgb": delta_map(measured, srgb),
                "rec709": delta_map(measured, rec709),
                "beats_srgb_on_curve_and_quality_loss": (
                    measured["curve_mae_mean"] < srgb["curve_mae_mean"]
                    and measured["overall_quality_loss_mae_mean"]
                    < srgb["overall_quality_loss_mae_mean"]
                ),
                "beats_rec709_on_curve_and_quality_loss": (
                    measured["curve_mae_mean"] < rec709["curve_mae_mean"]
                    and measured["overall_quality_loss_mae_mean"]
                    < rec709["overall_quality_loss_mae_mean"]
                ),
            },
        },
        "storage": {
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "new_fitted_artifact_paths": [
                "algo/deadleaf_13b10_imatest_sensor_comp_toe_measured_oecf_profile.json",
                "artifacts/issue77_measured_oecf_psd_benchmark.json",
                "artifacts/issue77_measured_oecf_acutance_benchmark.json",
                "artifacts/imatest_parity_measured_oecf_benchmark.json",
            ],
            "release_config_paths": [],
            "rules": [
                "Do not write fitted profiles, calibrations, or benchmark outputs under the golden/reference roots.",
                "Keep issue-77 fitted artifacts under algo/ and artifacts/ only.",
                "Do not promote a release-facing config until the measured-OECF family beats the current toe stand-in on the tracked guards.",
            ],
        },
        "sources": {
            "psd_artifact_path": relative_path(psd_artifact, repo_root),
            "acutance_artifact_path": relative_path(acutance_artifact, repo_root),
        },
    }
    promote = promotion_passes(payload["comparisons"]["measured_oecf_vs_toe_proxy"])
    payload["conclusion"] = {
        "status": "promote" if promote else "bounded_negative",
        "next_step": (
            "Advance this measured-OECF family beyond the toe stand-in."
            if promote
            else "Keep the issue as a bounded measured-OECF record only; the repo still lacks evidence that this family beats the toe stand-in."
        ),
    }
    assert_storage_separation(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    current_best = payload["profiles"][CURRENT_BEST_BRANCH_LABEL]
    toe = payload["profiles"][TOE_PROXY_LABEL]
    measured = payload["profiles"][MEASURED_OECF_LABEL]
    srgb = payload["profiles"][SRGB_LABEL]
    rec709 = payload["profiles"][REC709_LABEL]
    measured_vs_toe = payload["comparisons"]["measured_oecf_vs_toe_proxy"]["delta"]
    measured_vs_best = payload["comparisons"]["measured_oecf_vs_current_best_pr30"]["delta"]

    lines = [
        "# Imatest Parity Measured OECF Follow-up",
        "",
        "This note records the bounded measured-OECF family follow-up for issue `#77`.",
        "",
        "It builds on the family-selection result in issue `#71` / PR `#76`, which named "
        "`literal/measured_oecf_on_sensor_comp` as the next source-backed literal route.",
        "",
        "## Source Basis",
        "",
        "- Imatest gamma/OECF guidance still points to measured linearization as a missing family.",
        "- The earlier toe branch is only an engineering OECF stand-in, not a separate measured family record.",
        "- The repo already contains one source-backed matched-ORI quantile-transfer proxy from the earlier OECF audit, so issue `#77` reuses that same measured transfer formulation instead of reopening generic retunes.",
        "",
        "## Family Boundary Change",
        "",
        f"- Toe-proxy baseline: `{toe['profile_path']}`",
        f"- Measured-OECF candidate: `{measured['profile_path']}`",
        f"- Change: {payload['family_boundary_change']['change']}",
        f"- Artifact boundary note: {payload['family_boundary_change']['note']}",
        "",
        "## Profiles Compared",
        "",
        f"- current best branch from PR `#30`: `{current_best['profile_path']}`",
        f"- literal toe-proxy baseline from issue `#71`: `{toe['profile_path']}`",
        f"- issue `#77` measured-OECF candidate: `{measured['profile_path']}`",
        f"- inverse `sRGB` control: `{srgb['profile_path']}`",
        f"- inverse `Rec.709` control: `{rec709['profile_path']}`",
        "",
        "Artifacts:",
        "",
        f"- `{payload['sources']['psd_artifact_path']}`",
        f"- `{payload['sources']['acutance_artifact_path']}`",
        f"- `artifacts/imatest_parity_measured_oecf_benchmark.json`",
        "",
        "## Readout",
        "",
        "| Profile | Curve MAE | Focus Acu MAE | Overall QL | MTF20 | MTF30 | MTF50 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in (current_best, toe, measured, srgb, rec709):
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    format_metric(row["curve_mae_mean"]),
                    format_metric(row["focus_preset_acutance_mae_mean"]),
                    format_metric(row["overall_quality_loss_mae_mean"]),
                    format_metric(row["mtf_threshold_mae"]["mtf20"]),
                    format_metric(row["mtf_threshold_mae"]["mtf30"]),
                    format_metric(row["mtf_threshold_mae"]["mtf50"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Measured OECF Versus Toe Proxy",
            "",
            f"- `curve_mae_mean`: `{format_metric(toe['curve_mae_mean'])} -> {format_metric(measured['curve_mae_mean'])}` ({format_delta(measured_vs_toe['curve_mae_mean'])})",
            f"- focus-preset Acutance MAE mean: `{format_metric(toe['focus_preset_acutance_mae_mean'])} -> {format_metric(measured['focus_preset_acutance_mae_mean'])}` ({format_delta(measured_vs_toe['focus_preset_acutance_mae_mean'])})",
            f"- `overall_quality_loss_mae_mean`: `{format_metric(toe['overall_quality_loss_mae_mean'])} -> {format_metric(measured['overall_quality_loss_mae_mean'])}` ({format_delta(measured_vs_toe['overall_quality_loss_mae_mean'])})",
            f"- `MTF20` MAE: `{format_metric(toe['mtf_threshold_mae']['mtf20'])} -> {format_metric(measured['mtf_threshold_mae']['mtf20'])}` ({format_delta(measured_vs_toe['mtf_threshold_mae']['mtf20'])})",
            f"- `MTF30` MAE: `{format_metric(toe['mtf_threshold_mae']['mtf30'])} -> {format_metric(measured['mtf_threshold_mae']['mtf30'])}` ({format_delta(measured_vs_toe['mtf_threshold_mae']['mtf30'])})",
            f"- `MTF50` MAE: `{format_metric(toe['mtf_threshold_mae']['mtf50'])} -> {format_metric(measured['mtf_threshold_mae']['mtf50'])}` ({format_delta(measured_vs_toe['mtf_threshold_mae']['mtf50'])})",
            "",
            "## Measured OECF Versus PR #30 Current Best",
            "",
            f"- `curve_mae_mean`: `{format_metric(current_best['curve_mae_mean'])} -> {format_metric(measured['curve_mae_mean'])}` ({format_delta(measured_vs_best['curve_mae_mean'])})",
            f"- focus-preset Acutance MAE mean: `{format_metric(current_best['focus_preset_acutance_mae_mean'])} -> {format_metric(measured['focus_preset_acutance_mae_mean'])}` ({format_delta(measured_vs_best['focus_preset_acutance_mae_mean'])})",
            f"- `overall_quality_loss_mae_mean`: `{format_metric(current_best['overall_quality_loss_mae_mean'])} -> {format_metric(measured['overall_quality_loss_mae_mean'])}` ({format_delta(measured_vs_best['overall_quality_loss_mae_mean'])})",
            "",
            "## Controls",
            "",
            "- The measured-OECF candidate is benchmarked against the checked-in source-backed inverse-OETF controls rather than against a new free-form retune.",
            f"- Against `sRGB`: curve `{format_metric(srgb['curve_mae_mean'])}`, focus Acutance `{format_metric(srgb['focus_preset_acutance_mae_mean'])}`, overall QL `{format_metric(srgb['overall_quality_loss_mae_mean'])}`.",
            f"- Against `Rec.709`: curve `{format_metric(rec709['curve_mae_mean'])}`, focus Acutance `{format_metric(rec709['focus_preset_acutance_mae_mean'])}`, overall QL `{format_metric(rec709['overall_quality_loss_mae_mean'])}`.",
            "",
            "## Storage Separation",
            "",
            "- Golden/reference roots:",
            *[f"  - `{path}`" for path in payload["storage"]["golden_reference_roots"]],
            "- New fitted artifacts:",
            *[f"  - `{path}`" for path in payload["storage"]["new_fitted_artifact_paths"]],
            "- Rules:",
            *[f"  - {rule}" for rule in payload["storage"]["rules"]],
            "",
            "## Working Conclusion",
            "",
        ]
    )
    if payload["conclusion"]["status"] == "promote":
        lines.append(
            "- The measured-OECF candidate beats the toe stand-in on the tracked primary guards and is worth advancing as the next literal parity implementation line."
        )
    else:
        lines.append(
            "- The measured-OECF candidate does not beat the toe stand-in on the tracked primary guards, so this issue closes as a bounded measured-OECF record rather than as a new default path."
        )
    lines.append(f"- Next step: {payload['conclusion']['next_step']}")
    return "\n".join(lines)


def write_outputs(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    output_json: Path,
    output_md: Path,
) -> None:
    json_path = resolve_output(output_json, repo_root)
    md_path = resolve_output(output_md, repo_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(
        repo_root,
        psd_artifact_path=args.psd_artifact,
        acutance_artifact_path=args.acutance_artifact,
    )
    write_outputs(
        payload,
        repo_root=repo_root,
        output_json=args.output_json,
        output_md=args.output_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
