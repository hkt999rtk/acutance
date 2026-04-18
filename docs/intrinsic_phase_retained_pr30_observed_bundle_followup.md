# Intrinsic Phase-Retained PR30 Observed-Branch Bundle Follow-up

Issue `#108` implements the bounded slice selected by issue `#105` / PR `#107`: keep the issue-102 intrinsic topology, but graft the PR `#30` observed-branch bundle onto the reported-MTF/readout path and downstream Quality Loss branch only.

## Scope

- New intrinsic scope: `reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only`
- Basis issue `#102` profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_pr30_observed_bundle_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- The main acutance branch stays on the issue-102 intrinsic branch; release-facing PR30 configs are not promoted.

Selected PR30 observed-branch bundle:

- `calibration_file = algo/deadleaf_13b10_psd_calibration_anchored.json`
- `mtf_compensation_mode = sensor_aperture_sinc`
- `sensor_fill_factor = 1.5`
- `texture_support_scale = True`
- `high_frequency_guard_start_cpp = 0.36`

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf20 = 0.03301`
- `mtf30 = 0.03694`
- `mtf50 = 0.00933`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#102` baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.02972`
- `mtf30 = 0.04293`
- `mtf50 = 0.03094`
- `mtf_abs_signed_rel_mean = 0.23033`

Issue `#108` PR30 observed-branch bundle candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 1.40663`
- `mtf20 = 0.03301`
- `mtf30 = 0.03694`
- `mtf50 = 0.00933`
- `mtf_abs_signed_rel_mean = 0.08671`

## Comparison

- Versus issue `#102`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#102`, `overall_quality_loss_mae_mean` changes by `-2.54080`.
- Versus issue `#102`, `mtf20` changes by `+0.00329`, `mtf30` by `-0.00599`, `mtf50` by `-0.02161`, and `mtf_abs_signed_rel_mean` by `-0.14361`.
- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `+0.18513` and `mtf_abs_signed_rel_mean` changes by `+0.00000`.

## Acceptance

- `curve_mae_mean` no worse than issue `#102`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#102`: `True`
- `overall_quality_loss_mae_mean` materially improves versus issue `#102`: `True`
- `mtf_abs_signed_rel_mean` improves versus issue `#102`: `True`
- `mtf20` does not materially regress versus issue `#102`: `True`
- `mtf30` improves versus issue `#102`: `True`
- `mtf50` improves versus issue `#102`: `True`
- All issue-108 gates pass: `True`

## Conclusion

- Status: `issue108_acceptance_passed_but_not_current_best`
- Summary: The PR30 observed-branch bundle clears the issue-108 gates against issue #102, but at least one guarded output still trails the current PR #30 branch.
- Next step: Keep this as the bounded issue-108 implementation record and split any remaining gap from the measured candidate-vs-PR30 deltas.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/config`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
