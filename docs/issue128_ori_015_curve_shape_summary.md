# Issue 128 Ori/0.15 Curve-Shape Summary

- Result: `bounded_negative_not_promotable`.
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_ori_015_profile.json`
- Scoped boundary: add `0.15` to the existing issue #124 curve-only Acutance anchor mask; keep `0.25`, preset Acutance, Quality Loss, and reported-MTF/readout untouched.

## Metrics

| Metric | PR #125 | Issue #128 | Delta | Gate |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.02425 | 0.02547 | 0.00122 | <= 0.020 (miss) |
| focus_preset_acutance_mae_mean | 0.02892 | 0.02892 | 0.00000 | preserve |
| overall_quality_loss_mae_mean | 1.20436 | 1.20436 | 0.00000 | preserve |
| mtf_abs_signed_rel_mean | 0.08671 | 0.08671 | 0.00000 | preserve |
| Small Print Acutance | 0.03173 | 0.03173 | 0.00000 | <= 0.030 (miss) |

## Curve Shape Result

| Mixup | PR #125 | Issue #128 | Delta |
| --- | ---: | ---: | ---: |
| 0.15 | 0.02938 | 0.03546 | 0.00608 |
| 0.25 | 0.02480 | 0.02480 | 0.00000 |
| 0.4 | 0.01936 | 0.01936 | 0.00000 |
| 0.65 | 0.01195 | 0.01195 | 0.00000 |
| 0.8 | 0.01884 | 0.01884 | 0.00000 |
| ori | 0.04580 | 0.04580 | 0.00000 |

The `ori` and `0.8` curve values stay at their issue #124 values, but `0.15` worsens from `0.02938` to `0.03546`. The aggregate curve MAE therefore moves away from the README gate.

## Acceptance

- Curve gate pass: `False`.
- Curve improved versus PR #125: `False`.
- Reported-MTF preserved: `True`.
- Focus-preset Acutance preserved: `True`.
- Overall Quality Loss preserved: `True`.
- Small Print Acutance preserved: `True`.

## Next Result

The bounded ori/0.15 curve-shape candidate is not promotable: it preserves reported-MTF, preset Acutance, overall Quality Loss, and release separation, but worsens the aggregate curve MAE because the current matched-ori curve shape moves `0.15` in the wrong direction.

Do not continue broadening the issue #124 curve-only anchor mask. If PM splits another curve follow-up, it should require a per-mixup or shape-family variant that proves `0.15` improves before committing to a full benchmark; otherwise split the deferred Small Print Acutance preset-only miss.

## Release Separation

This remains canonical-target research, not a release-facing config promotion. No fitted outputs are written under golden/reference data roots or release configs.
