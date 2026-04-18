# Issue 126 Residual Curve Discovery

- Selected discovery: `issue124_residual_curve_ori_015_025_discovery`.
- Current best: issue `#124` / PR `#125`.
- Current profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_curve_only_high_mixup_ori_profile.json`
- Scope: post-issue124 curve residual only; do not broaden into Small Print Acutance preset work inside this slice.

## README Gate Status

| Gate | Value | Threshold | Delta | Status |
| --- | ---: | ---: | ---: | --- |
| curve_mae_mean | 0.02425 | 0.02000 | 0.00425 | miss |
| focus_preset_acutance_mae_mean | 0.02892 | 0.03000 | -0.00108 | pass |
| overall_quality_loss_mae_mean | 1.20436 | 1.30000 | -0.09564 | pass |
| non-phone Acutance max (Small Print Acutance) | 0.03173 | 0.03000 | 0.00173 | miss |

## Residual Curve Evidence

| Mixup | Curve MAE | Weighted contribution | Above-gate contribution | Positive excess share | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.15 | 0.02938 | 0.00588 | 0.00188 | 0.346 | miss |
| 0.25 | 0.02480 | 0.00496 | 0.00096 | 0.177 | miss |
| 0.4 | 0.01936 | 0.00387 | 0.00000 | 0.000 | pass |
| 0.65 | 0.01195 | 0.00120 | 0.00000 | 0.000 | pass |
| 0.8 | 0.01884 | 0.00377 | 0.00000 | 0.000 | pass |
| ori | 0.04580 | 0.00458 | 0.00258 | 0.476 | miss |

- Weighted curve MAE remains `0.02425`, delta `+0.00425` to the README curve gate.
- Positive above-gate pressure ranks as: `ori, 0.15, 0.25`.
- If `ori` alone were reduced to the gate, aggregate curve MAE would still be `0.02167`.
- If `ori + 0.25` were reduced to the gate, aggregate curve MAE would still be `0.02071`.
- If `ori + 0.15` were reduced to the gate, aggregate curve MAE would be `0.01980`.

## Selected Next Slice

- Slice ID: `issue124_residual_curve_ori_015_curve_only_shape_boundary`.
- Target mixups: `ori, 0.15`.
- Deferred residual mixups: `0.25`.
- Summary: Keep issue #124 curve-only isolation, but split the next implementation around residual curve-shape tuning for `ori` and `0.15`. Those two mixups are the smallest residual pair whose above-gate weighted excess can clear the README curve gate if each is reduced to the gate.

Minimum boundary:

- Start from the issue #124 / PR #125 candidate profile.
- Preserve `curve_only_acutance_anchor_mixups` isolation and do not touch preset Acutance.
- Add or tune only curve-side matched-ori Acutance correction shape for the selected residual mixups.
- Do not change reported-MTF compensation/readout settings or Quality Loss preset input overrides.
- Keep release-facing configs and golden/reference data untouched.

Validation plan:

- Regenerate Acutance/Quality Loss benchmark artifact for the candidate profile.
- Regenerate PSD/MTF benchmark artifact to prove reported-MTF remains unchanged.
- Compare README gates and PR #125 deltas in a checked-in summary.
- Require `curve_mae_mean <= 0.020` for promotion; otherwise record a bounded negative or split the residual `0.25` curve miss.
- Require focus-preset Acutance, overall Quality Loss, Small Print Acutance, and reported-MTF metrics to match PR #125 unless the result is explicitly non-promotable.

## Stop-Curve Option

Do not stop curve work yet: the residual curve miss is still larger than the deferred Small Print Acutance miss, and existing curve-only isolation has already produced a protected-branch-preserving improvement.

## Release Separation

This is canonical-target discovery only. It uses checked-in artifacts and does not promote fitted outputs into golden/reference roots or release configs.
