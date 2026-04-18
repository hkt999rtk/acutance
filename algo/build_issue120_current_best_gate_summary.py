from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CURRENT_BEST_LABEL = "issue118_large_print_quality_loss_input_boundary_candidate"
PR30_LABEL = "current_best_pr30_branch"
SUMMARY_KIND = "issue120_current_best_readme_gate_summary"
CURRENT_BEST_COMMIT = "52bbca7"
CURRENT_BEST_PR = 119
CURRENT_BEST_ISSUE = 118
ISSUE = 120
UMBRELLA_ISSUE = 29
NEXT_SLICE_ID = "issue118_remaining_curve_small_print_acutance_discovery"

README_GATES = {
    "curve_mae_mean": 0.020,
    "focus_preset_acutance_mae_mean": 0.030,
    "overall_quality_loss_mae_mean": 1.30,
    "non_phone_acutance_preset_mae_max": 0.030,
    '5.5" Phone Display Acutance': 0.050,
}
PHONE_PRESET = '5.5" Phone Display Acutance'
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build issue-120 current-best README gate summary."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--issue118-summary",
        type=Path,
        default=Path("artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json"),
        help="Repo-relative issue-118 summary artifact path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue120_current_best_readme_gate_summary.json"),
        help="Repo-relative output path for the machine-readable summary.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue120_current_best_readme_gate_summary.md"),
        help="Repo-relative output path for the Markdown summary.",
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def delta_map(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "curve_mae_mean": float(left["curve_mae_mean"] - right["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            left["focus_preset_acutance_mae_mean"]
            - right["focus_preset_acutance_mae_mean"]
        ),
        "overall_quality_loss_mae_mean": float(
            left["overall_quality_loss_mae_mean"] - right["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            left["mtf_abs_signed_rel_mean"] - right["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(left["mtf_threshold_mae"][key] - right["mtf_threshold_mae"][key])
            for key in left["mtf_threshold_mae"]
        },
        "acutance_preset_mae": {
            key: float(left["acutance_preset_mae"][key] - right["acutance_preset_mae"][key])
            for key in left["acutance_preset_mae"]
        },
        "quality_loss_preset_mae": {
            key: float(
                left["quality_loss_preset_mae"][key] - right["quality_loss_preset_mae"][key]
            )
            for key in left["quality_loss_preset_mae"]
        },
    }


def build_readme_gate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    acutance = candidate["acutance_preset_mae"]
    non_phone_values = {
        preset: value for preset, value in acutance.items() if preset != PHONE_PRESET
    }
    non_phone_max_preset, non_phone_max_value = max(
        non_phone_values.items(), key=lambda item: item[1]
    )
    gate_results = {
        "curve_mae_mean": {
            "value": float(candidate["curve_mae_mean"]),
            "threshold": README_GATES["curve_mae_mean"],
            "operator": "<=",
            "pass": candidate["curve_mae_mean"] <= README_GATES["curve_mae_mean"],
        },
        "focus_preset_acutance_mae_mean": {
            "value": float(candidate["focus_preset_acutance_mae_mean"]),
            "threshold": README_GATES["focus_preset_acutance_mae_mean"],
            "operator": "<=",
            "pass": (
                candidate["focus_preset_acutance_mae_mean"]
                <= README_GATES["focus_preset_acutance_mae_mean"]
            ),
        },
        "overall_quality_loss_mae_mean": {
            "value": float(candidate["overall_quality_loss_mae_mean"]),
            "threshold": README_GATES["overall_quality_loss_mae_mean"],
            "operator": "<=",
            "pass": (
                candidate["overall_quality_loss_mae_mean"]
                <= README_GATES["overall_quality_loss_mae_mean"]
            ),
        },
        "non_phone_acutance_preset_mae_max": {
            "value": float(non_phone_max_value),
            "threshold": README_GATES["non_phone_acutance_preset_mae_max"],
            "operator": "<=",
            "pass": (
                non_phone_max_value <= README_GATES["non_phone_acutance_preset_mae_max"]
            ),
            "worst_preset": non_phone_max_preset,
            "by_preset": {key: float(value) for key, value in sorted(non_phone_values.items())},
        },
        PHONE_PRESET: {
            "value": float(acutance[PHONE_PRESET]),
            "threshold": README_GATES[PHONE_PRESET],
            "operator": "<=",
            "pass": acutance[PHONE_PRESET] <= README_GATES[PHONE_PRESET],
        },
    }
    return {
        "all_readme_gates_pass": all(result["pass"] for result in gate_results.values()),
        "failed_gates": [
            gate_name for gate_name, result in gate_results.items() if not result["pass"]
        ],
        "gates": gate_results,
    }


def assert_storage_separation(payload: dict[str, Any]) -> None:
    for path in payload["current_best"]["source_artifacts"]:
        if path.startswith(GOLDEN_REFERENCE_ROOTS):
            raise ValueError(f"candidate artifact entered release/golden root: {path}")
    candidate_path = payload["current_best"]["profile_path"]
    if candidate_path.startswith(GOLDEN_REFERENCE_ROOTS):
        raise ValueError(f"candidate profile entered release/golden root: {candidate_path}")


def build_payload(repo_root: Path, *, issue118_summary_path: Path) -> dict[str, Any]:
    issue118_summary = load_json(resolve_path(repo_root, issue118_summary_path))
    profiles = issue118_summary["profiles"]
    pr30 = profiles[PR30_LABEL]
    candidate = profiles[CURRENT_BEST_LABEL]
    gate_summary = build_readme_gate_summary(candidate)
    candidate_vs_pr30 = delta_map(candidate, pr30)

    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "current_best": {
            "label": CURRENT_BEST_LABEL,
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "merge_commit": CURRENT_BEST_COMMIT,
            "profile_path": candidate["profile_path"],
            "source_artifacts": [
                "artifacts/intrinsic_after_issue116_quality_loss_boundary_benchmark.json",
                "artifacts/issue118_large_print_quality_loss_boundary_acutance_benchmark.json",
                "artifacts/issue118_large_print_quality_loss_boundary_psd_benchmark.json",
            ],
            "metrics": {
                "curve_mae_mean": float(candidate["curve_mae_mean"]),
                "focus_preset_acutance_mae_mean": float(
                    candidate["focus_preset_acutance_mae_mean"]
                ),
                "overall_quality_loss_mae_mean": float(
                    candidate["overall_quality_loss_mae_mean"]
                ),
                "mtf_abs_signed_rel_mean": float(candidate["mtf_abs_signed_rel_mean"]),
                "mtf_threshold_mae": {
                    key: float(value) for key, value in candidate["mtf_threshold_mae"].items()
                },
                "acutance_preset_mae": {
                    key: float(value) for key, value in candidate["acutance_preset_mae"].items()
                },
            },
        },
        "baseline": {
            "label": PR30_LABEL,
            "issue": 29,
            "pr": 30,
            "profile_path": pr30["profile_path"],
            "metrics": {
                "curve_mae_mean": float(pr30["curve_mae_mean"]),
                "focus_preset_acutance_mae_mean": float(
                    pr30["focus_preset_acutance_mae_mean"]
                ),
                "overall_quality_loss_mae_mean": float(pr30["overall_quality_loss_mae_mean"]),
                "mtf_abs_signed_rel_mean": float(pr30["mtf_abs_signed_rel_mean"]),
                "mtf_threshold_mae": {
                    key: float(value) for key, value in pr30["mtf_threshold_mae"].items()
                },
                "acutance_preset_mae": {
                    key: float(value) for key, value in pr30["acutance_preset_mae"].items()
                },
            },
        },
        "comparisons": {
            "current_best_vs_pr30": {"delta": candidate_vs_pr30},
        },
        "readme_gate_summary": gate_summary,
        "next_handoff": {
            "mode": "developer_discovery",
            "selected_slice_id": NEXT_SLICE_ID,
            "goal": (
                "Use the issue #118 profile and checked-in per-sample/benchmark artifacts to "
                "decide whether the remaining curve MAE miss and Small Print Acutance miss can be "
                "handled by one bounded acutance-side/readout-boundary implementation, or whether "
                "they must be split."
            ),
            "why_not_direct_implementation": (
                "The issue #118 branch already passes focus-preset Acutance mean, Phone, overall "
                "Quality Loss, and reported-MTF checks. The remaining failures are cross-family: "
                "curve MAE is still far above the README threshold, while only Small Print exceeds "
                "the non-Phone Acutance preset gate by a small margin. Issue #120 explicitly rules "
                "out another broad Quality Loss or readout retune, so the next implementable slice "
                "needs evidence mining before code changes."
            ),
            "acceptance_criteria": [
                "Identify one source-backed knob or boundary that targets either the curve MAE miss or the Small Print Acutance miss without broad retuning.",
                "Show whether the selected slice is expected to preserve the PR #119 Quality Loss and reported-MTF record.",
                "Record explicit pass/miss deltas against README gates and PR #119.",
            ],
            "validation_plan": [
                "Regenerate the relevant acutance/Quality Loss benchmark artifact on the issue #118 profile family.",
                "Compare curve MAE, focus-preset Acutance mean, per-preset Acutance, overall Quality Loss, and MTF thresholds against PR #119.",
                "Keep fitted artifacts under algo/ and artifacts/ only; do not promote release-facing configs.",
            ],
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "The issue #118 / PR #119 profile is a canonical-target candidate, not a release-facing config promotion.",
                "Do not copy fitted outputs into golden/reference data roots or release config roots.",
                "Release-facing configs remain separate until a later bounded implementation clears README gates.",
            ],
        },
        "refs": {
            "umbrella_issue": UMBRELLA_ISSUE,
            "current_issue": ISSUE,
            "current_best_issue": CURRENT_BEST_ISSUE,
            "current_best_pr": CURRENT_BEST_PR,
            "baseline_pr": 30,
        },
    }
    assert_storage_separation(payload)
    return payload


