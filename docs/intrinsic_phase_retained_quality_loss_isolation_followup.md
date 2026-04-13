# Intrinsic Phase-Retained Quality-Loss Isolation Follow-up

Issue `#81` implements the bounded slice selected in issue `#79` / PR `#80`: keep the phase-retained intrinsic transfer, but isolate downstream Quality Loss from the intrinsic path.

## Scope

- New intrinsic scope: `quality_loss_isolation`
- Basis profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_profile.json`
- Candidate profile: `algo/deadleaf_13b10_imatest_intrinsic_full_reference_phase_retained_real_quality_loss_isolation_profile.json`
- Difference from `replace_all`: Quality Loss no longer consumes the intrinsic compensated MTF path.
- Difference from `acutance_only`: this issue names the narrower downstream-isolation intent explicitly on top of the stronger phase-retained intrinsic branch.

## Result

Current PR `#30` branch:

- `curve_mae_mean = 0.03679`
- `focus_preset_acutance_mae_mean = 0.04249`
- `overall_quality_loss_mae_mean = 1.22150`

PR `#34` intrinsic baseline:

- `curve_mae_mean = 0.03587`
- `focus_preset_acutance_mae_mean = 0.03165`
- `overall_quality_loss_mae_mean = 4.56801`

PR `#47` phase-retained intrinsic baseline:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 14.47576`

Issue `#81` quality-loss-isolated candidate:

- `curve_mae_mean = 0.03280`
- `focus_preset_acutance_mae_mean = 0.02892`
- `overall_quality_loss_mae_mean = 8.02054`

## Comparison

- Versus PR `#47`, `overall_quality_loss_mae_mean` changes by `-6.45522`.
- Versus PR `#34`, `curve_mae_mean` changes by `-0.00307` and `focus_preset_acutance_mae_mean` changes by `-0.00273`.
- Versus current PR `#30`, `curve_mae_mean` changes by `-0.00399` and `overall_quality_loss_mae_mean` changes by `+6.79904`.

## Acceptance

- `curve_mae_mean` no worse than issue `#34`: `True`
- `focus_preset_acutance_mae_mean` no worse than issue `#34`: `True`
- `overall_quality_loss_mae_mean` improved versus issue `#47`: `True`
- All issue-81 gates pass: `True`

## Conclusion

- Status: `issue81_acceptance_passed_but_not_current_best`
- Summary: The new scope is a real improvement over the old phase-retained replace_all path: it preserves the intrinsic curve / focus-preset Acutance gains while materially reducing overall Quality Loss. It still remains worse than the current PR #30 main line on overall Quality Loss and MTF-threshold readouts.
- Next step: Keep this scope as the new bounded intrinsic record and evaluate whether a later follow-up can reduce the remaining gap to the current best branch without reopening unrelated families.

## Storage Separation

- Golden/reference roots: `20260318_deadleaf_13b10`, `release/deadleaf_13b10_release/data/20260318_deadleaf_13b10`
- Fitted outputs for this issue stay under `algo/` and `artifacts/` only.
- No release-facing config is promoted in this issue.
