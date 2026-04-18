# Intrinsic After Issue 120 Next Slice

Issue `#122` is the developer-discovery pass selected by issue `#120` / PR `#121`.

## Current Best

- Profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_computer_monitor_small_print_large_print_pr30_input_profile.json`
- `curve_mae_mean = 0.03280`; README gate delta `+0.01280`.
- `focus_preset_acutance_mae_mean = 0.02892`; gate status `True`.
- `overall_quality_loss_mae_mean = 1.20436`; gate status `True`.
- `Small Print Acutance = 0.03173`; non-Phone gate delta `+0.00173`.

## Curve Residual Evidence

- Weighted curve MAE recomputed from mixup records: `0.03280`.
- High-mixup keys `0.8, ori` are `0.300` of curve records but `0.515` of weighted curve error.
- Current `0.8` curve MAE: `0.04482`; delta versus the comparison profile `+0.00493`.
- Current `ori` curve MAE: `0.07934`; delta versus the comparison profile `+0.03492`.
- Lower/mid checks already under gate: `0.4 = True`, `0.65 = True`.

## Split Decision

- Recommendation: `split_remaining_misses`
- Reason: The curve miss is the dominant README miss and is concentrated in high-mixup/ori curve records, while the only non-Phone Acutance miss is a small Small Print preset excess. Existing issue #114/#116/#118 Quality Loss boundary changes leave all curve and Acutance-preset metrics invariant, so a single Quality Loss or broad readout slice is not supported by the current evidence.
- First slice: `issue118_curve_high_mixup_curve_only_boundary`
- Deferred slice: `issue118_small_print_acutance_preset_only_boundary`

## Selected Next Slice

- Slice id: `issue118_curve_high_mixup_curve_only_boundary`
- Summary: Isolate a curve-only boundary on the issue #118 profile that targets the high-mixup/ori curve tail while leaving preset Acutance, Quality Loss, and reported-MTF branches unchanged.

Repo evidence:

- Issue #120 records curve MAE as the largest remaining gate miss.
- `0.8` and `ori` are only 30% of curve records but contribute more than half of weighted curve MAE.
- The current issue #118 profile already keeps reported-MTF parity with PR #30.
- Prior curve-side mid-scale clip-hi work showed curve-only Acutance correction can move curve MAE while holding preset Acutance and Quality Loss fixed.

Minimum implementation boundary:

- Start from the issue #118 current-best profile.
- Touch only the curve-side Acutance/intrinsic-full-reference boundary used to produce `curve_mae_mean`.
- Do not alter `quality_loss_preset_input_profile_overrides`, Quality Loss coefficients, reported-MTF compensation/readout settings, or release-facing configs.

Expected preservation:

- `reported_mtf_parity`: `preserve`
- `overall_quality_loss_mae_mean`: `preserve`
- `focus_preset_acutance_mae_mean`: `preserve_or_non_worse`
- `small_print_acutance`: `preserve_or_measure_tradeoff`

Validation plan:

- Regenerate PSD/MTF and Acutance/Quality Loss benchmarks for the candidate.
- Compare README gates against PR #119 and PR #30.
- Require `mtf20`, `mtf30`, `mtf50`, and `mtf_abs_signed_rel_mean` to remain equal to PR #119 unless the tradeoff is explicitly accepted.
- Require `overall_quality_loss_mae_mean <= 1.20435969` or an explicit non-promotion result.

## Quality Loss Boundary Evidence

- Curve and Acutance metrics invariant across issue #108/#114/#116/#118 Quality Loss boundary records: `True`.
- Interpretation: The issue #114, #116, and #118 Quality Loss input-boundary changes do not move curve MAE, focus Acutance, reported-MTF, or any Acutance preset MAE. The remaining README misses therefore sit on the upstream Acutance/curve branch, not on the Quality Loss mapping branch.

## Storage Separation

- This issue is a canonical-target discovery record, not a release config promotion.
- Do not write fitted profiles, transfer tables, or generated outputs under golden/reference roots.
- Do not touch release-facing configs until a later implementation clears the README gates.
