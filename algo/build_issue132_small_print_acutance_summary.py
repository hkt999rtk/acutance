from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ISSUE = 132
UMBRELLA_ISSUE = 29
CURRENT_BEST_ISSUE = 124
CURRENT_BEST_PR = 125
DISCOVERY_ISSUE = 130
DISCOVERY_PR = 131
BASELINE_PR = 30
SUMMARY_KIND = "issue132_small_print_acutance_boundary_summary"
RESULT_KIND = "positive_targeted_not_full_canonical"
TARGET_PRESET = "Small Print Acutance"
PHONE_PRESET = '5.5" Phone Display Acutance'
CURVE_GATE = 0.020
FOCUS_PRESET_GATE = 0.030
QUALITY_LOSS_GATE = 1.30
NON_PHONE_ACUTANCE_GATE = 0.030
GOLDEN_REFERENCE_ROOTS = (
    "20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/data/20260318_deadleaf_13b10",
    "release/deadleaf_13b10_release/config",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build issue-132 Small Print summary.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--issue124-summary",
        type=Path,
        default=Path("artifacts/issue124_curve_only_high_mixup_ori_summary.json"),
    )
    parser.add_argument(
        "--issue130-discovery",
        type=Path,
        default=Path("artifacts/issue130_next_slice_discovery.json"),
    )
    parser.add_argument(
        "--candidate-profile",
        type=Path,
        default=Path("algo/issue132_small_print_acutance_parity_input_profile.json"),
    )
    parser.add_argument(
        "--baseline-profile",
        type=Path,
        default=Path(
            "algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json"
        ),
    )
    parser.add_argument(
        "--candidate-acutance",
        type=Path,
        default=Path("artifacts/issue132_small_print_acutance_boundary_acutance_benchmark.json"),
    )
    parser.add_argument(
        "--candidate-psd",
        type=Path,
        default=Path("artifacts/issue132_small_print_acutance_boundary_psd_benchmark.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/issue132_small_print_acutance_boundary_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/issue132_small_print_acutance_boundary_summary.md"),
    )
    return parser


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_single_profile(payload: dict[str, Any]) -> dict[str, Any]:
    profiles = payload["profiles"]
    if len(profiles) != 1:
        raise ValueError(f"Expected one profile, found {len(profiles)}")
    return profiles[0]


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


def collect_candidate_metrics(
    *,
    candidate_acutance: dict[str, Any],
    candidate_psd: dict[str, Any],
) -> dict[str, Any]:
    acutance = candidate_acutance["overall"]
    psd = candidate_psd["overall"]
    return {
        "curve_mae_mean": float(acutance["curve_mae_mean"]),
        "acutance_focus_preset_mae_mean": float(acutance["acutance_focus_preset_mae_mean"]),
        "overall_quality_loss_mae_mean": float(acutance["overall_quality_loss_mae_mean"]),
        "mtf_abs_signed_rel_mean": float(psd["mtf_abs_signed_rel_mean"]),
        "mtf_threshold_mae": {
            key: float(value) for key, value in psd["mtf_threshold_mae"].items()
        },
        "acutance_preset_mae": {
            key: float(value) for key, value in acutance["acutance_preset_mae"].items()
        },
        "quality_loss_preset_mae": {
            key: float(value) for key, value in acutance["quality_loss_preset_mae"].items()
        },
    }


