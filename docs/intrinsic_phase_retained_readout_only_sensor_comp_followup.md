# Intrinsic Phase-Retained Readout-Only Sensor Compensation Follow-up

Issue `#102` implements the bounded slice selected in issue `#99` / PR `#100` / PR `#101`: keep the issue-97 topology and downstream-only matched-ori Quality Loss branch, but add readout-only `sensor_aperture_sinc` compensation on the reported-MTF threshold-extraction path.

## Scope

- New intrinsic scope: `reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_reported_mtf_disconnect_readout_only_sensor_comp_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Difference from issue `#97`: the main acutance branch and downstream Quality Loss branch stay unchanged, but reported-MTF threshold extraction adds readout-only `sensor_aperture_sinc` compensation with `sensor_fill_factor = 1.5`.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf20 = 0.03301`
- `mtf30 = 0.03694`
- `mtf50 = 0.00933`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#93` baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.08577`
- `mtf30 = 0.01789`
- `mtf50 = 0.00720`
- `mtf_abs_signed_rel_mean = 0.13994`

Issue `#97` baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.07448`
- `mtf30 = 0.07553`
- `mtf50 = 0.03429`
- `mtf_abs_signed_rel_mean = 0.37688`

Issue `#102` readout-only sensor compensation candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf20 = 0.02972`
- `mtf30 = 0.04293`
- `mtf50 = 0.03094`
- `mtf_abs_signed_rel_mean = 0.23033`

## Comparison

- Versus issue `#97`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#97`, `overall_quality_loss_mae_mean` changes by `+0.00000`.
- Versus issue `#97`, `mtf20` changes by `-0.04476`, `mtf30` by `-0.03260`, `mtf50` by `-0.00335`, and `mtf_abs_signed_rel_mean` by `-0.14655`.
- Versus PR `#30`, `overall_quality_loss_mae_mean` changes by `+2.72593` and `mtf_abs_signed_rel_mean` changes by `+0.14361`.

## Acceptance

- `curve_mae_mean` no worse than issue `#97`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#97`: `True`
- `overall_quality_loss_mae_mean` no worse than issue `#97`: `True`
- `mtf_abs_signed_rel_mean` improves versus issue `#97`: `True`
- `mtf20` no worse than issue `#97`: `True`
- `mtf30` improves versus issue `#97`: `True`
- `mtf50` improves versus issue `#97`: `True`
- All issue-102 gates pass: `True`

## Conclusion

- Status: `issue102_acceptance_passed_but_not_current_best`
- Summary: Adding readout-only sensor-aperture compensation preserves the issue-97 curve, focus-preset Acutance, and downstream Quality Loss record while improving the reported-MTF readout, but it still trails the current PR #30 branch overall.
- Next step: Keep this branch as the bounded issue-102 implementation record and judge any later promotion against the remaining PR #30 gap.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
