# Issue 124 Curve-Only High-Mixup/Ori Summary

- Result: `positive_partial_not_promotable`.
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json`
- Scoped boundary: only the main Acutance curve is anchored for mixups `0.8` and `ori`; preset Acutance, Quality Loss, and reported-MTF/readout paths stay unchanged.

## Metrics

| Metric | PR #119 | Issue #124 | Delta | Gate |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.03280 | 0.02425 | -0.00855 | <= 0.020 (miss) |
| focus_preset_acutance_mae_mean | 0.02892 | 0.02892 | 0.00000 | <= 0.030 (pass) |
| overall_quality_loss_mae_mean | 1.20436 | 1.20436 | 0.00000 | <= 1.30 (pass) |
| mtf_abs_signed_rel_mean | 0.08671 | 0.08671 | 0.00000 | preserve |
| Small Print Acutance | 0.03173 | 0.03173 | 0.00000 | <= 0.030 (miss) |

## Curve Tail

| Mixup | Before | After | Delta |
| --- | ---: | ---: | ---: |
| 0.15 | 0.02938 | 0.02938 | 0.00000 |
| 0.25 | 0.02480 | 0.02480 | 0.00000 |
| 0.4 | 0.01936 | 0.01936 | 0.00000 |
| 0.65 | 0.01195 | 0.01195 | 0.00000 |
| 0.8 | 0.04482 | 0.01884 | -0.02598 |
| ori | 0.07934 | 0.04580 | -0.03353 |

The selected high-mixup/ori intervention reduces `0.8` and `ori` curve error, but the remaining README curve miss is now spread across `ori`, `0.15`, and `0.25` rather than being solved by this slice alone.

## Acceptance

- Curve MAE reduced versus PR #119: `True`.
- Reported-MTF preserved: `True`.
- Overall Quality Loss preserved: `True`.
- Small Print Acutance preserved: `True`.
- All README gates pass: `False`.

## Next Result

The high-mixup/ori curve-only anchor is a positive partial result: it materially lowers curve MAE while preserving reported-MTF, preset Acutance, and Quality Loss, but the README curve gate still misses.

Do not broaden this issue into Small Print preset work. If PM splits another engineering pass, target the remaining curve residual now visible in `ori`, `0.15`, and `0.25`, while preserving the issue #124 curve-only isolation.

## Release Separation

This remains canonical-target research, not a release-facing config promotion. No fitted outputs are written under golden/reference data roots or release configs.