def format_metric(value: float) -> str:
    return f"{value:.5f}"


def render_pass(value: bool) -> str:
    return "pass" if value else "miss"


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_best"]
    baseline = payload["baseline"]
    gate_summary = payload["readme_gate_summary"]
    delta = payload["comparisons"]["current_best_vs_pr30"]["delta"]

    lines = [
        "# Issue 120 Current Best README Gate Summary",
        "",
        "Issue `#120` refreshes the canonical current-best record after issue `#118` / PR `#119`.",
        "",
        "## Current Best",
        "",
        f"- Current best canonical-target candidate: issue `#{current['issue']}` / PR `#{current['pr']}` at commit `{current['merge_commit']}`.",
        f"- Candidate profile: `{current['profile_path']}`",
        f"- Baseline comparison branch: PR `#{baseline['pr']}` (`{baseline['label']}`).",
        "- This is not a release-facing config promotion; fitted outputs remain under `algo/` and `artifacts/`.",
        "",
        "## PR 119 Versus PR 30",
        "",
        "| Metric | PR 30 | PR 119 | Delta |",
        "| --- | --- | --- | --- |",
        f"| Curve MAE | {format_metric(baseline['metrics']['curve_mae_mean'])} | {format_metric(current['metrics']['curve_mae_mean'])} | {delta['curve_mae_mean']:+.5f} |",
        f"| Focus Acu MAE | {format_metric(baseline['metrics']['focus_preset_acutance_mae_mean'])} | {format_metric(current['metrics']['focus_preset_acutance_mae_mean'])} | {delta['focus_preset_acutance_mae_mean']:+.5f} |",
        f"| Overall Quality Loss | {format_metric(baseline['metrics']['overall_quality_loss_mae_mean'])} | {format_metric(current['metrics']['overall_quality_loss_mae_mean'])} | {delta['overall_quality_loss_mae_mean']:+.5f} |",
        f"| MTF20 | {format_metric(baseline['metrics']['mtf_threshold_mae']['mtf20'])} | {format_metric(current['metrics']['mtf_threshold_mae']['mtf20'])} | {delta['mtf_threshold_mae']['mtf20']:+.5f} |",
        f"| MTF30 | {format_metric(baseline['metrics']['mtf_threshold_mae']['mtf30'])} | {format_metric(current['metrics']['mtf_threshold_mae']['mtf30'])} | {delta['mtf_threshold_mae']['mtf30']:+.5f} |",
        f"| MTF50 | {format_metric(baseline['metrics']['mtf_threshold_mae']['mtf50'])} | {format_metric(current['metrics']['mtf_threshold_mae']['mtf50'])} | {delta['mtf_threshold_mae']['mtf50']:+.5f} |",
        "",
        "## README Gate Status",
        "",
        "| Gate | Value | Threshold | Status |",
        "| --- | --- | --- | --- |",
    ]

    for gate_name, result in gate_summary["gates"].items():
        label = gate_name
        if gate_name == "non_phone_acutance_preset_mae_max":
            label = f"non-Phone Acutance max ({result['worst_preset']})"
        lines.append(
            f"| {label} | {format_metric(result['value'])} | <= {format_metric(result['threshold'])} | {render_pass(result['pass'])} |"
        )

    non_phone = gate_summary["gates"]["non_phone_acutance_preset_mae_max"]
    lines.extend(
        [
            "",
            "Remaining README misses:",
            "",
            (
                "- `curve_mae_mean <= 0.020` still misses because PR #119 is "
                f"`{format_metric(gate_summary['gates']['curve_mae_mean']['value'])}`."
            ),
            (
                "- Non-Phone Acutance still misses only at "
                f"`{non_phone['worst_preset']} = {format_metric(non_phone['value'])}` "
                "against the `<= 0.030` gate."
            ),
            "",
            "## Next Handoff",
            "",
            f"- Mode: `{payload['next_handoff']['mode']}`",
            f"- Selected slice id: `{payload['next_handoff']['selected_slice_id']}`",
            f"- Goal: {payload['next_handoff']['goal']}",
            f"- Why discovery first: {payload['next_handoff']['why_not_direct_implementation']}",
            "",
            "Acceptance criteria for the next slice:",
            "",
        ]
    )
    for item in payload["next_handoff"]["acceptance_criteria"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Validation plan:",
            "",
        ]
    )
    for item in payload["next_handoff"]["validation_plan"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Release Separation",
            "",
        ]
    )
    for rule in payload["release_separation"]["rules"]:
        lines.append(f"- {rule}")
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_payload(repo_root, issue118_summary_path=args.issue118_summary)
    write_text(
        resolve_path(repo_root, args.output_json),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    write_text(resolve_path(repo_root, args.output_md), render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
