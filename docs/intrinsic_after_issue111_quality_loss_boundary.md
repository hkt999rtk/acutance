# Intrinsic After Issue 111 Quality Loss Boundary

Issue `#114` implements the bounded slice selected by issue `#111`: isolate only the `Computer Monitor Quality Loss` preset-family input boundary after issue `#108` matched PR `#30` on reported-MTF metrics.

## Scope

- Basis issue `#108` profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_pr30_input_profile.json`
- Targeted override: `Computer Monitor Quality Loss` uses the PR `#30` acutance-only / noise-share anchor input.
- Non-target Quality Loss presets stay on the issue-108 path.
- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` are unchanged.

## Result

| Record | Curve MAE | Focus Acu MAE | Overall QL | Computer Monitor QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 2.90291 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue108_pr30_observed_bundle_candidate | 0.03280 | 0.02892 | 1.40663 | 3.56493 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue114_computer_monitor_quality_loss_input_boundary_candidate | 0.03280 | 0.02892 | 1.27487 | 2.90611 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |

## Deltas

- Candidate versus issue `#108`: `Computer Monitor Quality Loss = -0.65882`, `overall_quality_loss_mae_mean = -0.13176`.
- Candidate versus PR `#30`: `Computer Monitor Quality Loss = +0.00321`, `overall_quality_loss_mae_mean = +0.05337`.
- Reported-MTF equality versus issue `#108`: `True`.
- Non-target Quality Loss presets unchanged versus issue `#108`: `True`.

## Acceptance

- `selected_slice_matches_issue111`: `True`
- `computer_monitor_quality_loss_improved_vs_issue108`: `True`
- `overall_quality_loss_improved_vs_issue108`: `True`
- `curve_mae_non_worse_than_issue108`: `True`
- `focus_preset_acutance_non_worse_than_issue108`: `True`
- `reported_mtf_equal_to_issue108`: `True`
- `only_computer_monitor_quality_loss_input_overridden`: `True`
- `quality_loss_coefficients_preserved`: `True`
- `all_issue114_gates_pass`: `True`

## Conclusion

- Status: `issue114_positive_partial_result`
- Summary: The Computer Monitor-only Quality Loss input boundary materially improves the largest residual preset and overall Quality Loss versus issue #108, but a smaller residual still remains versus PR #30.
- Next step: Keep this as the issue-114 bounded implementation record and split the next residual Quality Loss boundary from the checked-in candidate-vs-PR30 deltas.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/config`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
