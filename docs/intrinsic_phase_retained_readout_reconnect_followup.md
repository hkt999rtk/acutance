# Intrinsic Phase-Retained Readout Reconnect Follow-up

Issue `#85` implements the bounded slice selected in issue `#83` / PR `#84`: reconnect the phase-retained intrinsic branch to the reported-MTF/readout path while keeping downstream Quality Loss isolated.

## Scope

- New intrinsic scope: `readout_reconnect_quality_loss_isolation`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_readout_reconnect_quality_loss_isolation_profile.json`
- Difference from `quality_loss_isolation`: reported-MTF/readout metrics now consume the intrinsic branch as well.
- Difference from `replace_all`: downstream Quality Loss remains on the non-intrinsic branch.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`
- `mtf_abs_signed_rel_mean = 0.08671`

Issue `#47` phase-retained intrinsic baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 14.47576`
- `mtf_abs_signed_rel_mean = 0.13994`

Issue `#81` quality-loss-isolated candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 8.02054`
- `mtf_abs_signed_rel_mean = 0.37917`

Issue `#85` readout-reconnected candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 8.02054`
- `mtf_abs_signed_rel_mean = 0.13994`

## Comparison

- Versus issue `#81`, `curve_mae_mean` changes by `+0.00000` and `focus_preset_acutance_mae_mean` changes by `+0.00000`.
- Versus issue `#81`, `overall_quality_loss_mae_mean` changes by `+0.00000`.
- Versus issue `#81`, `mtf_abs_signed_rel_mean` changes by `-0.23924`.
- Thresholds closer to PR `#30` than issue `#81`: `mtf20=False`, `mtf30=True`, `mtf50=True`.

## Acceptance

- `curve_mae_mean` no worse than issue `#81`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#81`: `True`
- `overall_quality_loss_mae_mean` no worse than issue `#81`: `True`
- `mtf_abs_signed_rel_mean` closer to PR `#30` than issue `#81`: `True`
- At least two threshold errors closer to PR `#30` than issue `#81`: `True`
- All issue-85 gates pass: `True`

## Conclusion

- Status: `issue85_acceptance_passed_but_not_current_best`
- Summary: The new scope reconnects the phase-retained intrinsic branch to the reported-MTF/readout path while keeping downstream Quality Loss isolated. It is intended to improve the post-issue81 readout gap without giving back the issue-81 curve / focus / Quality Loss gains.
- Next step: Keep this scope as the new bounded intrinsic implementation record and judge promotion against the current PR #30 branch from the resulting readout and Quality Loss tradeoff.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
