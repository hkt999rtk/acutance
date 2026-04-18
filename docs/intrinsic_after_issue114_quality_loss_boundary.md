# Intrinsic After Issue 114 Quality Loss Boundary

Issue `#116` implements the bounded slice after issue `#114`: isolate only the `Small Print Quality Loss` preset-family input boundary while preserving the Computer Monitor improvement and reported-MTF parity.

## Scope

- Basis issue `#114` profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_pr30_input_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_pr30_input_profile.json`
- Targeted added override: `Small Print Quality Loss` uses the PR `#30` acutance-only / noise-share anchor input.
- Existing issue-114 `Computer Monitor Quality Loss` override is preserved.
- Other Quality Loss presets stay on the issue-114 path.
- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` are unchanged.

## Result

| Record | Curve MAE | Focus Acu MAE | Overall QL | Computer Monitor QL | Small Print QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 2.90291 | 0.60769 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue114_computer_monitor_quality_loss_input_boundary_candidate | 0.03280 | 0.02892 | 1.27487 | 2.90611 | 0.85450 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue116_small_print_quality_loss_input_boundary_candidate | 0.03280 | 0.02892 | 1.22551 | 2.90611 | 0.60770 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |

## Deltas

- Candidate versus issue `#114`: `Small Print Quality Loss = -0.24680`, `overall_quality_loss_mae_mean = -0.04936`.
- Candidate versus PR `#30`: `Small Print Quality Loss = +0.00000`, `overall_quality_loss_mae_mean = +0.00401`.
- Computer Monitor Quality Loss delta versus issue `#114`: `+0.00000`.
- Reported-MTF equality versus issue `#114`: `True`.
- Non-target Quality Loss presets unchanged versus issue `#114`: `True`.

## Acceptance

- `selected_slice_matches_issue116`: `True`
- `small_print_quality_loss_improved_vs_issue114`: `True`
- `overall_quality_loss_improved_vs_issue114`: `True`
- `computer_monitor_quality_loss_preserved_vs_issue114`: `True`
- `curve_mae_non_worse_than_issue114`: `True`
- `focus_preset_acutance_non_worse_than_issue114`: `True`
- `reported_mtf_equal_to_issue114`: `True`
- `only_small_print_quality_loss_input_added`: `True`
- `quality_loss_coefficients_preserved`: `True`
- `all_issue116_gates_pass`: `True`

## Conclusion

- Status: `issue116_positive_partial_result`
- Summary: The Small Print-only Quality Loss input boundary materially improves the largest remaining residual preset and overall Quality Loss versus issue #114, but a small residual still remains versus PR #30.
- Next step: Keep this as the issue-116 bounded implementation record and split the next residual Quality Loss boundary from the checked-in candidate-vs-PR30 deltas.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/config`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
