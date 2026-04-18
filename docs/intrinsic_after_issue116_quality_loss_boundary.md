# Intrinsic After Issue 116 Quality Loss Boundary

Issue `#118` implements the bounded slice after issue `#116`: isolate only the `Large Print Quality Loss` preset-family input boundary while preserving the Computer Monitor and Small Print improvements plus reported-MTF parity.

## Scope

- Basis issue `#116` profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_pr30_input_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_profile.json`
- Targeted added override: `Large Print Quality Loss` uses the PR `#30` acutance-only / noise-share anchor input.
- Existing issue-114 `Computer Monitor Quality Loss` and issue-116 `Small Print Quality Loss` overrides are preserved.
- Other Quality Loss presets stay on the issue-116 path.
- Quality Loss coefficients, preset overrides, and `quality_loss_om_ceiling` are unchanged.

## Result

| Record | Curve MAE | Focus Acu MAE | Overall QL | Computer Monitor QL | Small Print QL | Large Print QL | MTF20 | MTF30 | MTF50 | Abs Signed Rel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_best_pr30_branch | 0.03679 | 0.04249 | 1.22150 | 2.90291 | 0.60769 | 0.95482 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue116_small_print_quality_loss_input_boundary_candidate | 0.03280 | 0.02892 | 1.22551 | 2.90611 | 0.60770 | 1.06054 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |
| issue118_large_print_quality_loss_input_boundary_candidate | 0.03280 | 0.02892 | 1.20436 | 2.90611 | 0.60770 | 0.95479 | 0.03301 | 0.03694 | 0.00933 | 0.08671 |

## Deltas

- Candidate versus issue `#116`: `Large Print Quality Loss = -0.10575`, `overall_quality_loss_mae_mean = -0.02115`.
- Candidate versus PR `#30`: `Large Print Quality Loss = -0.00003`, `overall_quality_loss_mae_mean = -0.01714`.
- Computer Monitor Quality Loss delta versus issue `#116`: `+0.00000`.
- Small Print Quality Loss delta versus issue `#116`: `+0.00000`.
- Reported-MTF equality versus issue `#116`: `True`.
- Non-target Quality Loss presets unchanged versus issue `#116`: `True`.

## Acceptance

- `selected_slice_matches_issue118`: `True`
- `large_print_quality_loss_improved_vs_issue116`: `True`
- `overall_quality_loss_improved_vs_issue116`: `True`
- `computer_monitor_quality_loss_preserved_vs_issue116`: `True`
- `small_print_quality_loss_preserved_vs_issue116`: `True`
- `curve_mae_non_worse_than_issue116`: `True`
- `focus_preset_acutance_non_worse_than_issue116`: `True`
- `reported_mtf_equal_to_issue116`: `True`
- `only_large_print_quality_loss_input_added`: `True`
- `quality_loss_coefficients_preserved`: `True`
- `all_issue118_gates_pass`: `True`

## Conclusion

- Status: `issue118_current_best_candidate`
- Summary: The Large Print-only Quality Loss input boundary closes the residual overall Quality Loss delta while preserving issue-116's Computer Monitor and Small Print improvements plus reported-MTF parity.
- Next step: Promote the candidate for review against the current PR #30 branch.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/config`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