def metric_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_focus_key = (
        "acutance_focus_preset_mae_mean"
        if "acutance_focus_preset_mae_mean" in baseline
        else "focus_preset_acutance_mae_mean"
    )
    return {
        "curve_mae_mean": float(candidate["curve_mae_mean"] - baseline["curve_mae_mean"]),
        "focus_preset_acutance_mae_mean": float(
            candidate["acutance_focus_preset_mae_mean"] - baseline[baseline_focus_key]
        ),
        "overall_quality_loss_mae_mean": float(
            candidate["overall_quality_loss_mae_mean"]
            - baseline["overall_quality_loss_mae_mean"]
        ),
        "mtf_abs_signed_rel_mean": float(
            candidate["mtf_abs_signed_rel_mean"] - baseline["mtf_abs_signed_rel_mean"]
        ),
        "mtf_threshold_mae": {
            key: float(candidate["mtf_threshold_mae"][key] - baseline["mtf_threshold_mae"][key])
            for key in candidate["mtf_threshold_mae"]
        },
        "acutance_preset_mae": {
            key: float(
                candidate["acutance_preset_mae"][key] - baseline["acutance_preset_mae"][key]
            )
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


def is_close(left: float, right: float, *, tolerance: float = 1e-12) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def is_release_path(path: str) -> bool:
    return path.startswith(GOLDEN_REFERENCE_ROOTS)


def profile_scope_delta(
    *,
    baseline_profile: dict[str, Any],
    candidate_profile: dict[str, Any],
) -> dict[str, Any]:
    ignored = {"name"}
    changed_keys = sorted(
        key
        for key in set(baseline_profile) | set(candidate_profile)
        if key not in ignored and baseline_profile.get(key) != candidate_profile.get(key)
    )
    return {
        "changed_keys": changed_keys,
        "only_acutance_preset_input_override_added": changed_keys
        == ["acutance_preset_input_profile_overrides"],
        "acutance_preset_input_profile_overrides": candidate_profile.get(
            "acutance_preset_input_profile_overrides"
        ),
        "quality_loss_preset_input_profile_overrides_preserved": (
            candidate_profile.get("quality_loss_preset_input_profile_overrides")
            == baseline_profile.get("quality_loss_preset_input_profile_overrides")
        ),
        "curve_only_acutance_anchor_mixups_preserved": (
            candidate_profile.get("curve_only_acutance_anchor_mixups")
            == baseline_profile.get("curve_only_acutance_anchor_mixups")
        ),
        "reported_mtf_readout_fields_preserved": all(
            candidate_profile.get(key) == baseline_profile.get(key)
            for key in (
                "mtf_compensation_mode",
                "sensor_fill_factor",
                "matched_ori_reference_anchor",
                "matched_ori_anchor_mode",
                "intrinsic_full_reference_scope",
            )
        ),
        "quality_loss_coefficients_preserved": (
            candidate_profile.get("quality_loss_coefficients")
            == baseline_profile.get("quality_loss_coefficients")
            and candidate_profile.get("quality_loss_preset_overrides")
            == baseline_profile.get("quality_loss_preset_overrides")
        ),
    }


def build_payload(
    repo_root: Path,
    *,
    issue124_summary_path: Path,
    issue130_discovery_path: Path,
    candidate_profile_path: Path,
    baseline_profile_path: Path,
    candidate_acutance_path: Path,
    candidate_psd_path: Path,
) -> dict[str, Any]:
    issue124 = load_json(resolve_path(repo_root, issue124_summary_path))
    issue130 = load_json(resolve_path(repo_root, issue130_discovery_path))
    baseline_profile = load_json(resolve_path(repo_root, baseline_profile_path))
    candidate_profile = load_json(resolve_path(repo_root, candidate_profile_path))
    candidate_acutance = select_single_profile(
        load_json(resolve_path(repo_root, candidate_acutance_path))
    )
    candidate_psd = select_single_profile(load_json(resolve_path(repo_root, candidate_psd_path)))
    baseline = issue124["candidate"]["metrics"]
    candidate = collect_candidate_metrics(
        candidate_acutance=candidate_acutance,
        candidate_psd=candidate_psd,
    )
    delta = metric_delta(candidate, baseline)
    scope = profile_scope_delta(
        baseline_profile=baseline_profile,
        candidate_profile=candidate_profile,
    )
    payload = {
        "issue": ISSUE,
        "summary_kind": SUMMARY_KIND,
        "result_kind": RESULT_KIND,
        "candidate": {
            "label": "issue132_small_print_acutance_parity_input",
            "profile_path": str(candidate_profile_path),
            "source_artifacts": [
                str(candidate_acutance_path),
                str(candidate_psd_path),
                str(issue124_summary_path),
                str(issue130_discovery_path),
            ],
            "metrics": candidate,
        },
        "baseline_pr125": {
            "issue": CURRENT_BEST_ISSUE,
            "pr": CURRENT_BEST_PR,
            "profile_path": str(baseline_profile_path),
            "metrics": baseline,
        },
        "readme_gate_summary": readme_gate_summary(candidate),
        "comparisons": {
            "candidate_vs_pr125": {"delta": delta},
            "issue130_selected_slice": issue130["selected_next_slice"],
        },
        "small_print_result": {
            "target_preset": TARGET_PRESET,
            "baseline_value": float(baseline["acutance_preset_mae"][TARGET_PRESET]),
            "candidate_value": float(candidate["acutance_preset_mae"][TARGET_PRESET]),
            "delta_vs_pr125": float(delta["acutance_preset_mae"][TARGET_PRESET]),
            "gate": NON_PHONE_ACUTANCE_GATE,
            "candidate_delta_to_gate": float(
                candidate["acutance_preset_mae"][TARGET_PRESET] - NON_PHONE_ACUTANCE_GATE
            ),
            "override_source_profile": candidate_profile[
                "acutance_preset_input_profile_overrides"
            ][TARGET_PRESET],
        },
        "profile_scope_delta": scope,
        "acceptance": {
            "small_print_gate_pass": (
                candidate["acutance_preset_mae"][TARGET_PRESET] <= NON_PHONE_ACUTANCE_GATE
            ),
            "focus_preset_acutance_gate_pass": (
                candidate["acutance_focus_preset_mae_mean"] <= FOCUS_PRESET_GATE
            ),
            "curve_mae_preserved_vs_pr125": is_close(delta["curve_mae_mean"], 0.0),
            "reported_mtf_preserved_vs_pr125": (
                is_close(delta["mtf_abs_signed_rel_mean"], 0.0)
                and all(is_close(value, 0.0) for value in delta["mtf_threshold_mae"].values())
            ),
            "overall_quality_loss_gate_pass": (
                candidate["overall_quality_loss_mae_mean"] <= QUALITY_LOSS_GATE
            ),
            "overall_quality_loss_preserved_vs_pr125": is_close(
                delta["overall_quality_loss_mae_mean"],
                0.0,
            ),
            "quality_loss_inputs_preserved": (
                scope["quality_loss_preset_input_profile_overrides_preserved"]
                and scope["quality_loss_coefficients_preserved"]
            ),
            "only_small_print_acutance_input_added": (
                scope["only_acutance_preset_input_override_added"]
                and scope["acutance_preset_input_profile_overrides"]
                == {TARGET_PRESET: "algo/deadleaf_13b10_parity_psd_mtf_profile.json"}
            ),
            "release_separation_preserved": True,
            "full_readme_gate_pass": readme_gate_summary(candidate)["all_readme_gates_pass"],
        },
        "next_result": {
            "summary": (
                "The Small Print Acutance preset-only boundary passes the targeted "
                "non-Phone Acutance gate while preserving PR #125 curve MAE, reported-MTF, "
                "overall Quality Loss, Quality Loss inputs, and release separation."
            ),
            "remaining_miss": (
                "The full canonical README target still misses only `curve_mae_mean <= 0.020`; "
                "future curve work remains gated on a separate `0.15` improvement preflight."
            ),
        },
        "release_separation": {
            "candidate_is_release_config": False,
            "golden_reference_roots": list(GOLDEN_REFERENCE_ROOTS),
            "rules": [
                "The candidate profile is canonical-target research only.",
                "No fitted outputs are written under golden/reference data roots.",
                "No release-facing config is promoted in this issue.",
            ],
        },
        "refs": {
            "umbrella_issue": UMBRELLA_ISSUE,
            "current_issue": ISSUE,
            "current_best_issue": CURRENT_BEST_ISSUE,
            "current_best_pr": CURRENT_BEST_PR,
            "discovery_issue": DISCOVERY_ISSUE,
            "discovery_pr": DISCOVERY_PR,
            "baseline_pr": BASELINE_PR,
        },
    }
    assert_storage_separation(payload)
    return payload


def assert_storage_separation(payload: dict[str, Any]) -> None:
    paths = [
        payload["candidate"]["profile_path"],
        *payload["candidate"]["source_artifacts"],
    ]
    for path in paths:
        if is_release_path(path):
            raise ValueError(f"candidate path entered golden/release root: {path}")


def format_metric(value: float) -> str:
    return f"{float(value):.5f}"


def render_markdown(payload: dict[str, Any]) -> str:
    candidate = payload["candidate"]
    metrics = candidate["metrics"]
    pr125 = payload["baseline_pr125"]["metrics"]
    delta = payload["comparisons"]["candidate_vs_pr125"]["delta"]
    gates = payload["readme_gate_summary"]["gates"]
    small = payload["small_print_result"]
    acceptance = payload["acceptance"]
    return "\n".join(
        [
            "# Issue 132 Small Print Acutance Boundary Summary",
            "",
            f"- Result: `{payload['result_kind']}`.",
            f"- Candidate profile: `{candidate['profile_path']}`.",
            f"- Target preset: `{small['target_preset']}`.",
            f"- Override source profile: `{small['override_source_profile']}`.",
            "",
            "## Metrics",
            "",
            "| Metric | PR #125 | Issue #132 | Delta | Gate |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| curve_mae_mean | {format_metric(pr125['curve_mae_mean'])} | "
            f"{format_metric(metrics['curve_mae_mean'])} | "
            f"{format_metric(delta['curve_mae_mean'])} | "
            f"<= 0.020 ({'pass' if gates['curve_mae_mean']['pass'] else 'miss'}) |",
            f"| focus_preset_acutance_mae_mean | "
            f"{format_metric(pr125['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(metrics['acutance_focus_preset_mae_mean'])} | "
            f"{format_metric(delta['focus_preset_acutance_mae_mean'])} | "
            f"<= 0.030 ({'pass' if gates['focus_preset_acutance_mae_mean']['pass'] else 'miss'}) |",
            f"| overall_quality_loss_mae_mean | "
            f"{format_metric(pr125['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(metrics['overall_quality_loss_mae_mean'])} | "
            f"{format_metric(delta['overall_quality_loss_mae_mean'])} | "
            f"<= 1.30 ({'pass' if gates['overall_quality_loss_mae_mean']['pass'] else 'miss'}) |",
            f"| mtf_abs_signed_rel_mean | {format_metric(pr125['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(metrics['mtf_abs_signed_rel_mean'])} | "
            f"{format_metric(delta['mtf_abs_signed_rel_mean'])} | preserve |",
            f"| Small Print Acutance | "
            f"{format_metric(small['baseline_value'])} | "
            f"{format_metric(small['candidate_value'])} | "
            f"{format_metric(small['delta_vs_pr125'])} | "
            f"<= 0.030 ({'pass' if acceptance['small_print_gate_pass'] else 'miss'}) |",
            "",
            "## Scope",
            "",
            f"- Changed profile keys: `{', '.join(payload['profile_scope_delta']['changed_keys'])}`.",
            f"- Only Small Print Acutance input override added: `{acceptance['only_small_print_acutance_input_added']}`.",
            f"- Quality Loss inputs preserved: `{acceptance['quality_loss_inputs_preserved']}`.",
            f"- Reported-MTF preserved: `{acceptance['reported_mtf_preserved_vs_pr125']}`.",
            f"- Curve MAE preserved versus PR #125: `{acceptance['curve_mae_preserved_vs_pr125']}`.",
            "",
            "## Result",
            "",
            payload["next_result"]["summary"],
            "",
            payload["next_result"]["remaining_miss"],
            "",
            "## Release Separation",
            "",
            "This remains canonical-target research, not a release-facing config promotion. "
            "No fitted outputs are written under golden/reference data roots or release configs.",
        ]
    )


def main() -> None:
    args = build_parser().parse_args()
    repo_root = args.repo_root
    payload = build_payload(
        repo_root,
        issue124_summary_path=args.issue124_summary,
        issue130_discovery_path=args.issue130_discovery,
        candidate_profile_path=args.candidate_profile,
        baseline_profile_path=args.baseline_profile,
        candidate_acutance_path=args.candidate_acutance,
        candidate_psd_path=args.candidate_psd,
    )
    output_json = resolve_path(repo_root, args.output_json)
    output_md = resolve_path(repo_root, args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
