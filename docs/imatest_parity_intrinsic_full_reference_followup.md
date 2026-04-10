# Imatest Parity Intrinsic Full-Reference Follow-up

Issue: `#33`  
Parent: `#29`  
Context: `#30`, `#32`

## What changed

- Added a bounded intrinsic / full-reference dead-leaves path that uses the paired `ori` capture as the reference image for the same scene.
- Added translation-only registration via phase correlation so the intrinsic slice can align the observed patch against the paired `ori` patch without reopening the broader crop-tuning family.
- Derived a radial transfer curve from the paired `ori` and observed patches, then used that transfer to anchor the predicted dead-leaves MTF against the paired `ori` reference MTF.
- Checked in:
  - `algo/deadleaf_13b10_imatest_intrinsic_full_reference_profile.json`
  - `artifacts/imatest_parity_intrinsic_full_reference_psd_benchmark.json`
  - `artifacts/imatest_parity_intrinsic_full_reference_benchmark.json`

## Why this family

Issue `#31` asked for the next source-backed model family after the registration / reference-anchor sweep in PR `#30` plateaued.

PR `#32` then tested a stronger matched-`ori` OECF proxy and left the top-line metrics unchanged, which ruled out spending more time on that family. The black-box research notes still identified intrinsic / full-reference dead-leaves behavior as a plausible missing family, so this issue implements one bounded slice of that path.

## Result

Current best PR `#30` branch:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

PR `#32` matched-`ori` OECF proxy result:

- `curve_mae_mean = 0.03683438`
- `acutance_focus_preset_mae_mean = 0.04249131`
- `overall_quality_loss_mae_mean = 1.22214341`

Intrinsic / full-reference prototype:

- `curve_mae_mean = 0.03587346`
- `acutance_focus_preset_mae_mean = 0.03165223`
- `overall_quality_loss_mae_mean = 4.56800916`

Relative to both PR `#30` and PR `#32`, this intrinsic slice:

- improves `curve_mae_mean`
- improves the focus-preset Acutance mean
- improves every non-Phone Acutance preset MAE
- slightly worsens the Phone preset
- regresses `overall_quality_loss_mae_mean` sharply

Preset-level Acutance comparison against the PR `#30` / PR `#32` control:

- `5.5" Phone Display Acutance`: `0.01380 -> 0.01955`
- `Computer Monitor Acutance`: `0.05269 -> 0.03460`
- `UHDTV Display Acutance`: `0.04794 -> 0.03626`
- `Small Print Acutance`: `0.04670 -> 0.03236`
- `Large Print Acutance`: `0.05132 -> 0.03549`

The PSD benchmark shows the same mixed shape:

- the intrinsic slice improves `curve_mae_mean` from `0.04306442` to `0.03587346`
- but `mtf_abs_signed_rel_mean` rises from `0.08692956` to `0.20631329`

## Conclusion

This is a bounded mixed result, not a new winning replacement for the current PR `#30` branch.

The intrinsic / full-reference family does appear to help the remaining curve and non-Phone Acutance gap, which means the family is more promising than the matched-`ori` OECF proxy tested in PR `#32`. But the current transfer-only formulation breaks the README-facing quality-loss objective badly enough that it should remain experiment-only for now.

The most likely next narrower follow-up, if issue `#29` needs another descendant, is not more local curve tuning. It is a source-backed check on why the intrinsic transfer improves curve / Acutance while destabilizing the quality-loss mapping, for example by isolating whether the remaining miss is the transfer formulation itself or the downstream quality-loss calibration under that new MTF shape.
