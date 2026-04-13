# Intrinsic Phase-Retained Downstream Matched-Ori-Only Follow-up

Issue `#93` implements the bounded slice selected in issue `#91` / PR `#92`: keep the issue-85 topology and preserve only the isolated downstream matched-ori Quality Loss subfamily from issue `#89`.

## Scope

- New intrinsic scope: `readout_reconnect_quality_loss_isolation_downstream_matched_ori_only`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json`
- Reference issue-89 profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_matched_ori_graft_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_downstream_matched_ori_only_profile.json`
- Difference from issue `#89`: the isolated downstream Quality Loss branch still receives matched-ori correction / acutance-anchor, but the reported-MTF/readout path and the main acutance branch stay on the issue-85 topology.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#85` baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 8.02054`
- `mtf_abs_signed_rel_mean = 0.13994`

Issue `#89` full graft reference:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf_abs_signed_rel_mean = 0.74771`

Issue `#93` downstream-only candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 3.94743`
- `mtf_abs_signed_rel_mean = 0.13994`

## Comparison

- Versus issue `#85`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#85`, `overall_quality_loss_mae_mean` changes by `-4.07311`.
- Versus issue `#85`, `mtf20` changes by `+0.00000` and `mtf_abs_signed_rel_mean` changes by `+0.00000`.
- Versus issue `#89`, `overall_quality_loss_mae_mean` changes by `+0.00000` and `mtf_abs_signed_rel_mean` changes by `-0.60778`.

## Acceptance

- `curve_mae_mean` no worse than issue `#85`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#85`: `True`
- `overall_quality_loss_mae_mean` improves versus issue `#85`: `True`
- `mtf20` no worse than issue `#85`: `True`
- `mtf_abs_signed_rel_mean` no worse than issue `#85`: `True`
- All issue-93 gates pass: `True`

## Conclusion

- Status: `issue93_acceptance_passed_but_not_current_best`
- Summary: The downstream-only matched-ori slice preserves the issue-85 readout and main-acutance gains while improving overall Quality Loss, but it still trails the current PR #30 branch overall.
- Next step: Keep this branch as the bounded issue-93 implementation record and judge any later promotion against the remaining PR #30 gap.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
